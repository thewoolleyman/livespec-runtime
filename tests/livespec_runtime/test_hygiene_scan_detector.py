"""Tests for the shared `detect_stale_worktrees` detection seam."""

from pathlib import Path

from livespec_runtime.hygiene_scan import CommandResult, GitWorktree, detect_stale_worktrees

__all__: list[str] = []


def test_detect_stale_worktrees_flags_prunable_merged_and_rebase_merged() -> None:
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout=(
                    "worktree /repo\n"
                    "HEAD base\n"
                    "branch refs/heads/master\n"
                    "\n"
                    "worktree /repo-prunable\n"
                    "HEAD prunablesha\n"
                    "branch refs/heads/prunable\n"
                    "prunable gitdir file points to non-existent location\n"
                    "\n"
                    "worktree /repo-merged\n"
                    "HEAD mergedsha\n"
                    "branch refs/heads/merged\n"
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
            ("git", "-C", "/repo-merged", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "mergedsha",
                "origin/master",
            ): CommandResult(),
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
            # config absent -> forces the remote-tracking-ref push signal path.
            ("git", "-C", "/repo", "config", "--get", "branch.orphan.merge"): CommandResult(
                returncode=1
            ),
            (
                "git",
                "-C",
                "/repo",
                "rev-parse",
                "--verify",
                "--quiet",
                "refs/remotes/origin/orphan",
            ): CommandResult(stdout="orphansha\n"),
            ("git", "-C", "/repo", "ls-remote", "--heads", "origin", "orphan"): CommandResult(),
        }
    )

    result = detect_stale_worktrees(repo_path=Path("/repo"), runner=runner.run)

    assert [str(worktree.path) for worktree in result] == [
        "/repo-prunable",
        "/repo-merged",
        "/repo-orphan",
    ]
    assert all(isinstance(worktree, GitWorktree) for worktree in result)
    assert result[2].branch == "orphan"


def test_detect_stale_worktrees_skips_inprogress_and_undetermined_remotes() -> None:
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout=(
                    "worktree /repo\n"
                    "HEAD base\n"
                    "branch refs/heads/master\n"
                    "\n"
                    "worktree /repo-inprogress\n"
                    "HEAD inprogresssha\n"
                    "branch refs/heads/inprogress\n"
                    "\n"
                    "worktree /repo-remote-error\n"
                    "HEAD errorsha\n"
                    "branch refs/heads/remote-error\n"
                    "\n"
                    "worktree /repo-remote-present\n"
                    "HEAD presentsha\n"
                    "branch refs/heads/remote-present\n"
                )
            ),
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(
                stdout="/elsewhere\n"
            ),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"): (
                CommandResult(stdout="refs/remotes/origin/master\n")
            ),
            # in-progress: clean, not merged, never pushed (no upstream, no tracking ref).
            ("git", "-C", "/repo-inprogress", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "inprogresssha",
                "origin/master",
            ): CommandResult(returncode=1),
            ("git", "-C", "/repo", "config", "--get", "branch.inprogress.merge"): CommandResult(
                returncode=1
            ),
            (
                "git",
                "-C",
                "/repo",
                "rev-parse",
                "--verify",
                "--quiet",
                "refs/remotes/origin/inprogress",
            ): CommandResult(returncode=1),
            # remote-error: clean, not merged, pushed (upstream cfg), but ls-remote errors.
            ("git", "-C", "/repo-remote-error", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "errorsha",
                "origin/master",
            ): CommandResult(returncode=1),
            ("git", "-C", "/repo", "config", "--get", "branch.remote-error.merge"): CommandResult(
                stdout="refs/heads/remote-error\n"
            ),
            ("git", "-C", "/repo", "ls-remote", "--heads", "origin", "remote-error"): CommandResult(
                returncode=2, stderr="fatal: 'origin' does not appear to be a git repository\n"
            ),
            # remote-present: clean, not merged, pushed (upstream cfg), remote STILL present.
            ("git", "-C", "/repo-remote-present", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "presentsha",
                "origin/master",
            ): CommandResult(returncode=1),
            (
                "git",
                "-C",
                "/repo",
                "config",
                "--get",
                "branch.remote-present.merge",
            ): CommandResult(stdout="refs/heads/remote-present\n"),
            ("git", "-C", "/repo", "ls-remote", "--heads", "origin", "remote-present"): (
                CommandResult(stdout="presentsha\trefs/heads/remote-present\n")
            ),
        }
    )

    assert detect_stale_worktrees(repo_path=Path("/repo"), runner=runner.run) == []


def test_detect_stale_worktrees_includes_current_working_directory() -> None:
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout=(
                    "worktree /repo\n"
                    "HEAD base\n"
                    "branch refs/heads/master\n"
                    "\n"
                    "worktree /repo-orphan\n"
                    "HEAD orphansha\n"
                    "branch refs/heads/orphan\n"
                )
            ),
            # The scan runs FROM INSIDE the orphan worktree: its toplevel is
            # the orphan path. The detector must NOT skip the cwd — that skip
            # is the reaper's action-layer concern, not detection's.
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(
                stdout="/repo-orphan\n"
            ),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"): (
                CommandResult(stdout="refs/remotes/origin/master\n")
            ),
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


class _FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult]) -> None:
        self._responses = responses

    def run(self, *, argv: list[str], cwd: Path) -> CommandResult:
        _ = cwd
        return self._responses.get(tuple(argv), CommandResult(returncode=1, stderr="unexpected"))
