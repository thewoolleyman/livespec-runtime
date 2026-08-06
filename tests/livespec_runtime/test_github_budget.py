"""Tests for GitHub request-budget measurement."""

import json
import subprocess
from pathlib import Path
from typing import Any, cast
from unittest.mock import Mock

from returns.io import IOFailure
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


class _Clock:
    def __init__(self, *, value: float = 0.0) -> None:
        self.value = value

    def now(self) -> float:
        return self.value

    def sleep(self, seconds: float, /) -> None:
        self.value += seconds


def _budgeted_client_type() -> type[Any]:
    from livespec_runtime import github_budget

    assert hasattr(github_budget, "GithubBudgetedClient")
    return cast(type[Any], github_budget.GithubBudgetedClient)


def test_github_budget_module_exists() -> None:
    assert Path("livespec_runtime/github_budget.py").is_file()


def test_rate_limit_headers_parse_to_snapshot() -> None:
    from livespec_runtime.github_budget import parse_rate_limit_snapshot

    snapshot = parse_rate_limit_snapshot(
        headers={
            "x-ratelimit-limit": "5000",
            "x-ratelimit-remaining": "4997",
            "x-ratelimit-used": "3",
            "x-ratelimit-reset": "1720000000",
            "x-ratelimit-resource": "core",
        }
    )

    assert snapshot.limit == 5000
    assert snapshot.remaining == 4997
    assert snapshot.used == 3
    assert snapshot.reset == 1720000000
    assert snapshot.resource == "core"


def test_classifies_every_github_failure_branch() -> None:
    from livespec_runtime.github_budget import (
        GithubRateLimitClassification,
        GithubRateLimitSnapshot,
        classify_github_failure,
    )

    primary = GithubRateLimitSnapshot(
        limit=5000,
        remaining=0,
        used=5000,
        reset=1720000000,
        resource="core",
    )
    secondary = GithubRateLimitSnapshot(
        limit=5000,
        remaining=12,
        used=42,
        reset=1720000000,
        resource="search",
    )

    assert (
        classify_github_failure(status_code=403, snapshot=primary)
        is GithubRateLimitClassification.PRIMARY_EXHAUSTION
    )
    assert (
        classify_github_failure(status_code=403, snapshot=secondary)
        is GithubRateLimitClassification.SECONDARY_LIMIT
    )
    assert (
        classify_github_failure(status_code=401, snapshot=secondary)
        is GithubRateLimitClassification.AUTH_FAILURE
    )
    assert (
        classify_github_failure(status_code=500, snapshot=secondary)
        is GithubRateLimitClassification.OTHER
    )


def test_appends_snapshot_to_durable_jsonl_signal(tmp_path: Path) -> None:
    from livespec_runtime.github_budget import GithubRateLimitSnapshot, append_rate_limit_snapshot

    signal_path = tmp_path / "github-budget.jsonl"
    snapshot = GithubRateLimitSnapshot(
        limit=5000,
        remaining=4999,
        used=1,
        reset=1720000000,
        resource="core",
    )

    outcome = append_rate_limit_snapshot(
        snapshot=snapshot,
        argv="gh api repos/example/project",
        status_code=200,
        classification=None,
        path=signal_path,
    )

    assert not isinstance(outcome, IOFailure)
    records = [json.loads(line) for line in signal_path.read_text().splitlines()]
    assert records == [
        {
            "argv": "gh api repos/example/project",
            "classification": None,
            "limit": 5000,
            "remaining": 4999,
            "reset": 1720000000,
            "resource": "core",
            "status_code": 200,
            "used": 1,
        }
    ]


