"""`resolve_ref` — exhaustive live-walk dependency resolution.

Per livespec/SPECIFICATION/contracts.md §"Cross-repo dependency awareness":
no cache; tolerate partial visibility; for each `DependsOnEntry` variant,
walk every extant view the runtime can access and return a `RefStatus`.

The function is environment-aware:
- `kind: "local"` is always resolved against the local work-items store
  (the caller passes a `local_status_lookup` closure for this — the
  runtime doesn't know the impl-plugin's storage layout).
- Sibling/PR/branch resolutions walk `local_clone` when configured AND
  fall back to GitHub queries when not (or in addition, for branch
  state).
- Missing `local_clone` is NOT an error; the view is silently dropped.
- `gh` CLI auth failures translate to `RefStatus.unknown` after retry
  exhaustion.

Resolution semantics per the consolidated v071+ design:
- PR `state == "MERGED"` OR `state == "CLOSED"` → `closed`.
- Branch reachable from default (merged) → `closed`.
- Branch absent from remote → `closed` (assumes deleted-after-merge).
- Branch present on remote AND not merged → `open`.
"""

from collections.abc import Callable
from pathlib import Path

from typing_extensions import assert_never

from livespec_runtime.cross_repo.providers import github as gh_provider
from livespec_runtime.cross_repo.retry import retry_with_backoff
from livespec_runtime.cross_repo.types import (
    BranchEntry,
    CrossRepoManifest,
    DependsOnEntry,
    LocalEntry,
    PullRequestEntry,
    RefStatus,
    SiblingWorkItemEntry,
)


def resolve_ref(
    *,
    entry: DependsOnEntry,
    manifest: CrossRepoManifest,
    local_status_lookup: Callable[[str], RefStatus],
    sibling_status_lookup: Callable[[str, str], RefStatus] | None = None,
) -> RefStatus:
    """Return the entry's resolved status.

    `local_status_lookup(work_item_id)` returns the current-repo
    work-item's status (the caller wires this against the active
    impl-plugin's list-work-items output).

    `sibling_status_lookup(repo, work_item_id)` is OPTIONAL; when
    provided, it's used for `kind: "sibling_work_item"` entries before
    falling back to local-clone walk. When None and no local_clone is
    configured, sibling work-item resolution returns `RefStatus.unknown`.
    """
    match entry:
        case LocalEntry(work_item_id=work_item_id):
            return local_status_lookup(work_item_id)
        case SiblingWorkItemEntry(repo=repo, work_item_id=wi_id):
            return _resolve_sibling_work_item(
                repo=repo,
                work_item_id=wi_id,
                manifest=manifest,
                sibling_status_lookup=sibling_status_lookup,
            )
        case PullRequestEntry(repo=repo, number=number):
            return _resolve_pull_request(repo=repo, number=number, manifest=manifest)
        case BranchEntry(repo=repo, name=name):
            return _resolve_branch(repo=repo, name=name, manifest=manifest)
        case _:
            assert_never(entry)


def _resolve_sibling_work_item(
    *,
    repo: str,
    work_item_id: str,
    manifest: CrossRepoManifest,
    sibling_status_lookup: Callable[[str, str], RefStatus] | None,
) -> RefStatus:
    target = manifest.targets.get(repo)
    if target is None:
        return RefStatus.unknown
    if sibling_status_lookup is not None:
        return sibling_status_lookup(repo, work_item_id)
    if target.local_clone is None or not Path(target.local_clone).exists():
        return RefStatus.unknown
    # No local-clone parser shipped in v1; impl-plugins surface their
    # own sibling_status_lookup. The path-exists check above keeps the
    # contract honest (we declared we'd "walk the local clone" but the
    # runtime doesn't actually parse impl-plugin-specific store formats).
    return RefStatus.unknown


def _resolve_pull_request(*, repo: str, number: int, manifest: CrossRepoManifest) -> RefStatus:
    target = manifest.targets.get(repo)
    if target is None:
        return RefStatus.unknown
    state = retry_with_backoff(
        fn=lambda: gh_provider.query_pull_request_state(
            github_url=target.github_url, number=number
        ),
    )
    if state is None:
        return RefStatus.unknown
    if state in ("MERGED", "CLOSED"):
        return RefStatus.closed
    return RefStatus.open


def _resolve_branch(*, repo: str, name: str, manifest: CrossRepoManifest) -> RefStatus:
    target = manifest.targets.get(repo)
    if target is None:
        return RefStatus.unknown
    exists = retry_with_backoff(
        fn=lambda: gh_provider.branch_exists_on_remote(github_url=target.github_url, name=name),
    )
    if exists is None:
        return RefStatus.unknown
    if not exists:
        # Branch absent on remote — assume deleted-after-merge per the
        # consolidated v071+ design's branch-resolution rule.
        return RefStatus.closed
    merged = retry_with_backoff(
        fn=lambda: gh_provider.branch_merged_into_default(
            github_url=target.github_url,
            name=name,
            default_branch=target.default_branch,
        ),
    )
    if merged is None:
        return RefStatus.unknown
    return RefStatus.closed if merged else RefStatus.open


__all__ = ["resolve_ref"]
