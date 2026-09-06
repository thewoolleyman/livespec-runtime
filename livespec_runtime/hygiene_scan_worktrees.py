"""Stale worktree detection for hygiene scanning."""

from __future__ import annotations

from pathlib import Path

from returns.io import IOFailure, IOResult, IOSuccess
from returns.unsafe import unsafe_perform_io

from livespec_runtime.hygiene_scan_context import (
    DEFAULT_STALE_DAYS,
    build_context,
    git,
    quote_path,
    run_command,
    worktrees,
)
from livespec_runtime.hygiene_scan_types import (
    CommandRunner,
    CommandUnavailable,
    GitWorktree,
    ScanContext,
)
from livespec_runtime.hygiene_scan_worktree_merge import (
    branch_was_rebase_merged,
    head_is_merged,
)
from livespec_runtime.needs_attention import HygieneScanFinding

__all__: list[str] = [
    "detect_stale_worktrees",
    "stale_worktree_findings",
]


def stale_worktree_findings(
    *, context: ScanContext
) -> IOResult[list[HygieneScanFinding], CommandUnavailable]:
    """Detect worktrees the reaper can prune/remove without force."""
    listed = worktrees(context=context)
    if isinstance(listed, IOFailure):
        return listed
    findings: list[HygieneScanFinding] = []
    for worktree in unsafe_perform_io(listed.unwrap()):
        if worktree.path in (context.primary_path, context.current_path):
            continue
        probed = stale_worktree_finding(context=context, worktree=worktree)
        if isinstance(probed, IOFailure):
            return probed
        finding = unsafe_perform_io(probed.unwrap())
        if finding is not None:
            findings.append(finding)
    return IOSuccess(findings)


def detect_stale_worktrees(
    *,
    repo_path: Path,
    runner: CommandRunner | None = None,
) -> list[GitWorktree]:
    """Return the stale worktree CANDIDATE set for `repo_path`.

    ⛔ THE RAILWAY TERMINATES HERE, AND THE SIGNATURE IS HELD ON PURPOSE.
    This is one of exactly two functions in this subsystem consumed ACROSS
    REPOS by source copy — `livespec` and `livespec-overseer` call it from
    their `dev-tooling/reap_stale_worktrees.py` and index the list it
    returns. Widening the return type to `IOResult` is a coordinated
    multi-repo change, not a side effect of putting the leaf on the
    railway, so it is filed rather than taken here.

    `unwrap()` is the deliberate terminal: an unspawnable command raises
    out of this call, which is EXACTLY what it did before the railway
    existed (an uncaught `FileNotFoundError` from `subprocess.run`). This
    boundary is therefore behaviour-preserving, not a swallow — nothing
    is discarded and no failure is converted into an empty list.
    """
    context = unsafe_perform_io(
        build_context(
            repo_path=repo_path,
            repo_name=None,
            now=None,
            stale_days=DEFAULT_STALE_DAYS,
            runner=runner or run_command,
        ).unwrap()
    )
    candidates: list[GitWorktree] = []
    for worktree in unsafe_perform_io(worktrees(context=context).unwrap()):
        if worktree.path == context.primary_path:
            continue
        finding = unsafe_perform_io(
            stale_worktree_finding(context=context, worktree=worktree).unwrap()
        )
        if finding is not None:
            candidates.append(worktree)
    return candidates


def stale_worktree_finding(
    *,
    context: ScanContext,
    worktree: GitWorktree,
) -> IOResult[HygieneScanFinding | None, CommandUnavailable]:
    label = str(worktree.path)
    if is_default_branch_worktree(context=context, worktree=worktree):
        return IOSuccess(None)
    if worktree.prunable_reason is not None:
        return IOSuccess(prunable_worktree_finding(context=context, worktree=worktree, label=label))
    clean = worktree_is_clean(worktree=worktree, runner=context.runner)
    if isinstance(clean, IOFailure):
        return clean
    if not unsafe_perform_io(clean.unwrap()):
        return IOSuccess(None)
    return landed_worktree_finding(context=context, worktree=worktree, label=label)


def prunable_worktree_finding(
    *, context: ScanContext, worktree: GitWorktree, label: str
) -> HygieneScanFinding:
    """The finding for a worktree whose metadata git itself reports prunable."""
    return HygieneScanFinding(
        type="stale-worktree",
        resource=label,
        path=label,
        summary=f"Prune stale worktree metadata for {label} ({worktree.prunable_reason}).",
        command=f"git -C {quote_path(path=context.primary_path)} worktree prune -v",
    )


def landed_worktree_finding(
    *, context: ScanContext, worktree: GitWorktree, label: str
) -> IOResult[HygieneScanFinding | None, CommandUnavailable]:
    """The finding for a CLEAN worktree whose work has already landed, if any.

    Two ways work lands in a rebase-merging fleet: the HEAD is an ancestor
    of the base ref, or the branch was pushed and its origin head is now
    gone. Split out of `stale_worktree_finding` so neither carries the
    other's branches.
    """
    remove_command = (
        f"git -C {quote_path(path=context.primary_path)} "
        f"worktree remove {quote_path(path=worktree.path)}"
    )
    merged = head_is_merged(context=context, head=worktree.head)
    if isinstance(merged, IOFailure):
        return merged
    if unsafe_perform_io(merged.unwrap()):
        return IOSuccess(
            HygieneScanFinding(
                type="stale-worktree",
                resource=label,
                path=label,
                summary=(
                    f"Remove clean worktree {label}; its HEAD is merged into {context.base_ref}."
                ),
                command=remove_command,
            )
        )
    rebase_merged = branch_was_rebase_merged(context=context, worktree=worktree)
    if isinstance(rebase_merged, IOFailure):
        return rebase_merged
    if unsafe_perform_io(rebase_merged.unwrap()):
        return IOSuccess(
            HygieneScanFinding(
                type="stale-worktree",
                resource=label,
                path=label,
                summary=(
                    f"Remove clean worktree {label}; its branch {worktree.branch} was pushed and "
                    f"its origin branch is gone (rebase-merged, so its HEAD is not an ancestor of "
                    f"{context.base_ref})."
                ),
                command=remove_command,
            )
        )
    return IOSuccess(None)


def is_default_branch_worktree(*, context: ScanContext, worktree: GitWorktree) -> bool:
    """Return True if `worktree` is checked out on the repo's default branch."""
    return worktree.branch is not None and worktree.branch == context.default_branch


def worktree_is_clean(
    *, worktree: GitWorktree, runner: CommandRunner
) -> IOResult[bool, CommandUnavailable]:
    return git(repo_path=worktree.path, argv=["status", "--porcelain"], runner=runner).map(
        lambda result: result.returncode == 0 and result.stdout == ""
    )
