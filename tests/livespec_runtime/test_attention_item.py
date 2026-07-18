"""Tests for `livespec_runtime.attention_item`."""

from typing import get_args

import pytest

from livespec_runtime import attention_item
from livespec_runtime.attention_item import (
    AttentionItem,
    Handoff,
    SourceRef,
    validate_attention_item_id,
)

__all__: list[str] = []


def test_attention_item_carries_required_schema_fields() -> None:
    item = AttentionItem(
        id="valve:approve:li-abc123",
        kind="human-valve",
        urgency="high",
        summary="Approve the work item.",
        source_ref=SourceRef(repo="runtime", work_item="li-abc123"),
        handoff=Handoff(kind="drive", action_id="approve", command="approve li-abc123"),
    )

    assert item.id == "valve:approve:li-abc123"
    assert item.kind == "human-valve"
    assert item.urgency == "high"
    assert item.source_ref.path is None
    assert item.handoff.action_id == "approve"


def test_attention_item_is_frozen() -> None:
    item = AttentionItem(
        id="impl:li-abc123",
        kind="impl",
        urgency="medium",
        summary="Implement the item.",
        source_ref=SourceRef(repo="runtime", work_item="li-abc123"),
        handoff=Handoff(kind="drive", command="drive li-abc123"),
    )

    with pytest.raises(AttributeError, match="cannot assign to field 'summary'"):
        item.summary = "other"  # type: ignore[misc]


def test_attention_kind_carries_host_only_residue_kind() -> None:
    assert set(get_args(attention_item.AttentionKind)) == {
        "human-valve",
        "impl",
        "spec",
        "plan",
        "hygiene",
        "internal",
        "host-only",
    }


def test_validate_attention_item_id_accepts_stable_natural_keys() -> None:
    valid_ids = (
        "valve:approve:li-abc123",
        "impl:li-abc123",
        "hygiene:stale-branch:refs/heads/feat-x",
        "plan:needs-attention",
        "spec:next:SPECIFICATION/contracts.md",
        "host-only:needs-host-secrets:li-abc123",
    )

    assert all(validate_attention_item_id(id=value) for value in valid_ids)


def test_validate_attention_item_id_rejects_positional_or_malformed_keys() -> None:
    invalid_ids = (
        "0",
        "impl:0",
        "valve:approve:0",
        "hygiene:stale-branch:0",
        "plan:0",
        "spec:next:0",
        "internal:li-abc123",
        "spec::SPECIFICATION/contracts.md",
        "hygiene:type:",
        "host-only:needs-host-secrets:0",
        "host-only:type:",
    )

    assert not any(validate_attention_item_id(id=value) for value in invalid_ids)
