"""Every first-party GitHub read goes through `GithubBudgetedClient`.

`GithubBudgetedClient` shipped with the cache, the pacing, the backoff
and the floor already implemented and with ZERO production callers: this
library's own GitHub reads each built a `gh` argv and spawned it. A
budget policy nothing routes through is not a policy, so these tests
assert the ROUTING at the process boundary rather than asserting that a
call was made — a mock would pass on a client that did nothing.

What each half is worth is asserted separately, because the two reads
have different shapes:

- The branch-existence and compare reads POLL usually-unchanged state,
  so they take the client's CONDITIONAL path — the second read carries
  `If-None-Match` and a `304` answer is served from cache for no primary
  budget.
- The hygiene scan's PR listing is BULK advisory work, so it is declared
  DEFERRABLE against a reserved floor and is refused outright when the
  remaining budget sits below it.

New symbols are reached through `importlib` inside each test body rather
than imported at module top, so the Red commit fails on a real assertion
about behavior instead of dying at collection on a missing name.
"""

import importlib
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

import pytest
from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.cross_repo.providers.github import (
    GithubQueryFailed,
    branch_exists_on_remote,
    branch_merged_into_default,
    query_pull_request_state,
)
from livespec_runtime.hygiene_scan_findings import GH_PR_FIELDS, stale_pr_findings
from livespec_runtime.hygiene_scan_types import CommandResult, CommandUnavailable, ScanContext

__all__: list[str] = []

_REPO_URL = "https://github.com/thewoolleyman/livespec"
_REPO = Path("/repo")
_ORIGIN_URL = ("git", "-C", "/repo", "config", "--get", "remote.origin.url")
_RATE_LIMIT = ("gh", "api", "--include", "rate_limit")
_PR_LIST = ("gh", "pr", "list", "--state", "open", "--json", GH_PR_FIELDS)


def _measurement() -> Any:
    return importlib.import_module("livespec_runtime.github_budget_measurement")


def _budget() -> Any:
    return importlib.import_module("livespec_runtime.github_budget")


def _process() -> Any:
    return importlib.import_module("livespec_runtime.cross_repo.providers.github_process")


def _context_module() -> Any:
    return importlib.import_module("livespec_runtime.hygiene_scan_context")


def _rate_limit_lines(*, remaining: int, prefix: str = "< ") -> list[str]:
    return [
        f"{prefix}x-ratelimit-limit: 5000",
        f"{prefix}x-ratelimit-remaining: {remaining}",
        f"{prefix}x-ratelimit-used: {5000 - remaining}",
        f"{prefix}x-ratelimit-reset: 1720000000",
        f"{prefix}x-ratelimit-resource: core",
    ]


def _completed(*, argv: list[str], stdout: str, stderr: str) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=argv, returncode=0, stdout=stdout, stderr=stderr)


def _failed(*, stderr: str) -> subprocess.CalledProcessError:
    error = subprocess.CalledProcessError(returncode=1, cmd=["gh"])
    error.stderr = stderr
    return error


