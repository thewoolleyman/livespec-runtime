"""Every reader in the hygiene scan PROPAGATES an unspawnable command.

The value of putting `run_command` on the railway is not the leaf's own
return type — it is that a command which could not be spawned reaches the
caller instead of being absorbed into a default. Each test here makes
exactly ONE command unspawnable and asserts the failure comes back out
NAMING that command, so an absorption anywhere on the path fails a test
rather than silently shrinking the scan's output.
"""

import shlex
from datetime import datetime, timedelta, timezone
from pathlib import Path

from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.hygiene_scan_context import build_context
from livespec_runtime.hygiene_scan_findings import (
    primary_health_findings,
    stale_branch_findings,
    stale_pr_findings,
)
from livespec_runtime.hygiene_scan_types import (
    CommandResult,
    CommandUnavailable,
    GitWorktree,
    ScanContext,
)
from livespec_runtime.hygiene_scan_worktrees import (
    branch_was_rebase_merged,
    landed_worktree_finding,
    stale_worktree_finding,
    stale_worktree_findings,
)

__all__: list[str] = []

_REPO = Path("/repo")
_OTHER = Path("/repo-other")


class _Runner:
    """Answers every command except the ONE designated unspawnable."""

    def __init__(
        self,
        *,
        unspawnable: tuple[str, ...],
        responses: dict[tuple[str, ...], CommandResult] | None = None,
    ) -> None:
        self._unspawnable = unspawnable
        self._responses = responses or {}

    def run(self, *, argv: list[str], cwd: Path) -> IOResult[CommandResult, CommandUnavailable]:
        _ = cwd
        if tuple(argv) == self._unspawnable:
            return IOFailure(
                CommandUnavailable(argv=shlex.join(argv), detail="No such file or directory")
            )
        return IOSuccess(self._responses.get(tuple(argv), CommandResult()))


def _context(*, runner: _Runner, worktree_listing: str = "") -> ScanContext:
    """A ScanContext built directly, so each test isolates ONE failing command."""
    _ = worktree_listing
    return ScanContext(
        repo_path=_REPO,
        repo_name="repo",
        primary_path=_REPO,
        current_path=_REPO,
        base_ref="origin/master",
        default_branch="master",
        now=datetime(2026, 8, 3, tzinfo=timezone.utc),
        stale_after=timedelta(days=30),
        runner=runner.run,
    )


def _unavailable(outcome: IOResult[object, CommandUnavailable]) -> CommandUnavailable:
    """The failure an outcome carries, asserting it took the failure track."""
    assert isinstance(outcome, IOFailure)
    return unsafe_perform_io(outcome.failure())


_WORKTREE_LIST = ("git", "-C", "/repo", "worktree", "list", "--porcelain")
_ONE_OTHER_WORKTREE = CommandResult(
    stdout=(
        "worktree /repo\nHEAD base\nbranch refs/heads/master\n\n"
        "worktree /repo-other\nHEAD othersha\nbranch refs/heads/other\n"
    )
)


def test_build_context_propagates_an_unlistable_worktree_set() -> None:
    runner = _Runner(unspawnable=_WORKTREE_LIST)

    outcome = build_context(
        repo_path=_REPO, repo_name=None, now=None, stale_days=30, runner=runner.run
    )

    assert _unavailable(outcome).argv == "git -C /repo worktree list --porcelain"


def test_build_context_propagates_an_unreadable_toplevel() -> None:
    runner = _Runner(unspawnable=("git", "-C", "/repo", "rev-parse", "--show-toplevel"))

    outcome = build_context(
        repo_path=_REPO, repo_name=None, now=None, stale_days=30, runner=runner.run
    )

    assert _unavailable(outcome).argv == "git -C /repo rev-parse --show-toplevel"


