"""The stale-worktree gate must see the worktrees that actually accumulate.

Measured in `livespec-console-beads-fabro`: 14 abandoned janitor
worktrees, the oldest ten days old, and `needs-attention` flagged NONE of
them. Every one carried machine-generated untracked content — a vendored
`.livespec-core/` checkout the janitor clones inside its own checkout,
plus a self-provisioned `.venv` — and the gate read any `git status
--porcelain` output at all as "leave it alone". The dirt that makes a
worktree hard to remove was exactly the dirt that made it invisible, so
the gate could only ever surface the population a plain `git worktree
remove` would already have accepted.

The two-sided control from that measurement is reproduced here as a
PAIR — a clean detached worktree that fires, and the SAME worktree with
one untracked entry added, which must also fire. The only variable
between the two is the untracked file, so a later change cannot
re-blind the gate without failing one of them.

Authored work is the safety property the old test was protecting by
accident, and it is pinned separately: TRACKED modifications still
suppress the finding outright, because someone's uncommitted work must
never be proposed for removal.
"""

from pathlib import Path

from returns.io import IOResult, IOSuccess

from livespec_runtime.attention_item import AttentionItem
from livespec_runtime.hygiene_scan import CommandResult, CommandUnavailable, scan_hygiene

__all__: list[str] = []

_LISTING = (
    "worktree /repo\n"
    "HEAD base\n"
    "branch refs/heads/master\n"
    "\n"
    "worktree /repo-detached\n"
    "HEAD detachedsha\n"
    "detached\n"
)
_STATUS = ("git", "-C", "/repo-detached", "status", "--porcelain")
_ANCESTOR = ("git", "-C", "/repo", "merge-base", "--is-ancestor", "detachedsha", "origin/master")
_CHERRY = ("git", "-C", "/repo", "cherry", "origin/master", "detachedsha")
_REMOVE = "git -C /repo worktree remove /repo-detached"
_FORCED_REMOVE = "git -C /repo worktree remove --force /repo-detached"
_VENDORED_DIRT = "?? .livespec-core/\n?? .venv/\n"


def test_scan_hygiene_flags_a_clean_detached_worktree_merged_into_the_base_ref() -> None:
    """Side 1 of the control: the behaviour measured working today."""
    items = _scan(
        extra={
            _STATUS: CommandResult(),
            _ANCESTOR: CommandResult(),
        }
    )

    assert [item.id for item in items] == ["hygiene:stale-worktree:/repo-detached"]
    assert items[0].summary == (
        "Remove clean worktree /repo-detached; its HEAD is merged into origin/master."
    )
    assert items[0].handoff.command == _REMOVE


def test_scan_hygiene_flags_a_worktree_whose_only_dirt_is_untracked() -> None:
    """Side 2 of the control: the SAME worktree, one untracked entry added."""
    items = _scan(
        extra={
            _STATUS: CommandResult(stdout=_VENDORED_DIRT),
            _ANCESTOR: CommandResult(),
        }
    )

    assert [item.id for item in items] == ["hygiene:stale-worktree:/repo-detached"]
    assert items[0].summary == (
        "Remove worktree /repo-detached; its HEAD is merged into origin/master. "
        "Untracked content blocks a plain removal, so --force is required: "
        ".livespec-core/, .venv/."
    )
    assert items[0].handoff.command == _FORCED_REMOVE


def test_scan_hygiene_names_only_the_first_untracked_entries_and_counts_the_rest() -> None:
    items = _scan(
        extra={
            _STATUS: CommandResult(stdout="?? a\n?? b\n?? c\n?? d\n?? e\n"),
            _ANCESTOR: CommandResult(),
        }
    )

    assert items[0].summary.endswith(
        "Untracked content blocks a plain removal, so --force is required: a, b, c (+2 more)."
    )


def test_scan_hygiene_flags_a_worktree_whose_commits_landed_by_patch_equivalence() -> None:
    """Nine of fourteen strays had MERGED PRs yet read unmerged by ancestry.

    A rebase or squash merge rewrites the SHAs, so `merge-base
    --is-ancestor` answers "no" about work that demonstrably landed.
    `git cherry` compares patch ids instead, and an all-`-` reading is
    the durable signal that survives the rewrite.
    """
    items = _scan(
        extra={
            _STATUS: CommandResult(stdout=_VENDORED_DIRT),
            _ANCESTOR: CommandResult(returncode=1),
            _CHERRY: CommandResult(stdout="- aaaa1111\n- bbbb2222\n"),
        }
    )

    assert [item.id for item in items] == ["hygiene:stale-worktree:/repo-detached"]
    assert items[0].summary == (
        "Remove worktree /repo-detached; every commit on its HEAD is already in "
        "origin/master by patch equivalence (git cherry), so a rebase or squash merge "
        "landed it. Untracked content blocks a plain removal, so --force is required: "
        ".livespec-core/, .venv/."
    )
    assert items[0].handoff.command == _FORCED_REMOVE


def test_scan_hygiene_leaves_a_worktree_carrying_tracked_modifications_alone() -> None:
    """Negative control: authored work is never proposed for removal."""
    assert (
        _scan(
            extra={
                _STATUS: CommandResult(stdout=" M livespec_runtime/hygiene_scan.py\n?? .venv/\n"),
                _ANCESTOR: CommandResult(),
            }
        )
        == []
    )


def test_scan_hygiene_leaves_an_unlanded_worktree_alone() -> None:
    """Negative control: a live factory run is never proposed for removal."""
    assert (
        _scan(
            extra={
                _STATUS: CommandResult(stdout=_VENDORED_DIRT),
                _ANCESTOR: CommandResult(returncode=1),
                _CHERRY: CommandResult(stdout="+ cccc3333\n- dddd4444\n"),
            }
        )
        == []
    )


def test_scan_hygiene_leaves_a_worktree_with_an_unreadable_status_alone() -> None:
    """A `git status` that did not ANSWER concludes nothing about the worktree."""
    assert (
        _scan(
            extra={
                _STATUS: CommandResult(returncode=128, stderr="fatal: not a git repository\n"),
                _ANCESTOR: CommandResult(),
            }
        )
        == []
    )


def _scan(*, extra: dict[tuple[str, ...], CommandResult]) -> list[AttentionItem]:
    """Run `scan_hygiene` over one secondary worktree, PR reads off."""
    runner = _FakeRunner(
        {
            ("git", "-C", "/repo", "worktree", "list", "--porcelain"): CommandResult(
                stdout=_LISTING
            ),
            ("git", "-C", "/repo", "rev-parse", "--show-toplevel"): CommandResult(
                stdout="/elsewhere\n"
            ),
            ("git", "-C", "/repo", "symbolic-ref", "--quiet", "refs/remotes/origin/HEAD"): (
                CommandResult(stdout="refs/remotes/origin/master\n")
            ),
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
            ): CommandResult(stdout="master\x00base\n"),
            **extra,
        }
    )
    return scan_hygiene(
        repo_path=Path("/repo"),
        repo_name="runtime",
        include_prs=False,
        runner=runner.run,
    )


class _FakeRunner:
    def __init__(self, responses: dict[tuple[str, ...], CommandResult]) -> None:
        self._responses = responses

    def run(self, *, argv: list[str], cwd: Path) -> IOResult[CommandResult, CommandUnavailable]:
        _ = cwd
        return IOSuccess(
            self._responses.get(tuple(argv), CommandResult(returncode=1, stderr="unexpected"))
        )
