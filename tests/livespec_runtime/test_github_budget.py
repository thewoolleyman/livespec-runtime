"""Tests for GitHub request-budget measurement."""

import json
import subprocess
from pathlib import Path
from typing import Any

from returns.io import IOFailure
from returns.unsafe import unsafe_perform_io

__all__: list[str] = []


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
