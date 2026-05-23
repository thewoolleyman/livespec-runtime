"""Tests for the DependsOnEntry union, CrossRepoManifest, RefStatus."""

import pytest

from livespec_runtime.cross_repo.types import (
    BranchEntry,
    CrossRepoManifest,
    CrossRepoTarget,
    LocalEntry,
    PullRequestEntry,
    RefStatus,
    SiblingWorkItemEntry,
)


def test_ref_status_enum_members() -> None:
    assert RefStatus.open.value == "open"
    assert RefStatus.closed.value == "closed"
    assert RefStatus.unknown.value == "unknown"


def test_local_entry_carries_work_item_id() -> None:
    entry = LocalEntry(kind="local", work_item_id="li-abc123")
    assert entry.kind == "local"
    assert entry.work_item_id == "li-abc123"


def test_sibling_work_item_entry_carries_repo_and_id() -> None:
    entry = SiblingWorkItemEntry(
        kind="sibling_work_item", repo="livespec-core", work_item_id="li-xyz789"
    )
    assert entry.kind == "sibling_work_item"
    assert entry.repo == "livespec-core"
    assert entry.work_item_id == "li-xyz789"


def test_pull_request_entry_carries_repo_and_number() -> None:
    entry = PullRequestEntry(kind="pull_request", repo="livespec-core", number=123)
    assert entry.kind == "pull_request"
    assert entry.repo == "livespec-core"
    assert entry.number == 123


def test_branch_entry_carries_repo_and_name() -> None:
    entry = BranchEntry(kind="branch", repo="livespec-core", name="feat/foo")
    assert entry.kind == "branch"
    assert entry.repo == "livespec-core"
    assert entry.name == "feat/foo"


def test_cross_repo_target_defaults() -> None:
    target = CrossRepoTarget(github_url="https://github.com/thewoolleyman/livespec")
    assert target.local_clone is None
    assert target.default_branch == "master"


def test_cross_repo_target_with_local_clone() -> None:
    target = CrossRepoTarget(
        github_url="https://github.com/thewoolleyman/livespec",
        local_clone="/data/projects/livespec",
        default_branch="main",
    )
    assert target.local_clone == "/data/projects/livespec"
    assert target.default_branch == "main"


def test_cross_repo_manifest_holds_named_targets() -> None:
    manifest = CrossRepoManifest(
        targets={
            "livespec": CrossRepoTarget(github_url="https://github.com/thewoolleyman/livespec"),
            "livespec-impl-plaintext": CrossRepoTarget(
                github_url="https://github.com/thewoolleyman/livespec-impl-plaintext"
            ),
        }
    )
    assert "livespec" in manifest.targets
    assert manifest.targets["livespec-impl-plaintext"].default_branch == "master"


def test_dataclass_frozen() -> None:
    from dataclasses import FrozenInstanceError

    entry = LocalEntry(kind="local", work_item_id="li-a")
    with pytest.raises(FrozenInstanceError):
        entry.work_item_id = "li-b"  # type: ignore[misc]