def test_build_context_propagates_an_unreadable_origin_head() -> None:
    runner = _Runner(
        unspawnable=("git", "-C", "/repo", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD")
    )

    outcome = build_context(
        repo_path=_REPO, repo_name=None, now=None, stale_days=30, runner=runner.run
    )

    assert "refs/remotes/origin/HEAD" in _unavailable(outcome).argv


def test_primary_health_findings_propagates_an_unreadable_status() -> None:
    runner = _Runner(unspawnable=("git", "-C", "/repo", "status", "--porcelain"))

    outcome = primary_health_findings(context=_context(runner=runner))

    assert _unavailable(outcome).argv == "git -C /repo status --porcelain"


def test_primary_health_findings_propagates_an_unreadable_branch() -> None:
    runner = _Runner(
        unspawnable=("git", "-C", "/repo", "symbolic-ref", "--quiet", "--short", "HEAD")
    )

    outcome = primary_health_findings(context=_context(runner=runner))

    assert "--short" in _unavailable(outcome).argv


def test_stale_branch_findings_propagates_an_unlistable_worktree_set() -> None:
    runner = _Runner(unspawnable=_WORKTREE_LIST)

    outcome = stale_branch_findings(context=_context(runner=runner))

    assert _unavailable(outcome).argv == "git -C /repo worktree list --porcelain"


def test_stale_branch_findings_propagates_an_unreadable_ref_listing() -> None:
    runner = _Runner(
        unspawnable=(
            "git",
            "-C",
            "/repo",
            "for-each-ref",
            "--format=%(refname:short)%00%(objectname)",
            "refs/heads",
        )
    )

    outcome = stale_branch_findings(context=_context(runner=runner))

    assert "for-each-ref" in _unavailable(outcome).argv


def test_stale_branch_findings_propagates_an_unanswerable_merge_base() -> None:
    runner = _Runner(
        unspawnable=("git", "-C", "/repo", "merge-base", "--is-ancestor", "sha", "origin/master"),
        responses={
            (
                "git",
                "-C",
                "/repo",
                "for-each-ref",
                "--format=%(refname:short)%00%(objectname)",
                "refs/heads",
            ): CommandResult(stdout="feature\x00sha\n")
        },
    )

    outcome = stale_branch_findings(context=_context(runner=runner))

    assert "merge-base" in _unavailable(outcome).argv


def test_stale_pr_findings_propagates_an_unreadable_origin_url() -> None:
    runner = _Runner(unspawnable=("git", "-C", "/repo", "config", "--get", "remote.origin.url"))

    outcome = stale_pr_findings(context=_context(runner=runner))

    assert "remote.origin.url" in _unavailable(outcome).argv


def test_stale_pr_findings_propagates_an_unspawnable_gh() -> None:
    runner = _Runner(
        unspawnable=(
            "gh",
            "pr",
            "list",
            "--state",
            "open",
            "--json",
            "number,headRefName,updatedAt,title,url",
        )
    )

    outcome = stale_pr_findings(context=_context(runner=runner))

    assert _unavailable(outcome).argv.startswith("gh pr list")


def test_stale_worktree_findings_propagates_an_unlistable_worktree_set() -> None:
    runner = _Runner(unspawnable=_WORKTREE_LIST)

    outcome = stale_worktree_findings(context=_context(runner=runner))

    assert _unavailable(outcome).argv == "git -C /repo worktree list --porcelain"


def test_stale_worktree_findings_propagates_a_per_worktree_failure() -> None:
    runner = _Runner(
        unspawnable=("git", "-C", "/repo-other", "status", "--porcelain"),
        responses={_WORKTREE_LIST: _ONE_OTHER_WORKTREE},
    )

    outcome = stale_worktree_findings(context=_context(runner=runner))

    assert _unavailable(outcome).argv == "git -C /repo-other status --porcelain"


def test_stale_worktree_finding_propagates_an_unreadable_cleanliness() -> None:
    runner = _Runner(unspawnable=("git", "-C", "/repo-other", "status", "--porcelain"))

    outcome = stale_worktree_finding(
        context=_context(runner=runner),
        worktree=GitWorktree(path=_OTHER, head="othersha", branch="other"),
    )

    assert _unavailable(outcome).argv == "git -C /repo-other status --porcelain"


def test_landed_worktree_finding_propagates_an_unanswerable_merge_base() -> None:
    runner = _Runner(
        unspawnable=(
            "git",
            "-C",
            "/repo",
            "merge-base",
            "--is-ancestor",
            "othersha",
            "origin/master",
        )
    )

    outcome = landed_worktree_finding(
        context=_context(runner=runner),
        worktree=GitWorktree(path=_OTHER, head="othersha", branch="other"),
        label="/repo-other",
    )

    assert "merge-base" in _unavailable(outcome).argv


def test_landed_worktree_finding_propagates_an_unreadable_rebase_merge_signal() -> None:
    runner = _Runner(
        unspawnable=("git", "-C", "/repo", "config", "--get", "branch.other.merge"),
        responses={
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "othersha",
                "origin/master",
            ): CommandResult(returncode=1)
        },
    )

    outcome = landed_worktree_finding(
        context=_context(runner=runner),
        worktree=GitWorktree(path=_OTHER, head="othersha", branch="other"),
        label="/repo-other",
    )

    assert _unavailable(outcome).argv == "git -C /repo config --get branch.other.merge"


def test_branch_was_rebase_merged_propagates_an_unreadable_upstream_config() -> None:
    runner = _Runner(unspawnable=("git", "-C", "/repo", "config", "--get", "branch.other.merge"))

    outcome = branch_was_rebase_merged(
        context=_context(runner=runner),
        worktree=GitWorktree(path=_OTHER, head="othersha", branch="other"),
    )

    assert _unavailable(outcome).argv == "git -C /repo config --get branch.other.merge"
