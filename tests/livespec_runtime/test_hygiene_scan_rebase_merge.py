"""Rebase-merge orphan detection for `livespec_runtime.hygiene_scan`.

This fleet merges by rebase, which rewrites commit SHAs, so a
rebase-merged orphan worktree's HEAD is NOT a literal ancestor of
`origin/HEAD` and the ancestor test misses it. The extended
stale-worktree predicate must still flag it via the reliable
pushed-then-remote-gone signal.
"""

from pathlib import Path

from livespec_runtime.hygiene_scan import CommandResult, scan_hygiene

__all__: list[str] = []


def test_scan_hygiene_flags_rebase_merged_orphan_worktree() -> None:
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
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(
                stdout="/elsewhere\n"
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
            ("git", "-C", "/repo", "status", "--porcelain"): CommandResult(),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "--short", "HEAD"): CommandResult(
                stdout="master\n"
            ),
            (
                "git",
                "-C",
                "/repo",
                "for-each-ref",
                "--format=%(refname:short)%00%(objectname)",
                "refs/heads",
            ): CommandResult(stdout="master\x00base\norphan\x00orphansha\n"),
        }
    )

    items = scan_hygiene(
        repo_path=Path("/repo"),
        repo_name="runtime",
        include_prs=False,
        runner=runner.run,
    )

    assert [item.id for item in items] == ["hygiene:stale-worktree:/repo-orphan"]
    assert items[0].handoff.command == "git -C /repo worktree remove /repo-orphan"


class _FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult]) -> None:
        self._responses = responses

    def run(self, *, argv: list[str], cwd: Path) -> CommandResult:
        _ = cwd
        return self._responses.get(tuple(argv), CommandResult(returncode=1, stderr="unexpected"))