def test_rate_limited_403_returns_unmeasurable_failure_not_empty_success(
    monkeypatch: Any,
    tmp_path: Path,
) -> None:
    from livespec_runtime.cross_repo.providers.github import branch_exists_on_remote
    from livespec_runtime.github_budget import GithubBudgetUnmeasurable

    def fake_run(_argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        error = subprocess.CalledProcessError(returncode=1, cmd=["gh"])
        error.stderr = "\n".join(
            [
                "x-ratelimit-limit: 5000",
                "x-ratelimit-remaining: 0",
                "x-ratelimit-used: 5000",
                "x-ratelimit-reset: 1720000000",
                "x-ratelimit-resource: core",
                "gh: API rate limit exceeded (HTTP 403)",
            ]
        )
        raise error

    monkeypatch.setenv("LIVESPEC_GITHUB_BUDGET_LOG", str(tmp_path / "budget.jsonl"))
    monkeypatch.setattr(subprocess, "run", fake_run)

    outcome = branch_exists_on_remote(
        github_url="https://github.com/thewoolleyman/livespec",
        name="feat/foo",
    )

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert isinstance(failure, GithubBudgetUnmeasurable)
    assert failure.outcome == "UNMEASURABLE"
    assert bool(failure)
    assert failure != []


def test_repeated_read_of_unchanged_data_spends_no_primary_budget() -> None:
    client_type = _budgeted_client_type()
    from livespec_runtime.github_budget import GithubBudgetRequest, GithubBudgetResponse

    requests: list[GithubBudgetRequest] = []

    def fake_transport(*, request: GithubBudgetRequest) -> GithubBudgetResponse:
        requests.append(request)
        if len(requests) == 1:
            return GithubBudgetResponse(
                status_code=200,
                headers={
                    "etag": '"abc"',
                    "x-poll-interval": "3",
                    "x-ratelimit-limit": "5000",
                    "x-ratelimit-remaining": "4999",
                    "x-ratelimit-used": "1",
                    "x-ratelimit-reset": "1720000000",
                    "x-ratelimit-resource": "core",
                },
                value={"state": "open"},
                primary_budget_spent=1,
            )
        assert request.headers["If-None-Match"] == '"abc"'
        return GithubBudgetResponse(
            status_code=304,
            headers={
                "x-ratelimit-limit": "5000",
                "x-ratelimit-remaining": "4999",
                "x-ratelimit-used": "1",
                "x-ratelimit-reset": "1720000000",
                "x-ratelimit-resource": "core",
            },
            value=None,
            primary_budget_spent=1,
        )

    clock = _Clock()
    client = client_type(transport=fake_transport, now=clock.now, sleep=clock.sleep)

    first = client.request(method="GET", resource="/repos/example/project")
    second = client.request(method="GET", resource="/repos/example/project")
    clock.value = 4.0
    third = client.request(method="GET", resource="/repos/example/project")

    assert first.unwrap().value == {"state": "open"}
    assert second.unwrap().value == {"state": "open"}
    assert second.unwrap().primary_budget_spent == 0
    assert third.unwrap().value == {"state": "open"}
    assert third.unwrap().primary_budget_spent == 0
    assert len(requests) == 2


def test_mutation_sequence_is_paced_below_secondary_per_minute_ceiling() -> None:
    client_type = _budgeted_client_type()
    from livespec_runtime.github_budget import GithubBudgetRequest, GithubBudgetResponse

    clock = _Clock()
    mutation_times: list[float] = []

    def fake_transport(*, request: GithubBudgetRequest) -> GithubBudgetResponse:
        assert request.method == "DELETE"
        mutation_times.append(clock.value)
        assert sum(1 for issued_at in mutation_times if clock.value - issued_at < 60.0) <= 180
        return GithubBudgetResponse(
            status_code=204,
            headers={
                "x-ratelimit-limit": "5000",
                "x-ratelimit-remaining": "4999",
                "x-ratelimit-used": "1",
                "x-ratelimit-reset": "1720000000",
                "x-ratelimit-resource": "core",
            },
            value=None,
            primary_budget_spent=1,
        )

    client = client_type(transport=fake_transport, now=clock.now, sleep=clock.sleep)

    for index in range(181):
        result = client.request(method="DELETE", resource=f"/repos/example/project/{index}")
        assert result.unwrap().status_code == 204

    assert mutation_times[-1] >= 180.0


def test_deferrable_bulk_work_is_refused_below_reserved_floor() -> None:
    from returns.io import IOFailure

    client_type = _budgeted_client_type()
    from livespec_runtime.github_budget import GithubBudgetDeferred

    transport = Mock()
    client = client_type(transport=transport)
    outcome = client.request(
        method="DELETE",
        resource="/repos/example/project/obsolete",
        deferrable=True,
        remaining_floor=10,
        snapshot_headers={
            "x-ratelimit-limit": "5000",
            "x-ratelimit-remaining": "8",
            "x-ratelimit-used": "4992",
            "x-ratelimit-reset": "1720000000",
            "x-ratelimit-resource": "core",
        },
    )

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert isinstance(failure, GithubBudgetDeferred)
    assert failure.remaining == 8
    assert failure.floor == 10
    assert transport.mock_calls == []


def test_deferrable_bulk_floor_preflights_rate_limit_without_primary_spend() -> None:
    from returns.io import IOFailure

    client_type = _budgeted_client_type()
    from livespec_runtime.github_budget import (
        GithubBudgetDeferred,
        GithubBudgetRequest,
        GithubBudgetResponse,
    )

    requests: list[GithubBudgetRequest] = []

    def fake_transport(*, request: GithubBudgetRequest) -> GithubBudgetResponse:
        requests.append(request)
        assert request.resource == "/rate_limit"
        return GithubBudgetResponse(
            status_code=200,
            headers={
                "x-ratelimit-limit": "5000",
                "x-ratelimit-remaining": "8",
                "x-ratelimit-used": "4992",
                "x-ratelimit-reset": "1720000000",
                "x-ratelimit-resource": "core",
            },
            value={"resources": {}},
            primary_budget_spent=0,
        )

    client = client_type(transport=fake_transport)
    outcome = client.request(
        method="DELETE",
        resource="/repos/example/project/obsolete",
        deferrable=True,
        remaining_floor=10,
    )

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert isinstance(failure, GithubBudgetDeferred)
    assert failure.remaining == 8
    assert len(requests) == 1


def test_retry_after_backoff_is_honored_before_retry() -> None:
    client_type = _budgeted_client_type()
    from livespec_runtime.github_budget import GithubBudgetRequest, GithubBudgetResponse

    clock = _Clock(value=10.0)
    requests: list[GithubBudgetRequest] = []

    def fake_transport(*, request: GithubBudgetRequest) -> GithubBudgetResponse:
        requests.append(request)
        if len(requests) == 1:
            return GithubBudgetResponse(
                status_code=403,
                headers={
                    "retry-after": "7",
                    "x-ratelimit-limit": "5000",
                    "x-ratelimit-remaining": "9",
                    "x-ratelimit-used": "4991",
                    "x-ratelimit-reset": "1720000000",
                    "x-ratelimit-resource": "core",
                },
                value=None,
                primary_budget_spent=1,
            )
        return GithubBudgetResponse(
            status_code=200,
            headers={
                "x-ratelimit-limit": "5000",
                "x-ratelimit-remaining": "8",
                "x-ratelimit-used": "4992",
                "x-ratelimit-reset": "1720000000",
                "x-ratelimit-resource": "core",
            },
            value={"ok": True},
            primary_budget_spent=1,
        )

    client = client_type(transport=fake_transport, now=clock.now, sleep=clock.sleep)
    outcome = client.request(method="GET", resource="/repos/example/project")

    assert outcome.unwrap().value == {"ok": True}
    assert clock.value == 17.0
    assert len(requests) == 2


def test_primary_exhaustion_waits_until_reset_before_retry() -> None:
    client_type = _budgeted_client_type()
    from livespec_runtime.github_budget import GithubBudgetRequest, GithubBudgetResponse

    clock = _Clock(value=10.0)
    requests: list[GithubBudgetRequest] = []

    def fake_transport(*, request: GithubBudgetRequest) -> GithubBudgetResponse:
        requests.append(request)
        if len(requests) == 1:
            return GithubBudgetResponse(
                status_code=403,
                headers={
                    "x-ratelimit-limit": "5000",
                    "x-ratelimit-remaining": "0",
                    "x-ratelimit-used": "5000",
                    "x-ratelimit-reset": "13",
                    "x-ratelimit-resource": "core",
                },
                value=None,
                primary_budget_spent=1,
            )
        return GithubBudgetResponse(
            status_code=200,
            headers={
                "x-ratelimit-limit": "5000",
                "x-ratelimit-remaining": "4999",
                "x-ratelimit-used": "1",
                "x-ratelimit-reset": "1720000000",
                "x-ratelimit-resource": "core",
            },
            value={"ok": True},
            primary_budget_spent=1,
        )

    client = client_type(transport=fake_transport, now=clock.now, sleep=clock.sleep)
    outcome = client.request(method="GET", resource="/repos/example/project")

    assert outcome.unwrap().value == {"ok": True}
    assert clock.value == 13.0


def test_repeated_secondary_backoff_grows_exponentially_then_fails() -> None:
    from returns.io import IOFailure

    client_type = _budgeted_client_type()
    from livespec_runtime.github_budget import (
        GithubBudgetRequest,
        GithubBudgetResponse,
        GithubBudgetUnmeasurable,
    )

    clock = _Clock()

    def fake_transport(*, request: GithubBudgetRequest) -> GithubBudgetResponse:
        assert request.method == "GET"
        return GithubBudgetResponse(
            status_code=403,
            headers={
                "x-ratelimit-limit": "5000",
                "x-ratelimit-remaining": "1",
                "x-ratelimit-used": "4999",
                "x-ratelimit-reset": "1720000000",
                "x-ratelimit-resource": "core",
            },
            value=None,
            primary_budget_spent=1,
        )

    client = client_type(transport=fake_transport, now=clock.now, sleep=clock.sleep, max_attempts=3)
    outcome = client.request(method="GET", resource="/repos/example/project")

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert isinstance(failure, GithubBudgetUnmeasurable)
    assert failure.classification == "secondary_limit"
    assert clock.value == 180.0
