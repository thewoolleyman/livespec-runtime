"""Tests for the gh CLI provider — mocked subprocess.run."""

import json
import subprocess
from unittest.mock import MagicMock, patch

import pytest

from livespec_runtime.cross_repo.providers import github as gh_provider


def _mock_completed_process(*, stdout: str = "", returncode: int = 0) -> MagicMock:
    proc = MagicMock(spec=subprocess.CompletedProcess)
    proc.stdout = stdout
    proc.returncode = returncode
    proc.stderr = ""
    return proc


def test_query_pull_request_state_returns_state() -> None:
    with patch("subprocess.run") as run:
        run.return_value = _mock_completed_process(stdout=json.dumps({"state": "MERGED"}))
        state = gh_provider.query_pull_request_state(
            github_url="https://github.com/thewoolleyman/livespec", number=42
        )
    assert state == "MERGED"
    call_args = run.call_args[0][0]
    assert call_args[0] == "gh"
    assert "pr" in call_args
    assert "view" in call_args
    assert "42" in call_args


def test_branch_exists_on_remote_true_on_200() -> None:
    with patch("subprocess.run") as run:
        run.return_value = _mock_completed_process(stdout="{}")
        exists = gh_provider.branch_exists_on_remote(
            github_url="https://github.com/thewoolleyman/livespec", name="feat/foo"
        )
    assert exists is True


def test_branch_exists_on_remote_false_on_404() -> None:
    with patch("subprocess.run") as run:
        exc = subprocess.CalledProcessError(returncode=1, cmd=["gh"])
        exc.stderr = "gh: branch not found (HTTP 404)"
        run.side_effect = exc
        exists = gh_provider.branch_exists_on_remote(
            github_url="https://github.com/thewoolleyman/livespec", name="missing"
        )
    assert exists is False


def test_branch_exists_on_remote_propagates_non_404() -> None:
    with patch("subprocess.run") as run:
        exc = subprocess.CalledProcessError(returncode=1, cmd=["gh"])
        exc.stderr = "gh: auth failure (HTTP 401)"
        run.side_effect = exc
        with pytest.raises(subprocess.CalledProcessError):
            _ = gh_provider.branch_exists_on_remote(
                github_url="https://github.com/thewoolleyman/livespec", name="x"
            )


def test_branch_merged_into_default_true_on_identical_or_behind() -> None:
    for status in ("identical", "behind"):
        with patch("subprocess.run") as run:
            run.return_value = _mock_completed_process(
                stdout=json.dumps({"status": status, "ahead_by": 0, "behind_by": 0})
            )
            merged = gh_provider.branch_merged_into_default(
                github_url="https://github.com/thewoolleyman/livespec",
                name="feat/foo",
                default_branch="master",
            )
        assert merged is True


def test_branch_merged_into_default_false_on_ahead() -> None:
    with patch("subprocess.run") as run:
        run.return_value = _mock_completed_process(
            stdout=json.dumps({"status": "ahead", "ahead_by": 3, "behind_by": 0})
        )
        merged = gh_provider.branch_merged_into_default(
            github_url="https://github.com/thewoolleyman/livespec",
            name="feat/foo",
            default_branch="master",
        )
    assert merged is False


def test_split_owner_name_strips_prefix_and_suffix() -> None:
    assert (
        gh_provider._split_owner_name(  # noqa: SLF001 — testing private helper
            github_url="https://github.com/thewoolleyman/livespec"
        )
        == "thewoolleyman/livespec"
    )
    assert (
        gh_provider._split_owner_name(  # noqa: SLF001
            github_url="https://github.com/thewoolleyman/livespec.git"
        )
        == "thewoolleyman/livespec"
    )


def test_split_owner_name_rejects_non_canonical_url() -> None:
    with pytest.raises(gh_provider.NonCanonicalGithubUrlError):
        _ = gh_provider._split_owner_name(  # noqa: SLF001
            github_url="git@github.com:thewoolleyman/livespec.git"
        )
