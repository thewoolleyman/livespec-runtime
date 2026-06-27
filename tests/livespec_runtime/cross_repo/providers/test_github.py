"""Tests for `livespec_runtime.cross_repo.providers.github`.

Verifies the gh CLI subprocess dispatch surface: PR state query,
remote branch existence check, branch-merged-into-default compare,
and the canonical-github-url enforcement.

All tests mock `subprocess.run` (no real `gh` invocations). Recorded
gh responses live as fixture JSON files under `fixtures/`; loading
through `Path.read_text` keeps the test bodies focused on argv shape
and the impl's interpretation of the response payload.

Schema reference: livespec/SPECIFICATION/contracts.md v072.
"""

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from livespec_runtime.cross_repo.providers.github import (
    NonCanonicalGithubUrlError,
    branch_exists_on_remote,
    branch_merged_into_default,
    query_pull_request_state,
)

__all__: list[str] = []

_FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(*, name: str) -> str:
    return (_FIXTURES / name).read_text()


def _make_completed_process(
    *,
    args: list[str],
    stdout: str = "",
    stderr: str = "",
    returncode: int = 0,
) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        args=args,
        returncode=returncode,
        stdout=stdout,
        stderr=stderr,
    )


def _make_called_process_error(*, stderr: str) -> subprocess.CalledProcessError:
    exc = subprocess.CalledProcessError(returncode=1, cmd=["gh"])
    exc.stderr = stderr
    return exc


def test_query_pull_request_state_returns_open(monkeypatch: pytest.MonkeyPatch) -> None:
    captured_argv: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured_argv.append(argv)
        return _make_completed_process(args=argv, stdout=_load_fixture(name="pr_view_open.json"))

    monkeypatch.setattr(subprocess, "run", fake_run)
    state = query_pull_request_state(
        github_url="https://github.com/thewoolleyman/livespec",
        number=42,
    )
    assert state == "OPEN"


