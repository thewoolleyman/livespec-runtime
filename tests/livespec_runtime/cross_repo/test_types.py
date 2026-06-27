"""Tests for `livespec_runtime.cross_repo.types`.

Verifies the typed `DependsOnEntry` union (4 variants discriminated on
`kind`), the `CrossRepoManifest` / `CrossRepoTarget` dataclasses, the
`RefStatus` enum, and the dict-to-typed parser helpers.

Schema reference: livespec/SPECIFICATION/contracts.md v072.
"""

from pathlib import Path

import pytest

from livespec_runtime.cross_repo.errors import CrossRepoSchemaError
from livespec_runtime.cross_repo.types import (
    BranchDependency,
    CrossRepoManifest,
    CrossRepoTarget,
    DependsOnEntry,
    LocalDependency,
    PullRequestDependency,
    RefStatus,
    SiblingWorkItemDependency,
    parse_cross_repo_manifest,
    parse_depends_on_entry,
)

__all__: list[str] = []


def test_ref_status_values() -> None:
    assert RefStatus.OPEN.value == "open"
    assert RefStatus.CLOSED.value == "closed"
    assert RefStatus.UNKNOWN.value == "unknown"


def test_ref_status_membership() -> None:
    assert {member.value for member in RefStatus} == {"open", "closed", "unknown"}


def test_local_dependency_construction() -> None:
    entry = LocalDependency(work_item_id="li-abc123")
    assert entry.kind == "local"
    assert entry.work_item_id == "li-abc123"


def test_sibling_work_item_dependency_construction() -> None:
    entry = SiblingWorkItemDependency(repo="impl-git-jsonl", work_item_id="li-xyz789")
    assert entry.kind == "sibling_work_item"
    assert entry.repo == "impl-git-jsonl"
    assert entry.work_item_id == "li-xyz789"


def test_pull_request_dependency_construction() -> None:
    entry = PullRequestDependency(repo="impl-git-jsonl", number=42)
    assert entry.kind == "pull_request"
    assert entry.repo == "impl-git-jsonl"
    assert entry.number == 42


def test_branch_dependency_construction() -> None:
    entry = BranchDependency(repo="dev-tooling", name="feat/foo")
    assert entry.kind == "branch"
    assert entry.repo == "dev-tooling"
    assert entry.name == "feat/foo"


def test_dependency_dataclasses_are_frozen() -> None:
    entry = LocalDependency(work_item_id="li-abc")
    with pytest.raises(AttributeError):
        entry.work_item_id = "other"  # type: ignore[misc]


def test_cross_repo_target_construction_minimal() -> None:
    target = CrossRepoTarget(github_url="https://github.com/owner/repo")
    assert target.github_url == "https://github.com/owner/repo"
    assert target.local_clone is None
    assert target.default_branch == "master"


def test_cross_repo_target_construction_full() -> None:
    target = CrossRepoTarget(
        github_url="https://github.com/owner/repo",
        local_clone=Path("/tmp/sibling"),
        default_branch="main",
    )
    assert target.local_clone == Path("/tmp/sibling")
    assert target.default_branch == "main"


def test_cross_repo_manifest_construction_empty() -> None:
    manifest = CrossRepoManifest(targets={})
    assert manifest.targets == {}


def test_cross_repo_manifest_construction_with_targets() -> None:
    manifest = CrossRepoManifest(
        targets={
            "impl": CrossRepoTarget(github_url="https://github.com/owner/impl"),
            "runtime": CrossRepoTarget(github_url="https://github.com/owner/runtime"),
        },
    )
    assert set(manifest.targets) == {"impl", "runtime"}


def test_parse_depends_on_entry_local() -> None:
    entry = parse_depends_on_entry(parsed={"kind": "local", "work_item_id": "li-abc"})
    assert isinstance(entry, LocalDependency)
    assert entry.work_item_id == "li-abc"


