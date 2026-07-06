"""Tests for `livespec_runtime.hygiene_scan`."""

from datetime import datetime, timezone
from pathlib import Path

from livespec_runtime.hygiene_scan import CommandResult, scan_hygiene

__all__: list[str] = []


def test_scan_hygiene_emits_git_state_attention_items() -> None:
    repo = Path("/repo")
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout=(
                    "worktree /repo\n"
                    "HEAD base\n"
                    "branch refs/heads/master\n"
                    "\n"
                    "worktree /repo-old\n"
                    "HEAD oldsha\n"
                    "branch refs/heads/old\n"
                    "\n"
                    "worktree /repo-gone\n"
                    "HEAD gonesha\n"
                    "branch refs/heads/gone\n"
                    "prunable missing\n"
                )
            ),
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(
                stdout="/repo-current\n"
            ),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"): (
                CommandResult(stdout="refs/remotes/origin/master\n")
            ),
            ("git", "-C", "/repo-old", "status", "--porcelain"): CommandResult(stdout=""),
            ("git", "-C", "/repo", "merge-base", "--is-ancestor", "oldsha", "origin/master"): (
                CommandResult()
            ),
            ("git", "-C", "/repo", "status", "--porcelain"): CommandResult(stdout=" M README.md\n"),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "--short", "HEAD"): (
                CommandResult(stdout="feature\n")
            ),
            (
                "git",
                "-C",
                "/repo",
                "for-each-ref",
                "--format=%(refname:short)%00%(objectname)",
                "refs/heads",
            ): CommandResult(stdout="master\x00base\nmerged\x00mergedsha\nold\x00oldsha\n"),
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "mergedsha",
                "origin/master",
            ): CommandResult(),
            ("git", "-C", "/repo", "config", "--get", "remote.origin.url"): CommandResult(
                stdout="https://github.com/acme/repo.git\n"
            ),
            (
                "gh",
                "pr",
                "list",
                "--state",
                "open",
                "--json",
                "number,headRefName,updatedAt,title,url",
                "--repo",
                "https://github.com/acme/repo.git",
            ): CommandResult(
                stdout=(
                    '[{"number":7,"headRefName":"old-pr",'
                    '"updatedAt":"2026-05-01T00:00:00Z",'
                    '"title":"Old PR","url":"https://github.com/acme/repo/pull/7"}]'
                )
            ),
        }
    )

    items = scan_hygiene(
        repo_path=repo,
        repo_name="runtime",
        now=datetime(2026, 7, 6, tzinfo=timezone.utc),
        runner=runner.run,
    )

    assert [item.id for item in items] == [
        "hygiene:stale-worktree:/repo-old",
        "hygiene:stale-worktree:/repo-gone",
        "hygiene:primary-dirty:/repo",
        "hygiene:primary-off-default:/repo",
        "hygiene:stale-branch:refs/heads/merged",
        "hygiene:stale-pr:pr-7",
    ]
    assert {item.kind for item in items} == {"hygiene"}
    assert items[0].source_ref.repo == "runtime"
    assert items[0].handoff.command == "git -C /repo worktree remove /repo-old"
    assert items[-1].source_ref.path == "https://github.com/acme/repo/pull/7"


def test_scan_hygiene_degrades_when_github_is_unavailable() -> None:
    repo = Path("/repo")
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout="worktree /repo\nHEAD base\nbranch refs/heads/master\n"
            ),
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(stdout="/repo\n"),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"): (
                CommandResult(stdout="refs/remotes/origin/master\n")
            ),
            ("git", "-C", "/repo", "status", "--porcelain"): CommandResult(stdout=""),
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
            ("git", "-C", "/repo", "config", "--get", "remote.origin.url"): CommandResult(
                stdout="https://github.com/acme/repo.git\n"
            ),
            (
                "gh",
                "pr",
                "list",
                "--state",
                "open",
                "--json",
                "number,headRefName,updatedAt,title,url",
                "--repo",
                "https://github.com/acme/repo.git",
            ): CommandResult(returncode=1, stderr="authentication required"),
        }
    )

    assert (
        scan_hygiene(
            repo_path=repo,
            repo_name="runtime",
            now=datetime(2026, 7, 6, tzinfo=timezone.utc),
            runner=runner.run,
        )
        == []
    )


class _FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult]) -> None:
        self._responses = responses

    def run(self, *, argv: list[str], cwd: Path) -> CommandResult:
        _ = cwd
        return self._responses.get(tuple(argv), CommandResult(returncode=1, stderr="unexpected"))
