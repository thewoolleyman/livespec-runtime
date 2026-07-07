"""Default-branch worktrees are MAINLINE, never stale-worktree candidates.

A secondary worktree checked out on the repo's default branch
(`master`/`main`) is clean and its HEAD is trivially an ancestor of
`origin/HEAD` (the default branch IS `origin/HEAD`), so the merged/
rebase-merge predicates would wrongly flag it and the consuming reaper
would `git worktree remove` + `branch -D master` (which errors). The
guard lives in the SHARED `_stale_worktree_finding` predicate so BOTH
`detect_stale_worktrees` and `scan_hygiene` are fixed on one path.
"""

from datetime import datetime, timezone
from pathlib import Path

from livespec_runtime.hygiene_scan import (
    CommandResult,
    detect_stale_worktrees,
    scan_hygiene,
)

__all__: list[str] = []


def test_detect_stale_worktrees_skips_secondary_default_branch_worktree() -> None:
    # Primary /repo on master; a SECONDARY worktree /repo-master-wt also on
    # master (clean); and a genuine rebase-merged orphan /repo-orphan
    # (pushed + remote-gone) to prove the guard is NARROW — mainline is
    # spared while real orphans are still flagged.
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout=(
                    "worktree /repo\n"
                    "HEAD base\n"
                    "branch refs/heads/master\n"
                    "\n"
                    "worktree /repo-master-wt\n"
                    "HEAD masterhead\n"
                    "branch refs/heads/master\n"
                    "\n"
                    "worktree /repo-orphan\n"
                    "HEAD orphansha\n"
                    "branch refs/heads/orphan\n"
                )
            ),
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(
                stdout="/elsewhere\n"
            ),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"): (
                CommandResult(stdout="refs/remotes/origin/master\n")
            ),
            # /repo-master-wt: clean AND merged (its HEAD IS origin/master) —
            # the buggy predicate flags it; the guard must spare it.
            ("git", "-C", "/repo-master-wt", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "masterhead",
                "origin/master",
            ): CommandResult(),
            # /repo-orphan: clean, NOT merged, pushed (upstream cfg), remote gone.
            ("git", "-C", "/repo-orphan", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "orphansha",
                "origin/master",
            ): CommandResult(returncode=1),
            ("git", "-C", "/repo", "config", "--get", "branch.orphan.merge"): CommandResult(
                stdout="refs/heads/orphan\n"
            ),
            ("git", "-C", "/repo", "ls-remote", "--heads", "origin", "orphan"): CommandResult(),
        }
    )

    result = detect_stale_worktrees(repo_path=Path("/repo"), runner=runner.run)

    assert [str(worktree.path) for worktree in result] == ["/repo-orphan"]


def test_scan_hygiene_emits_no_stale_worktree_finding_for_default_branch_worktree() -> None:
    # scan_hygiene's needs-attention surface uses the SAME shared predicate;
    # a clean secondary worktree on the default branch must produce NO
    # stale-worktree finding there either.
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout=(
                    "worktree /repo\n"
                    "HEAD base\n"
                    "branch refs/heads/master\n"
                    "\n"
                    "worktree /repo-master-wt\n"
                    "HEAD masterhead\n"
                    "branch refs/heads/master\n"
                )
            ),
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(stdout="/repo\n"),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"): (
                CommandResult(stdout="refs/remotes/origin/master\n")
            ),
            ("git", "-C", "/repo-master-wt", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "masterhead",
                "origin/master",
            ): CommandResult(),
            # primary-health + stale-branch reads: primary clean, on master,
            # only master exists locally -> no non-worktree findings.
            ("git", "-C", "/repo", "status", "--porcelain"): CommandResult(),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "--short", "HEAD"): (
                CommandResult(stdout="master\n")
            ),
            (
                "git",
                "-C",
                "/repo",
                "for-each-ref",
                "--format=%(refname:short)%00%(objectname)",
                "refs/heads",
            ): CommandResult(stdout="master\x00base\n"),
        }
    )

    items = scan_hygiene(
        repo_path=Path("/repo"),
        repo_name="runtime",
        now=datetime(2026, 7, 8, tzinfo=timezone.utc),
        include_prs=False,
        runner=runner.run,
    )

    stale = [item for item in items if item.id.startswith("hygiene:stale-worktree:")]
    assert stale == []


def test_detect_stale_worktrees_still_flags_detached_worktree_at_default_commit() -> None:
    # DELIBERATE detached-HEAD decision (documented in the impl comment):
    # a DETACHED worktree parked at the default-branch commit has NO named
    # branch, so the branch-name guard does not match it and it stays a
    # candidate. Removing it is `git worktree remove` ONLY — there is no
    # branch to `branch -D`, so the destructive regression cannot recur.
    # Guarding it would REGRESS the existing merged-detached-worktree cleanup.
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout=(
                    "worktree /repo\n"
                    "HEAD base\n"
                    "branch refs/heads/master\n"
                    "\n"
                    "worktree /repo-detached\n"
                    "HEAD detachedsha\n"
                    "detached\n"
                )
            ),
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(
                stdout="/elsewhere\n"
            ),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"): (
                CommandResult(stdout="refs/remotes/origin/master\n")
            ),
            ("git", "-C", "/repo-detached", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "detachedsha",
                "origin/master",
            ): CommandResult(),
        }
    )

    result = detect_stale_worktrees(repo_path=Path("/repo"), runner=runner.run)

    assert [str(worktree.path) for worktree in result] == ["/repo-detached"]
    assert result[0].detached is True
    assert result[0].branch is None


class _FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult]) -> None:
        self._responses = responses

    def run(self, *, argv: list[str], cwd: Path) -> CommandResult:
        _ = cwd
        return self._responses.get(tuple(argv), CommandResult(returncode=1, stderr="unexpected"))
