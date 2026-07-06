"""Edge-case tests for `livespec_runtime.hygiene_scan`."""

from io import StringIO
from pathlib import Path

from livespec_runtime.hygiene_scan import CommandResult, main, scan_hygiene

__all__: list[str] = []


def test_scan_hygiene_handles_empty_git_context_without_pr_scan() -> None:
    runner = _FakeRunner(
        {
            ("git", "-C", "/empty", "worktree", "list", "--porcelain"): CommandResult(),
            ("git", "-C", "/empty", "rev-parse", "--show-toplevel"): CommandResult(),
            (
                "git",
                "-C",
                "/empty",
                "symbolic-ref",
                "--quiet",
                "refs/remotes/origin/HEAD",
            ): CommandResult(returncode=1),
            ("git", "-C", "/empty", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/empty",
                "symbolic-ref",
                "--quiet",
                "--short",
                "HEAD",
            ): CommandResult(stdout="HEAD\n"),
            (
                "git",
                "-C",
                "/empty",
                "for-each-ref",
                "--format=%(refname:short)%00%(objectname)",
                "refs/heads",
            ): CommandResult(returncode=1),
        }
    )

    assert scan_hygiene(repo_path=Path("/empty"), include_prs=False, runner=runner.run) == []


def test_scan_hygiene_reports_detached_primary_and_skips_unsafe_worktrees() -> None:
    worktrees = (
        "worktree /repo\n"
        "HEAD base\n"
        "branch refs/heads/main\n"
        "\n"
        "worktree /repo-detached\n"
        "detached\n"
        "\n"
        "worktree /repo-dirty\n"
        "HEAD dirtysha\n"
        "branch refs/heads/dirty\n"
        "\n"
        "worktree /repo-unmerged\n"
        "HEAD unmergedsha\n"
        "branch refs/heads/unmerged\n"
    )
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout=worktrees
            ),
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(
                stdout="/elsewhere\n"
            ),
            (
                "git",
                "-C",
                "/repo",
                "symbolic-ref",
                "--quiet",
                "refs/remotes/origin/HEAD",
            ): CommandResult(stdout="refs/remotes/origin/main\n"),
            ("git", "-C", "/repo-detached", "status", "--porcelain"): CommandResult(),
            ("git", "-C", "/repo-dirty", "status", "--porcelain"): CommandResult(
                stdout=" M file\n"
            ),
            ("git", "-C", "/repo-unmerged", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "merge-base",
                "--is-ancestor",
                "unmergedsha",
                "origin/main",
            ): CommandResult(returncode=1),
            ("git", "-C", "/repo", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "symbolic-ref",
                "--quiet",
                "--short",
                "HEAD",
            ): CommandResult(returncode=1),
            (
                "git",
                "-C",
                "/repo",
                "for-each-ref",
                "--format=%(refname:short)%00%(objectname)",
                "refs/heads",
            ): CommandResult(stdout="main\x00base\nmalformed\nactive\x00unmergedsha\n"),
        }
    )

    items = scan_hygiene(repo_path=Path("/repo"), include_prs=False, runner=runner.run)

    assert [item.id for item in items] == ["hygiene:primary-detached:/repo"]
    assert items[0].handoff.command == "git -C /repo switch main"


def test_scan_hygiene_ignores_malformed_pr_payloads_and_keeps_stale_defaults() -> None:
    base = {
        ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
            stdout="worktree /repo\nHEAD base\nbranch refs/heads/main\n"
        ),
        ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(stdout="/repo\n"),
        (
            "git",
            "-C",
            "/repo",
            "symbolic-ref",
            "--quiet",
            "refs/remotes/origin/HEAD",
        ): CommandResult(stdout="refs/remotes/origin/main\n"),
        ("git", "-C", "/repo", "status", "--porcelain"): CommandResult(),
        (
            "git",
            "-C",
            "/repo",
            "symbolic-ref",
            "--quiet",
            "--short",
            "HEAD",
        ): CommandResult(stdout="main\n"),
        (
            "git",
            "-C",
            "/repo",
            "for-each-ref",
            "--format=%(refname:short)%00%(objectname)",
            "refs/heads",
        ): CommandResult(stdout="main\x00base\n"),
        ("git", "-C", "/repo", "config", "--get", "remote.origin.url"): CommandResult(),
    }
    runner = _FakeRunner(
        {
            **base,
            ("gh", "pr", "list", "--state", "open", "--json", _PR_FIELDS): CommandResult(
                stdout=(
                    '[1,{"number":"bad","updatedAt":"2026-01-01T00:00:00Z"},'
                    '{"number":8,"updatedAt":"bad"},'
                    '{"number":9,"updatedAt":"2026-07-01T00:00:00Z"},'
                    '{"number":10,"updatedAt":"2026-05-01T00:00:00"}]'
                )
            ),
        }
    )

    items = scan_hygiene(repo_path=Path("/repo"), runner=runner.run)

    assert [item.id for item in items] == ["hygiene:stale-pr:pr-10"]
    assert items[0].summary == "Open PR #10 (PR #10) on unknown branch has gone stale."

    invalid_json = _FakeRunner(
        {
            **base,
            ("gh", "pr", "list", "--state", "open", "--json", _PR_FIELDS): CommandResult(
                stdout="{"
            ),
        }
    )
    assert scan_hygiene(repo_path=Path("/repo"), runner=invalid_json.run) == []

    non_list = _FakeRunner(
        {
            **base,
            ("gh", "pr", "list", "--state", "open", "--json", _PR_FIELDS): CommandResult(
                stdout="{}"
            ),
        }
    )
    assert scan_hygiene(repo_path=Path("/repo"), runner=non_list.run) == []


def test_main_writes_json_and_rejects_negative_stale_days() -> None:
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout="worktree /repo\nHEAD base\nbranch refs/heads/main\n"
            ),
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(stdout="/repo\n"),
            (
                "git",
                "-C",
                "/repo",
                "symbolic-ref",
                "--quiet",
                "refs/remotes/origin/HEAD",
            ): CommandResult(stdout="refs/remotes/origin/main\n"),
            ("git", "-C", "/repo", "status", "--porcelain"): CommandResult(),
            (
                "git",
                "-C",
                "/repo",
                "symbolic-ref",
                "--quiet",
                "--short",
                "HEAD",
            ): CommandResult(stdout="main\n"),
            (
                "git",
                "-C",
                "/repo",
                "for-each-ref",
                "--format=%(refname:short)%00%(objectname)",
                "refs/heads",
            ): CommandResult(stdout="main\x00base\n"),
        }
    )
    stdout = StringIO()
    stderr = StringIO()

    assert (
        main(
            argv=["--repo", "/repo", "--repo-name", "runtime", "--no-prs"],
            environ={},
            stdout=stdout,
            stderr=stderr,
            runner=runner.run,
        )
        == 0
    )
    assert stdout.getvalue() == "[]\n"

    assert (
        main(
            argv=["--repo", "/repo", "--stale-days", "-1"],
            environ={},
            stdout=StringIO(),
            stderr=stderr,
            runner=runner.run,
        )
        == 2
    )
    assert "--stale-days must be non-negative" in stderr.getvalue()


_PR_FIELDS = "number,headRefName,updatedAt,title,url"


class _FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult]) -> None:
        self._responses = responses

    def run(self, *, argv: list[str], cwd: Path) -> CommandResult:
        _ = cwd
        return self._responses.get(tuple(argv), CommandResult(returncode=1, stderr="unexpected"))