def test_query_pull_request_state_returns_merged(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return _make_completed_process(args=argv, stdout=_load_fixture(name="pr_view_merged.json"))

    monkeypatch.setattr(subprocess, "run", fake_run)
    state = query_pull_request_state(
        github_url="https://github.com/thewoolleyman/livespec",
        number=42,
    )
    assert state == "MERGED"


def test_query_pull_request_state_returns_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return _make_completed_process(args=argv, stdout=_load_fixture(name="pr_view_closed.json"))

    monkeypatch.setattr(subprocess, "run", fake_run)
    state = query_pull_request_state(
        github_url="https://github.com/thewoolleyman/livespec",
        number=42,
    )
    assert state == "CLOSED"


def test_query_pull_request_state_invokes_gh_pr_view(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured.append(argv)
        return _make_completed_process(args=argv, stdout=_load_fixture(name="pr_view_open.json"))

    monkeypatch.setattr(subprocess, "run", fake_run)
    _ = query_pull_request_state(
        github_url="https://github.com/thewoolleyman/livespec",
        number=42,
    )
    assert captured == [
        [
            "gh",
            "pr",
            "view",
            "42",
            "--repo",
            "https://github.com/thewoolleyman/livespec",
            "--json",
            "state",
        ],
    ]


def test_branch_exists_on_remote_true_on_present(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return _make_completed_process(
            args=argv,
            stdout=_load_fixture(name="branch_view_present.json"),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert (
        branch_exists_on_remote(
            github_url="https://github.com/thewoolleyman/livespec",
            name="feat/foo",
        )
        is True
    )


def test_branch_exists_on_remote_false_on_404(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(_argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise _make_called_process_error(stderr="gh: branch not found (HTTP 404)")

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert (
        branch_exists_on_remote(
            github_url="https://github.com/thewoolleyman/livespec",
            name="missing",
        )
        is False
    )


def test_branch_exists_on_remote_propagates_non_404(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(_argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise _make_called_process_error(stderr="gh: auth failure (HTTP 401)")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(subprocess.CalledProcessError):
        _ = branch_exists_on_remote(
            github_url="https://github.com/thewoolleyman/livespec",
            name="feat/foo",
        )


def test_branch_exists_on_remote_propagates_when_stderr_empty(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(_argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise _make_called_process_error(stderr="")

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(subprocess.CalledProcessError):
        _ = branch_exists_on_remote(
            github_url="https://github.com/thewoolleyman/livespec",
            name="feat/foo",
        )


def test_branch_exists_on_remote_propagates_when_unrelated_404_substring(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Regression guard for li-y2hd44.

    An unrelated stderr fragment containing '404' as content (e.g. a
    body-text mention of a 404-redirect target, an error body that
    happens to include the digits, etc.) MUST NOT be mis-categorized
    as a real HTTP 404. The detection MUST key off the structured
    `HTTP 404` prefix (or the exit-code carrier) per
    SPECIFICATION/history/v003/contracts.md.
    """
    unrelated_stderr = "gh: rate limit exceeded; see https://example.com/404-redirect (HTTP 403)"

    def fake_run(_argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        raise _make_called_process_error(stderr=unrelated_stderr)

    monkeypatch.setattr(subprocess, "run", fake_run)
    with pytest.raises(subprocess.CalledProcessError):
        _ = branch_exists_on_remote(
            github_url="https://github.com/thewoolleyman/livespec",
            name="feat/foo",
        )


def test_branch_exists_on_remote_invokes_gh_api(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured.append(argv)
        return _make_completed_process(
            args=argv,
            stdout=_load_fixture(name="branch_view_present.json"),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    _ = branch_exists_on_remote(
        github_url="https://github.com/thewoolleyman/livespec",
        name="feat/foo",
    )
    assert captured == [
        [
            "gh",
            "api",
            "repos/thewoolleyman/livespec/branches/feat/foo",
        ],
    ]


def test_branch_exists_on_remote_raises_on_non_canonical_url() -> None:
    with pytest.raises(NonCanonicalGithubUrlError):
        _ = branch_exists_on_remote(
            github_url="git@github.com:thewoolleyman/livespec.git",
            name="feat/foo",
        )


def test_branch_merged_into_default_true_when_identical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return _make_completed_process(
            args=argv,
            stdout=_load_fixture(name="branch_compare_identical.json"),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert (
        branch_merged_into_default(
            github_url="https://github.com/thewoolleyman/livespec",
            name="feat/foo",
            default_branch="master",
        )
        is True
    )


def test_branch_merged_into_default_true_when_behind(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return _make_completed_process(
            args=argv,
            stdout=_load_fixture(name="branch_compare_behind.json"),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert (
        branch_merged_into_default(
            github_url="https://github.com/thewoolleyman/livespec",
            name="feat/foo",
            default_branch="master",
        )
        is True
    )


def test_branch_merged_into_default_false_when_ahead(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return _make_completed_process(
            args=argv,
            stdout=_load_fixture(name="branch_compare_ahead.json"),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert (
        branch_merged_into_default(
            github_url="https://github.com/thewoolleyman/livespec",
            name="feat/foo",
            default_branch="master",
        )
        is False
    )


def test_branch_merged_into_default_false_when_diverged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        return _make_completed_process(
            args=argv,
            stdout=_load_fixture(name="branch_compare_diverged.json"),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    assert (
        branch_merged_into_default(
            github_url="https://github.com/thewoolleyman/livespec",
            name="feat/foo",
            default_branch="master",
        )
        is False
    )


def test_branch_merged_into_default_invokes_gh_api_compare(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured.append(argv)
        return _make_completed_process(
            args=argv,
            stdout=_load_fixture(name="branch_compare_identical.json"),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    _ = branch_merged_into_default(
        github_url="https://github.com/thewoolleyman/livespec",
        name="feat/foo",
        default_branch="master",
    )
    assert captured == [
        [
            "gh",
            "api",
            "repos/thewoolleyman/livespec/compare/master...feat/foo",
        ],
    ]


def test_branch_merged_into_default_raises_on_non_canonical_url() -> None:
    with pytest.raises(NonCanonicalGithubUrlError):
        _ = branch_merged_into_default(
            github_url="git@github.com:thewoolleyman/livespec.git",
            name="feat/foo",
            default_branch="master",
        )


def test_branch_merged_into_default_accepts_dot_git_suffix(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured.append(argv)
        return _make_completed_process(
            args=argv,
            stdout=_load_fixture(name="branch_compare_identical.json"),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    _ = branch_merged_into_default(
        github_url="https://github.com/thewoolleyman/livespec.git",
        name="feat/foo",
        default_branch="master",
    )
    assert captured == [
        [
            "gh",
            "api",
            "repos/thewoolleyman/livespec/compare/master...feat/foo",
        ],
    ]


def test_branch_merged_into_default_accepts_trailing_slash(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: list[list[str]] = []

    def fake_run(argv: list[str], **_kwargs: Any) -> subprocess.CompletedProcess[str]:
        captured.append(argv)
        return _make_completed_process(
            args=argv,
            stdout=_load_fixture(name="branch_compare_identical.json"),
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    _ = branch_merged_into_default(
        github_url="https://github.com/thewoolleyman/livespec/",
        name="feat/foo",
        default_branch="master",
    )
    assert captured == [
        [
            "gh",
            "api",
            "repos/thewoolleyman/livespec/compare/master...feat/foo",
        ],
    ]


def test_non_canonical_github_url_error_carries_url() -> None:
    exc = NonCanonicalGithubUrlError(github_url="git@github.com:owner/repo.git")
    assert exc.github_url == "git@github.com:owner/repo.git"
    assert "git@github.com:owner/repo.git" in str(exc)


def test_fixture_payload_round_trips_through_json() -> None:
    payload: dict[str, Any] = json.loads(_load_fixture(name="branch_compare_identical.json"))
    assert payload["status"] == "identical"
