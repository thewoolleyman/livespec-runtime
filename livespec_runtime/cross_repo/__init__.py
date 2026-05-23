"""livespec_runtime.cross_repo — cross-repo work-item dependency resolution.

Public API per livespec/SPECIFICATION/contracts.md
§"Cross-repo dependency awareness" (landed by work-item li-e7h6ki under
parent epic li-6d2wpj):

- `RefStatus` — `open` / `closed` / `unknown`.
- `DependsOnEntry` — union over `LocalEntry`, `SiblingWorkItemEntry`,
  `PullRequestEntry`, `BranchEntry`.
- `CrossRepoManifest` / `CrossRepoTarget` — in-memory shape of the
  `.livespec.jsonc` `cross_repo_targets` block.
- `resolve_ref(entry, manifest, local_status_lookup, ...)` — exhaustive
  live-walk resolution returning a `RefStatus`.

Implementation lands at v0.2.0 per work-item li-aclzfe; v0.1.0 shipped
the empty skeleton.
"""

from livespec_runtime.cross_repo.resolve import resolve_ref
from livespec_runtime.cross_repo.types import (
    BranchEntry,
    CrossRepoManifest,
    CrossRepoTarget,
    DependsOnEntry,
    LocalEntry,
    PullRequestEntry,
    RefStatus,
    SiblingWorkItemEntry,
)

__all__ = [
    "BranchEntry",
    "CrossRepoManifest",
    "CrossRepoTarget",
    "DependsOnEntry",
    "LocalEntry",
    "PullRequestEntry",
    "RefStatus",
    "SiblingWorkItemEntry",
    "resolve_ref",
]
