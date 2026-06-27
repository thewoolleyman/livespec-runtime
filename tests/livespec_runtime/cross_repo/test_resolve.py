"""Tests for `livespec_runtime.cross_repo.resolve.resolve_ref`.

Exercises the exhaustive-walk resolver across all four
`DependsOnEntry` variants and every resolution outcome
(`OPEN`, `CLOSED`, `UNKNOWN`).

Provider calls (`gh_provider.query_pull_request_state`,
`gh_provider.branch_exists_on_remote`,
`gh_provider.branch_merged_into_default`) are monkeypatched at the
module attribute level so the resolve-walker's lambdas see the
patched value on each invocation. `time.sleep` is monkeypatched in
retry-exhaustion tests so they don't burn real wall-clock backoff.

Schema reference: livespec/SPECIFICATION/contracts.md v072.
"""

import time
from typing import Any

import pytest

from livespec_runtime.cross_repo.providers import github as gh_provider
from livespec_runtime.cross_repo.resolve import resolve_ref
from livespec_runtime.cross_repo.types import (
    BranchDependency,
    CrossRepoManifest,
    CrossRepoTarget,
    LocalDependency,
    PullRequestDependency,
    RefStatus,
    SiblingWorkItemDependency,
)

__all__: list[str] = []

_MANIFEST = CrossRepoManifest(
    targets={
        "livespec": CrossRepoTarget(github_url="https://github.com/thewoolleyman/livespec"),
        "runtime": CrossRepoTarget(
            github_url="https://github.com/thewoolleyman/livespec-runtime",
            default_branch="main",
        ),
    },
)


def _raise_runtime_error(*_args: Any, **_kwargs: Any) -> Any:
    raise RuntimeError("simulated gh failure")


def test_local_dependency_delegates_to_lookup() -> None:
    captured: list[str] = []

    def lookup(work_item_id: str) -> RefStatus:
        captured.append(work_item_id)
        return RefStatus.CLOSED

    entry = LocalDependency(work_item_id="li-abc")
    status = resolve_ref(entry=entry, manifest=_MANIFEST, local_status_lookup=lookup)
    assert status == RefStatus.CLOSED
    assert captured == ["li-abc"]


def test_sibling_unknown_repo_returns_unknown() -> None:
    entry = SiblingWorkItemDependency(repo="not-in-manifest", work_item_id="li-x")
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.UNKNOWN


def test_sibling_uses_lookup_when_provided() -> None:
    captured: list[tuple[str, str]] = []

    def sibling_lookup(repo: str, work_item_id: str) -> RefStatus:
        captured.append((repo, work_item_id))
        return RefStatus.CLOSED

    entry = SiblingWorkItemDependency(repo="livespec", work_item_id="li-q")
    status = resolve_ref(
        entry=entry,
        manifest=_MANIFEST,
        local_status_lookup=lambda _wi: RefStatus.OPEN,
        sibling_status_lookup=sibling_lookup,
    )
    assert status == RefStatus.CLOSED
    assert captured == [("livespec", "li-q")]


def test_sibling_no_lookup_returns_unknown() -> None:
    entry = SiblingWorkItemDependency(repo="livespec", work_item_id="li-q")
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.UNKNOWN


def test_pull_request_unknown_repo_returns_unknown() -> None:
    entry = PullRequestDependency(repo="not-in-manifest", number=42)
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.UNKNOWN


def test_pull_request_open_returns_open(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh_provider, "query_pull_request_state", lambda **_kwargs: "OPEN")
    entry = PullRequestDependency(repo="livespec", number=42)
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.OPEN


def test_pull_request_merged_returns_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh_provider, "query_pull_request_state", lambda **_kwargs: "MERGED")
    entry = PullRequestDependency(repo="livespec", number=42)
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.CLOSED


def test_pull_request_closed_returns_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh_provider, "query_pull_request_state", lambda **_kwargs: "CLOSED")
    entry = PullRequestDependency(repo="livespec", number=42)
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.CLOSED


def test_pull_request_retry_exhaustion_returns_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(gh_provider, "query_pull_request_state", _raise_runtime_error)
    entry = PullRequestDependency(repo="livespec", number=42)
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.UNKNOWN


def test_branch_unknown_repo_returns_unknown() -> None:
    entry = BranchDependency(repo="not-in-manifest", name="feat/foo")
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.UNKNOWN


def test_branch_absent_on_remote_returns_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh_provider, "branch_exists_on_remote", lambda **_kwargs: False)
    entry = BranchDependency(repo="livespec", name="feat/foo")
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.CLOSED


def test_branch_present_and_merged_returns_closed(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh_provider, "branch_exists_on_remote", lambda **_kwargs: True)
    monkeypatch.setattr(gh_provider, "branch_merged_into_default", lambda **_kwargs: True)
    entry = BranchDependency(repo="livespec", name="feat/foo")
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.CLOSED


def test_branch_present_and_not_merged_returns_open(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gh_provider, "branch_exists_on_remote", lambda **_kwargs: True)
    monkeypatch.setattr(gh_provider, "branch_merged_into_default", lambda **_kwargs: False)
    entry = BranchDependency(repo="livespec", name="feat/foo")
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.OPEN


def test_branch_exists_check_retry_exhausted_returns_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(gh_provider, "branch_exists_on_remote", _raise_runtime_error)
    entry = BranchDependency(repo="livespec", name="feat/foo")
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.UNKNOWN


def test_branch_merged_check_retry_exhausted_returns_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(time, "sleep", lambda _seconds: None)
    monkeypatch.setattr(gh_provider, "branch_exists_on_remote", lambda **_kwargs: True)
    monkeypatch.setattr(gh_provider, "branch_merged_into_default", _raise_runtime_error)
    entry = BranchDependency(repo="livespec", name="feat/foo")
    status = resolve_ref(
        entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN
    )
    assert status == RefStatus.UNKNOWN


def test_branch_uses_target_default_branch(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[dict[str, Any]] = []

    def fake_merged(**kwargs: Any) -> bool:
        captured.append(kwargs)
        return True

    monkeypatch.setattr(gh_provider, "branch_exists_on_remote", lambda **_kwargs: True)
    monkeypatch.setattr(gh_provider, "branch_merged_into_default", fake_merged)
    entry = BranchDependency(repo="runtime", name="feat/foo")
    _ = resolve_ref(entry=entry, manifest=_MANIFEST, local_status_lookup=lambda _wi: RefStatus.OPEN)
    assert len(captured) == 1
    assert captured[0]["default_branch"] == "main"
