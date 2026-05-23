"""Typed `DependsOnEntry` union, `CrossRepoManifest`, and `RefStatus` enum.

Per livespec/SPECIFICATION/contracts.md §"Cross-repo dependency awareness"
(landed by work-item li-e7h6ki under parent epic li-6d2wpj):

- `DependsOnEntry` is a discriminated union over `kind`:
    `local` | `sibling_work_item` | `pull_request` | `branch`.
- `CrossRepoManifest` is the in-memory shape of the `cross_repo_targets`
  block from `.livespec.jsonc`.
- `RefStatus` is the open / closed / unknown enum the runtime returns
  from `resolve_ref`.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Literal


class RefStatus(Enum):
    """Resolution status returned by `resolve_ref`.

    `open` — the dependency is in-flight (work-item open, PR open, branch
        not merged).
    `closed` — the dependency is resolved (work-item closed, PR
        merged-or-closed, branch merged into default).
    `unknown` — the runtime could not derive a status (missing local
        clone AND GitHub query failed, or retry exhausted).
    """

    open = "open"
    closed = "closed"
    unknown = "unknown"


@dataclass(frozen=True, kw_only=True)
class LocalEntry:
    """`kind: "local"` — same-repo work-item dependency."""

    kind: Literal["local"]
    work_item_id: str


@dataclass(frozen=True, kw_only=True)
class SiblingWorkItemEntry:
    """`kind: "sibling_work_item"` — work-item in a configured sibling repo."""

    kind: Literal["sibling_work_item"]
    repo: str
    work_item_id: str


@dataclass(frozen=True, kw_only=True)
class PullRequestEntry:
    """`kind: "pull_request"` — specific GitHub pull request."""

    kind: Literal["pull_request"]
    repo: str
    number: int


@dataclass(frozen=True, kw_only=True)
class BranchEntry:
    """`kind: "branch"` — specific GitHub branch."""

    kind: Literal["branch"]
    repo: str
    name: str


DependsOnEntry = LocalEntry | SiblingWorkItemEntry | PullRequestEntry | BranchEntry


@dataclass(frozen=True, kw_only=True)
class CrossRepoTarget:
    """One entry in `cross_repo_targets`.

    `github_url` is the canonical `https://github.com/<owner>/<name>` form
    (no trailing `.git`). `local_clone` is OPTIONAL (None = CI / no local
    clone available; runtime degrades to GitHub-only queries).
    `default_branch` defaults to `"master"`.
    """

    github_url: str
    local_clone: str | None = None
    default_branch: str = "master"


@dataclass(frozen=True, kw_only=True)
class CrossRepoManifest:
    """In-memory shape of `.livespec.jsonc`'s `cross_repo_targets` block.

    Keys are the repo slugs used as the `repo` field in
    `DependsOnEntry` variants; values are the per-target config.
    """

    targets: dict[str, CrossRepoTarget]


__all__ = [
    "BranchEntry",
    "CrossRepoManifest",
    "CrossRepoTarget",
    "DependsOnEntry",
    "LocalEntry",
    "PullRequestEntry",
    "RefStatus",
    "SiblingWorkItemEntry",
]