@pytest.fixture(autouse=True)
def _budget_signal(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    """Keep the durable budget signal these tests append inside `tmp_path`."""
    monkeypatch.setenv("LIVESPEC_GITHUB_BUDGET_LOG", str(tmp_path / "budget.jsonl"))


def test_a_repeated_branch_probe_is_revalidated_instead_of_refetched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The poll-shaped branch read takes the client's CONDITIONAL path.

    The second probe of the same branch MUST carry the `ETag` the first
    one was answered with, and a `304` MUST be served from the client's
    cache — that is the whole point of routing this read through the
    budgeted client rather than spawning `gh` directly.
    """
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(list(argv))
        if len(calls) == 1:
            return _completed(
                argv=argv,
                stdout='{"name": "conditional-probe"}',
                stderr="\n".join([*_rate_limit_lines(remaining=4999), '< ETag: "probe-etag"']),
            )
        raise _failed(stderr="\n".join([*_rate_limit_lines(remaining=4999), "gh: (HTTP 304)"]))

    monkeypatch.setattr(subprocess, "run", fake_run)

    first = branch_exists_on_remote(github_url=_REPO_URL, name="conditional-probe")
    second = branch_exists_on_remote(github_url=_REPO_URL, name="conditional-probe")

    assert unsafe_perform_io(first.unwrap()) is True
    assert unsafe_perform_io(second.unwrap()) is True
    assert calls[0] == ["gh", "api", "repos/thewoolleyman/livespec/branches/conditional-probe"]
    assert calls[1] == [
        "gh",
        "api",
        "repos/thewoolleyman/livespec/branches/conditional-probe",
        "-H",
        'If-None-Match: "probe-etag"',
    ]


def test_a_repeated_compare_read_is_revalidated_instead_of_refetched(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The compare read is the second poll-shaped read and takes the same path."""
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(list(argv))
        if len(calls) == 1:
            return _completed(
                argv=argv,
                stdout='{"status": "identical"}',
                stderr="\n".join([*_rate_limit_lines(remaining=4998), '< ETag: "compare-etag"']),
            )
        raise _failed(stderr="\n".join([*_rate_limit_lines(remaining=4998), "gh: (HTTP 304)"]))

    monkeypatch.setattr(subprocess, "run", fake_run)

    merged = branch_merged_into_default(
        github_url=_REPO_URL, name="conditional-compare", default_branch="master"
    )
    again = branch_merged_into_default(
        github_url=_REPO_URL, name="conditional-compare", default_branch="master"
    )

    assert unsafe_perform_io(merged.unwrap()) is True
    assert unsafe_perform_io(again.unwrap()) is True
    assert calls[1][-2:] == ["-H", 'If-None-Match: "compare-etag"']


def test_a_subcommand_that_cannot_carry_a_conditional_header_is_never_given_one(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`gh pr view` takes no `-H`, so its `ETag` is withheld rather than dropped.

    Caching a read the transport could not later revalidate would make
    the second call look conditional while sending an unconditional
    request — a saving that never happens, hidden behind a header the
    argv silently discarded.
    """
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(list(argv))
        return _completed(
            argv=argv,
            stdout='{"state": "OPEN"}',
            stderr="\n".join([*_rate_limit_lines(remaining=4997), '< ETag: "pr-etag"']),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    assert unsafe_perform_io(query_pull_request_state(github_url=_REPO_URL, number=77).unwrap())
    assert unsafe_perform_io(query_pull_request_state(github_url=_REPO_URL, number=77).unwrap())
    assert calls[0] == calls[1]
    assert "-H" not in calls[1]


def test_an_unmeasured_403_stays_an_ordinary_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """`UNMEASURABLE` names a budget class, and a class needs a measurement.

    A 403 whose response carried no `x-ratelimit-*` headers reported no
    budget at all. Treating it as exhaustion would make the client sleep
    to a reset time nobody sent, so it comes back as the transport
    failure it is — in ONE attempt.
    """
    calls: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append(list(argv))
        raise _failed(stderr="gh: forbidden (HTTP 403)")

    monkeypatch.setattr(subprocess, "run", fake_run)

    outcome = branch_exists_on_remote(github_url=_REPO_URL, name="unmeasured-403")

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert isinstance(failure, GithubQueryFailed)
    assert failure.argv.startswith("gh api repos/thewoolleyman/livespec/branches/")
    assert len(calls) == 1


def test_the_rate_limited_failure_still_names_a_command_an_operator_can_rerun(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The client names a method and a resource; the provider restates the argv."""

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        _ = argv
        raise _failed(
            stderr="\n".join(
                [*_rate_limit_lines(remaining=0), "gh: API rate limit exceeded (HTTP 403)"]
            )
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    outcome = branch_exists_on_remote(github_url=_REPO_URL, name="rate-limited")

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert isinstance(failure, _budget().GithubBudgetUnmeasurable)
    assert failure.argv == "gh api repos/thewoolleyman/livespec/branches/rate-limited"


class _Runner:
    """Answers a fixed argv table and records what it was asked to run."""

    def __init__(self, *, responses: dict[tuple[str, ...], CommandResult]) -> None:
        self.calls: list[tuple[str, ...]] = []
        self._responses = responses

    def run(self, *, argv: list[str], cwd: Path) -> IOResult[CommandResult, CommandUnavailable]:
        _ = cwd
        self.calls.append(tuple(argv))
        return IOSuccess(
            self._responses.get(tuple(argv), CommandResult(returncode=1, stderr="unexpected"))
        )


def _scan_context(*, runner: _Runner) -> ScanContext:
    return ScanContext(
        repo_path=_REPO,
        repo_name="repo",
        primary_path=_REPO,
        current_path=_REPO,
        base_ref="origin/master",
        default_branch="master",
        now=datetime(2026, 9, 6, tzinfo=timezone.utc),
        stale_after=timedelta(days=30),
        runner=runner.run,
    )


def _stale_pr_listing() -> str:
    return (
        '[{"number": 5, "headRefName": "feat/x", "updatedAt": "2026-01-01T00:00:00Z",'
        ' "title": "old", "url": "https://example.com/5"}]'
    )


def test_the_bulk_pr_listing_is_refused_below_the_reserved_floor() -> None:
    """Deferrable bulk work does not spend the budget interactive work needs."""
    floor = _context_module().GH_READ_BUDGET_FLOOR
    runner = _Runner(
        responses={
            _RATE_LIMIT: CommandResult(
                stdout="\n".join(_rate_limit_lines(remaining=floor - 1, prefix=""))
            ),
            _PR_LIST: CommandResult(stdout=_stale_pr_listing()),
        }
    )

    outcome = stale_pr_findings(context=_scan_context(runner=runner))

    assert unsafe_perform_io(outcome.unwrap()) == []
    assert _RATE_LIMIT in runner.calls
    assert _PR_LIST not in runner.calls


def test_the_bulk_pr_listing_proceeds_above_the_reserved_floor() -> None:
    """The floor holds work back; it does not cancel it."""
    floor = _context_module().GH_READ_BUDGET_FLOOR
    runner = _Runner(
        responses={
            _RATE_LIMIT: CommandResult(
                stdout="\n".join(_rate_limit_lines(remaining=floor + 1, prefix=""))
            ),
            _PR_LIST: CommandResult(stdout=_stale_pr_listing()),
        }
    )

    outcome = stale_pr_findings(context=_scan_context(runner=runner))

    findings = unsafe_perform_io(outcome.unwrap())
    assert [finding.resource for finding in findings] == ["pr-5"]
    assert _PR_LIST in runner.calls


def test_an_unmeasurable_budget_lets_deferrable_work_through() -> None:
    """A floor read that reported nothing fails OPEN, not closed.

    A preflight that could not be measured is not a reading of zero. If
    an unmeasurable budget refused deferrable work, a scan against any
    executor that cannot report headers would silently stop scanning.
    """
    runner = _Runner(responses={_PR_LIST: CommandResult(stdout=_stale_pr_listing())})

    outcome = stale_pr_findings(context=_scan_context(runner=runner))

    assert [finding.resource for finding in unsafe_perform_io(outcome.unwrap())] == ["pr-5"]


def test_a_gh_read_that_exits_non_zero_yields_an_empty_listing() -> None:
    """A non-zero exit and a refusal are the same answer here: nothing to report."""
    runner = _Runner(responses={_ORIGIN_URL: CommandResult(stdout="https://example.com/o/n\n")})

    outcome = stale_pr_findings(context=_scan_context(runner=runner))

    assert unsafe_perform_io(outcome.unwrap()) == []
    assert (*_PR_LIST, "--repo", "https://example.com/o/n") in runner.calls


def test_a_budgeted_response_carrying_a_foreign_value_names_itself() -> None:
    """The transport-agnostic `value` is read back in exactly one place."""
    invocation = _measurement().gh_invocation(value={"not": "an invocation"})

    assert invocation.unspawnable is not None
    assert "carried no gh outcome" in invocation.unspawnable


def test_a_deferral_is_restated_in_the_providers_failure_vocabulary() -> None:
    """The ratified `GithubFailure` union admits no deferral, so one is mapped."""
    budget = _budget()
    deferred = budget.GithubBudgetDeferred(
        resource="api repos/o/n/branches/b",
        remaining=8,
        floor=10,
        snapshot=budget.GithubRateLimitSnapshot(
            limit=5000, remaining=8, used=4992, reset=1720000000, resource="core"
        ),
    )

    failure = _process().budget_failure(failure=deferred, argv="gh api repos/o/n/branches/b")

    assert isinstance(failure, GithubQueryFailed)
    assert failure.detail == "deferred with 8 left of a 10 floor"


def test_an_unparseable_http_marker_reports_no_status() -> None:
    """A status that is not a number is no status, not a rate-limit signal."""
    measurement = _measurement()
    invocation = _budget().GhInvocation(
        argv="gh api repos/o/n", stderr="gh: broke (HTTP nope)", returncode=1
    )

    assert measurement.gh_status_code(invocation=invocation) == 0


def test_an_etag_is_withheld_from_a_subcommand_that_cannot_revalidate() -> None:
    """`gh_headers` is where the withholding happens, and it is total."""
    measurement = _measurement()
    invocation = _budget().GhInvocation(argv="gh pr view 1", stderr='< ETag: "e"')

    assert measurement.gh_headers(invocation=invocation, revalidatable=True) == {"etag": '"e"'}
    assert measurement.gh_headers(invocation=invocation, revalidatable=False) == {}


def test_header_extraction_reads_an_absent_stream_as_no_headers() -> None:
    """A stream `gh` never wrote carries no headers rather than raising."""
    budget = _budget()

    assert budget.extract_rate_limit_headers(text=None) == {}
    assert budget.extract_conditional_headers(text=None) == {}