def test_parse_depends_on_entry_sibling_work_item() -> None:
    entry = parse_depends_on_entry(
        parsed={"kind": "sibling_work_item", "repo": "impl", "work_item_id": "li-xyz"},
    )
    assert isinstance(entry, SiblingWorkItemDependency)
    assert entry.repo == "impl"
    assert entry.work_item_id == "li-xyz"


def test_parse_depends_on_entry_pull_request() -> None:
    entry = parse_depends_on_entry(
        parsed={"kind": "pull_request", "repo": "impl", "number": 42},
    )
    assert isinstance(entry, PullRequestDependency)
    assert entry.repo == "impl"
    assert entry.number == 42


def test_parse_depends_on_entry_branch() -> None:
    entry = parse_depends_on_entry(
        parsed={"kind": "branch", "repo": "impl", "name": "feat/foo"},
    )
    assert isinstance(entry, BranchDependency)
    assert entry.repo == "impl"
    assert entry.name == "feat/foo"


def test_parse_depends_on_entry_missing_kind_raises() -> None:
    with pytest.raises(CrossRepoSchemaError, match="missing required field 'kind'"):
        _ = parse_depends_on_entry(parsed={"work_item_id": "li-abc"})


def test_parse_depends_on_entry_unknown_kind_raises() -> None:
    with pytest.raises(CrossRepoSchemaError, match="unknown kind"):
        _ = parse_depends_on_entry(parsed={"kind": "garbage", "work_item_id": "li-abc"})


def test_parse_depends_on_entry_local_missing_required_field_raises() -> None:
    with pytest.raises(CrossRepoSchemaError, match="missing required field 'work_item_id'"):
        _ = parse_depends_on_entry(parsed={"kind": "local"})


def test_parse_depends_on_entry_sibling_work_item_missing_required_field_raises() -> None:
    with pytest.raises(CrossRepoSchemaError, match="missing required field 'repo'"):
        _ = parse_depends_on_entry(
            parsed={"kind": "sibling_work_item", "work_item_id": "li-xyz"},
        )


def test_parse_depends_on_entry_pull_request_missing_required_field_raises() -> None:
    with pytest.raises(CrossRepoSchemaError, match="missing required field 'number'"):
        _ = parse_depends_on_entry(parsed={"kind": "pull_request", "repo": "impl"})


def test_parse_depends_on_entry_branch_missing_required_field_raises() -> None:
    with pytest.raises(CrossRepoSchemaError, match="missing required field 'name'"):
        _ = parse_depends_on_entry(parsed={"kind": "branch", "repo": "impl"})


def test_parse_cross_repo_manifest_empty() -> None:
    manifest = parse_cross_repo_manifest(parsed={})
    assert manifest.targets == {}


def test_parse_cross_repo_manifest_minimal_target() -> None:
    manifest = parse_cross_repo_manifest(
        parsed={"impl": {"github_url": "https://github.com/owner/impl"}},
    )
    assert manifest.targets["impl"].github_url == "https://github.com/owner/impl"
    assert manifest.targets["impl"].local_clone is None
    assert manifest.targets["impl"].default_branch == "master"


def test_parse_cross_repo_manifest_full_target() -> None:
    manifest = parse_cross_repo_manifest(
        parsed={
            "impl": {
                "github_url": "https://github.com/owner/impl",
                "local_clone": "/tmp/impl",
                "default_branch": "main",
            },
        },
    )
    target = manifest.targets["impl"]
    assert target.local_clone == Path("/tmp/impl")
    assert target.default_branch == "main"


def test_parse_cross_repo_manifest_target_missing_github_url_raises() -> None:
    with pytest.raises(CrossRepoSchemaError, match="missing required field 'github_url'"):
        _ = parse_cross_repo_manifest(parsed={"impl": {"local_clone": "/tmp/impl"}})


def test_dependency_union_type_alias_resolves() -> None:
    entries: list[DependsOnEntry] = [
        LocalDependency(work_item_id="li-a"),
        SiblingWorkItemDependency(repo="r", work_item_id="li-b"),
        PullRequestDependency(repo="r", number=1),
        BranchDependency(repo="r", name="feat/x"),
    ]
    assert len(entries) == 4
