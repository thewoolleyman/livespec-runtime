"""Tests for resolve_ref across all four DependsOnEntry variants."""

from pathlib import Path
from unittest.mock import patch

from livespec_runtime.cross_repo.resolve import resolve_ref
from livespec_runtime.cross_repo.types import (
    BranchEntry,
    CrossRepoManifest,
    CrossRepoTarget,
    LocalEntry,
    PullRequestEntry,
    RefStatus,
    SiblingWorkItemEntry,
)

_MANIFEST = CrossRepoManifest(
    targets={
        "livespec": CrossRepoTarget(github_url="https://github.com/thewoolleyman/livespec"),
        "with-clone": CrossRepoTarget(
            github_url="https://github.com/thewoolleyman/with-clone",
            local_clone="/data/projects/with-clone",
        ),
    }
)


# ---------- LocalEntry ----------


def test_local_entry_delegates_to_lookup() -> None:
    entry = LocalEntry(kind="local", work_item_id="li-abc")
    lookup_calls: list[str] = []

    def lookup(wi: str) -> RefStatus:
        lookup_calls.append(wi)
        return RefStatus.open

    status = resolve_ref(entry=entry, manifest=_MANIFEST, local_status_lookup=lookup)
    assert status == RefStatus.open
    assert lookup_calls == ["li-abc"]


# ---------- SiblingWorkItemEntry ----------


def test_sibling_unknown_repo_returns_unknown() -> None:
    entry = SiblingWorkItemEntry(
        kind="sibling_work_item", repo="not-in-manifest", work_item_id="li-x"
    )
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
    )
    assert status == RefStatus.unknown


def test_sibling_uses_lookup_when_provided() -> None:
    entry = SiblingWorkItemEntry(kind="sibling_work_item", repo="livespec", work_item_id="li-q")
    captured: list[tuple[str, str]] = []

    def sib(repo: str, wi: str) -> RefStatus:
        captured.append((repo, wi))
        return RefStatus.closed

    status = resolve_ref(
        entry=entry,
        manifest=_MANIFEST,
        local_status_lookup=lambda _: RefStatus.open,
        sibling_status_lookup=sib,
    )
    assert status == RefStatus.closed
    assert captured == [("livespec", "li-q")]


def test_sibling_no_lookup_no_clone_returns_unknown() -> None:
    entry = SiblingWorkItemEntry(kind="sibling_work_item", repo="livespec", work_item_id="li-q")
    status = resolve_ref(
        entry=entry,
        manifest=_MANIFEST,
        local_status_lookup=lambda _: RefStatus.open,
    )
    assert status == RefStatus.unknown


def test_sibling_clone_path_missing_returns_unknown() -> None:
    entry = SiblingWorkItemEntry(kind="sibling_work_item", repo="with-clone", work_item_id="li-q")
    with patch.object(Path, "exists", return_value=False):
        status = resolve_ref(
            entry=entry,
            manifest=_MANIFEST,
            local_status_lookup=lambda _: RefStatus.open,
        )
    assert status == RefStatus.unknown


def test_sibling_clone_path_present_no_parser_returns_unknown() -> None:
    """v1 has no local-clone JSONL parser shipped in the runtime; returns unknown."""
    entry = SiblingWorkItemEntry(kind="sibling_work_item", repo="with-clone", work_item_id="li-q")
    with patch.object(Path, "exists", return_value=True):
        status = resolve_ref(
            entry=entry,
            manifest=_MANIFEST,
            local_status_lookup=lambda _: RefStatus.open,
        )
    assert status == RefStatus.unknown


# ---------- PullRequestEntry ----------


def test_pull_request_merged_returns_closed() -> None:
    entry = PullRequestEntry(kind="pull_request", repo="livespec", number=42)
    with (
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.query_pull_request_state",
            return_value="MERGED",
        ),
    ):
        status = resolve_ref(
            entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
        )
    assert status == RefStatus.closed


def test_pull_request_closed_returns_closed() -> None:
    entry = PullRequestEntry(kind="pull_request", repo="livespec", number=42)
    with (
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.query_pull_request_state",
            return_value="CLOSED",
        ),
    ):
        status = resolve_ref(
            entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
        )
    assert status == RefStatus.closed


def test_pull_request_open_returns_open() -> None:
    entry = PullRequestEntry(kind="pull_request", repo="livespec", number=42)
    with (
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.query_pull_request_state",
            return_value="OPEN",
        ),
    ):
        status = resolve_ref(
            entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
        )
    assert status == RefStatus.open


def test_pull_request_retry_exhausted_returns_unknown() -> None:
    entry = PullRequestEntry(kind="pull_request", repo="livespec", number=42)
    with (
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.query_pull_request_state",
            side_effect=RuntimeError("auth fail"),
        ),
    ):
        status = resolve_ref(
            entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
        )
    assert status == RefStatus.unknown


def test_pull_request_unknown_repo_returns_unknown() -> None:
    entry = PullRequestEntry(kind="pull_request", repo="missing", number=1)
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
    )
    assert status == RefStatus.unknown


# ---------- BranchEntry ----------


def test_branch_absent_remote_returns_closed() -> None:
    entry = BranchEntry(kind="branch", repo="livespec", name="feat/old")
    with (
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.branch_exists_on_remote",
            return_value=False,
        ),
    ):
        status = resolve_ref(
            entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
        )
    assert status == RefStatus.closed


def test_branch_present_merged_returns_closed() -> None:
    entry = BranchEntry(kind="branch", repo="livespec", name="feat/done")
    with (
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.branch_exists_on_remote",
            return_value=True,
        ),
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.branch_merged_into_default",
            return_value=True,
        ),
    ):
        status = resolve_ref(
            entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
        )
    assert status == RefStatus.closed


def test_branch_present_not_merged_returns_open() -> None:
    entry = BranchEntry(kind="branch", repo="livespec", name="feat/wip")
    with (
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.branch_exists_on_remote",
            return_value=True,
        ),
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.branch_merged_into_default",
            return_value=False,
        ),
    ):
        status = resolve_ref(
            entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
        )
    assert status == RefStatus.open


def test_branch_retry_exhausted_on_exists_returns_unknown() -> None:
    entry = BranchEntry(kind="branch", repo="livespec", name="feat/x")
    with (
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.branch_exists_on_remote",
            side_effect=RuntimeError("flake"),
        ),
    ):
        status = resolve_ref(
            entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
        )
    assert status == RefStatus.unknown


def test_branch_retry_exhausted_on_merged_returns_unknown() -> None:
    entry = BranchEntry(kind="branch", repo="livespec", name="feat/x")
    with (
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.branch_exists_on_remote",
            return_value=True,
        ),
        patch(
            "livespec_runtime.cross_repo.resolve.gh_provider.branch_merged_into_default",
            side_effect=RuntimeError("flake"),
        ),
    ):
        status = resolve_ref(
            entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
        )
    assert status == RefStatus.unknown


def test_branch_unknown_repo_returns_unknown() -> None:
    entry = BranchEntry(kind="branch", repo="missing", name="x")
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _: RefStatus.open
    )
    assert status == RefStatus.unknown
