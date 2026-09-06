"""Merged-ness readings for hygiene scanning.

"Has this work already landed?" is a question about the BASE REF, not
about any one worktree, and it is asked from two places — the stale
worktree gate and the stale branch gate. It lives here so neither caller
carries the other's reasons, and so the several ways a rebase-merging
fleet can land work stay side by side where they can be compared.
"""

from __future__ import annotations

from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.hygiene_scan_context import git
from livespec_runtime.hygiene_scan_types import (
    CommandUnavailable,
    GitWorktree,
    ScanContext,
)

__all__: list[str] = [
    "branch_was_rebase_merged",
    "head_is_merged",
]

# Named rather than written as bare `True`/`False` literals at the lift
# sites: `IOSuccess(...)` takes its value positionally, and a positional
# boolean says nothing at the call site about which answer it is.
_DETACHED_WORKTREE_IS_NOT_MERGED = False
_DETACHED_WORKTREE_HAS_NO_REBASE_SIGNAL = False
_UNPUSHED_BRANCH_WAS_NOT_REBASE_MERGED = False
_UPSTREAM_CONFIG_IS_EVIDENCE_OF_A_PUSH = True


def branch_was_rebase_merged(
    *, context: ScanContext, worktree: GitWorktree
) -> IOResult[bool, CommandUnavailable]:
    """Return True if `worktree`'s branch shows the rebase-merge orphan signal."""
    branch = worktree.branch
    if branch is None:
        return IOSuccess(_DETACHED_WORKTREE_HAS_NO_REBASE_SIGNAL)
    pushed = branch_was_pushed(context=context, branch=branch)
    if isinstance(pushed, IOFailure):
        return pushed
    if not unsafe_perform_io(pushed.unwrap()):
        return IOSuccess(_UNPUSHED_BRANCH_WAS_NOT_REBASE_MERGED)
    return branch_is_done(context=context, branch=branch)


def branch_was_pushed(*, context: ScanContext, branch: str) -> IOResult[bool, CommandUnavailable]:
    """Return True if `branch` carries local evidence of ever having been pushed."""
    upstream = git(
        repo_path=context.primary_path,
        argv=["config", "--get", f"branch.{branch}.merge"],
        runner=context.runner,
    )
    if isinstance(upstream, IOFailure):
        return upstream
    configured = unsafe_perform_io(upstream.unwrap())
    if configured.returncode == 0 and configured.stdout.strip() != "":
        return IOSuccess(_UPSTREAM_CONFIG_IS_EVIDENCE_OF_A_PUSH)
    return git(
        repo_path=context.primary_path,
        argv=["rev-parse", "--verify", "--quiet", f"refs/remotes/origin/{branch}"],
        runner=context.runner,
    ).map(lambda tracking: tracking.returncode == 0)


def branch_is_done(*, context: ScanContext, branch: str) -> IOResult[bool, CommandUnavailable]:
    """Return True if `branch`'s remote head is absent on origin."""
    return git(
        repo_path=context.primary_path,
        argv=["ls-remote", "--heads", "origin", branch],
        runner=context.runner,
    ).map(lambda result: result.returncode == 0 and result.stdout.strip() == "")


def head_is_merged(*, context: ScanContext, head: str | None) -> IOResult[bool, CommandUnavailable]:
    if head is None:
        return IOSuccess(_DETACHED_WORKTREE_IS_NOT_MERGED)
    return git(
        repo_path=context.primary_path,
        argv=["merge-base", "--is-ancestor", head, context.base_ref],
        runner=context.runner,
    ).map(lambda result: result.returncode == 0)
