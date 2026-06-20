"""Tests for `livespec_runtime.work_items.types`.

Verifies the unified `WorkItem` model (the git-jsonl 16-field shape
carrying `supersedes`), the `AuditRecord` sub-object, the schema
enums/aliases, the `supersedes` / `spec_commitment_hint` defaults, and
frozenness.

Schema reference: livespec/SPECIFICATION/contracts.md §"Work-items JSONL
record schema".
"""

import pytest

from livespec_runtime.work_items.types import AuditRecord, WorkItem

__all__: list[str] = []


def _work_item(**overrides: object) -> WorkItem:
    """Build a WorkItem with sensible defaults, overridable per-field."""
    base: dict[str, object] = {
        "id": "li-aaa111",
        "type": "task",
        "status": "open",
        "title": "Title",
        "description": "Description",
        "origin": "freeform",
        "gap_id": None,
        "priority": 2,
        "assignee": None,
        "depends_on": (),
        "captured_at": "2026-06-20T00:00:00Z",
        "resolution": None,
        "reason": None,
        "audit": None,
        "superseded_by": None,
    }
    base.update(overrides)
    return WorkItem(**base)  # type: ignore[arg-type]


def test_work_item_construction_minimal() -> None:
    item = _work_item()
    assert item.id == "li-aaa111"
    assert item.type == "task"
    assert item.status == "open"
    assert item.origin == "freeform"
    assert item.depends_on == ()


def test_work_item_supersedes_defaults_to_none() -> None:
    item = _work_item()
    assert item.supersedes is None


def test_work_item_spec_commitment_hint_defaults_to_none() -> None:
    item = _work_item()
    assert item.spec_commitment_hint is None


def test_work_item_supersedes_carries_prior_identity() -> None:
    item = _work_item(supersedes="sha256:deadbeef")
    assert item.supersedes == "sha256:deadbeef"


def test_work_item_has_sixteen_schema_fields() -> None:
    # The unified shape is the 16-field git-jsonl record; the two
    # optional-on-read fields (spec_commitment_hint, supersedes) are the
    # fifteenth and sixteenth keys.
    field_names = {f for f in WorkItem.__dataclass_fields__}
    assert field_names == {
        "id",
        "type",
        "status",
        "title",
        "description",
        "origin",
        "gap_id",
        "priority",
        "assignee",
        "depends_on",
        "captured_at",
        "resolution",
        "reason",
        "audit",
        "superseded_by",
        "spec_commitment_hint",
        "supersedes",
    }


def test_work_item_carries_audit_record() -> None:
    audit = AuditRecord(
        verification_timestamp="2026-06-20T01:00:00Z",
        commits=("abc",),
        files_changed=("a.py",),
        merge_sha="f00",
    )
    item = _work_item(audit=audit, status="closed", resolution="completed", reason="done")
    assert item.audit is audit
    assert audit.merge_sha == "f00"


def test_work_item_is_frozen() -> None:
    item = _work_item()
    with pytest.raises(AttributeError):
        item.title = "other"  # type: ignore[misc]


def test_audit_record_pr_number_defaults_to_none() -> None:
    audit = AuditRecord(
        verification_timestamp="2026-06-20T01:00:00Z",
        commits=(),
        files_changed=(),
        merge_sha="f00",
    )
    assert audit.pr_number is None


def test_audit_record_carries_pr_number() -> None:
    audit = AuditRecord(
        verification_timestamp="2026-06-20T01:00:00Z",
        commits=("c1", "c2"),
        files_changed=("a.py", "b.py"),
        merge_sha="abc123",
        pr_number=42,
    )
    assert audit.pr_number == 42
    assert audit.commits == ("c1", "c2")


def test_audit_record_is_frozen() -> None:
    audit = AuditRecord(
        verification_timestamp="2026-06-20T01:00:00Z",
        commits=(),
        files_changed=(),
        merge_sha="f00",
    )
    with pytest.raises(AttributeError):
        audit.merge_sha = "other"  # type: ignore[misc]
