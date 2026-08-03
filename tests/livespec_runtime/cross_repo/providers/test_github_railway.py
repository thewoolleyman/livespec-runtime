"""The `gh` provider answers on a railway, not by raising.

Every query in this provider previously raised
`subprocess.CalledProcessError` / `json.JSONDecodeError` / `KeyError` on
failure and relied on `retry.retry_with_backoff` catching `Exception`
broadly. Those tests live in `test_github.py`; these assert the railway
itself — that a query which produced an ANSWER lands on the success
track, and one that did not lands on the failure track NAMING the
command, so the reason survives instead of collapsing to a bare `None`
two layers up.
"""

import json
import subprocess
from typing import Any

import pytest
from returns.io import IOFailure, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.cross_repo.providers.github import (
    GithubQueryFailed,
    query_pull_request_state,
)

__all__: list[str] = []

_REPO = "https://github.com/thewoolleyman/livespec"


def test_query_pull_request_state_carries_the_state_on_the_success_track(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=argv, returncode=0, stdout=json.dumps({"state": "OPEN"}), stderr=""
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    outcome = query_pull_request_state(github_url=_REPO, number=42)

    assert isinstance(outcome, IOSuccess)
    assert unsafe_perform_io(outcome.unwrap()) == "OPEN"


def test_query_pull_request_state_routes_a_failed_gh_to_the_failure_track(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        _ = argv
        error = subprocess.CalledProcessError(returncode=1, cmd=["gh"])
        error.stderr = "gh: Not Found (HTTP 404)"
        raise error

    monkeypatch.setattr(subprocess, "run", fake_run)

    outcome = query_pull_request_state(github_url=_REPO, number=42)

    assert isinstance(outcome, IOFailure)
    failure = unsafe_perform_io(outcome.failure())
    assert isinstance(failure, GithubQueryFailed)
    assert failure.argv.startswith("gh pr view 42")
    assert "HTTP 404" in failure.detail
