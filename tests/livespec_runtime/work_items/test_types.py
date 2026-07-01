"""Tests for `livespec_runtime.work_items.types`.

Verifies the unified `WorkItem` model (the 22-field shape codified by
this repo's own `### livespec_runtime.work_items.types`), the
`AuditRecord` sub-object, the schema enums/aliases (the 7-state
`WorkItemStatus`, the `AdmissionPolicy` / `AcceptancePolicy` /
`StoredBlockedReason` aliases), the optional-on-read defaults
(`spec_commitment_hint`, `acceptance_criteria`, `notes`, `supersedes`,
`admission_policy`, `acceptance_policy`, `blocked_reason`), the
required `rank` ordering key, and frozenness.

Schema reference: this repo's own `SPECIFICATION/contracts.md`
§`### livespec_runtime.work_items.types`.
"""

import pytest

from livespec_runtime.work_items.types import AuditRecord, WorkItem

__all__: list[str] = []

# The ratified 22-field order (required block, then optional-on-read
# block), per `### livespec_runtime.work_items.types`.
_EXPECTED_FIELD_ORDER: tuple[str, ...] = (
    "id",
    "type",
    "status",
    "title",
    "description",
    "origin",
    "gap_id",
    "rank",
    "assignee",
    "depends_on",
    "captured_at",
    "resolution",
    "reason",
    "audit",
    "superseded_by",
    "spec_commitment_hint",
    "acceptance_criteria",
    "notes",
    "supersedes",
    "admission_policy",
    "acceptance_policy",
    "blocked_reason",
)


def _work_item(**overrides: object) -> WorkItem:
    """Build a WorkItem with sensible defaults, overridable per-field."""
    base: dict[str, object] = {
        "id": "li-aaa111",
        "type": "task",
        "status": "backlog",
        "title": "Title",
        "description": "Description",
        "origin": "freeform",
        "gap_id": None,
        "rank": "a0",
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
    assert item.status == "backlog"
    assert item.origin == "freeform"
    assert item.rank == "a0"
    assert item.depends_on == ()


def test_work_item_rank_is_required_and_carried() -> None:
    # `rank` is the sole ordering authority: required, non-null, no
    # default. A field this library owns is set on every record it writes.
    item = _work_item(rank="a1V")
    assert item.rank == "a1V"


def test_work_item_supersedes_defaults_to_none() -> None:
    item = _work_item()
    assert item.supersedes is None


def test_work_item_spec_commitment_hint_defaults_to_none() -> None:
    item = _work_item()
    assert item.spec_commitment_hint is None


def test_work_item_acceptance_criteria_defaults_to_none() -> None:
    item = _work_item()
    assert item.acceptance_criteria is None


def test_work_item_notes_defaults_to_none() -> None:
    item = _work_item()
    assert item.notes is None


def test_work_item_admission_policy_defaults_to_none() -> None:
    item = _work_item()
    assert item.admission_policy is None


def test_work_item_acceptance_policy_defaults_to_none() -> None:
    item = _work_item()
    assert item.acceptance_policy is None


def test_work_item_blocked_reason_defaults_to_none() -> None:
    item = _work_item()
    assert item.blocked_reason is None


def test_work_item_supersedes_carries_prior_identity() -> None:
    item = _work_item(supersedes="sha256:deadbeef")
    assert item.supersedes == "sha256:deadbeef"


def test_work_item_carries_acceptance_criteria_and_notes() -> None:
    item = _work_item(
        acceptance_criteria="Given context, then preserve it.",
        notes="Operator rider is load-bearing.",
    )
    assert item.acceptance_criteria == "Given context, then preserve it."
    assert item.notes == "Operator rider is load-bearing."


def test_work_item_carries_policy_fields() -> None:
    # The three policy fields follow the blessed `… | None` optional-on-
    # read pattern; when set, they carry the stored value verbatim.
    item = _work_item(
        status="blocked",
        admission_policy="auto",
        acceptance_policy="ai-then-human",
        blocked_reason="needs-human",
    )
    assert item.admission_policy == "auto"
    assert item.acceptance_policy == "ai-then-human"
    assert item.blocked_reason == "needs-human"


def test_work_item_accepts_each_lifecycle_status() -> None:
    # The seven stored lifecycle states (the `WorkItemStatus` Literal).
    for status in (
        "backlog",
        "pending-approval",
        "ready",
        "active",
        "acceptance",
        "blocked",
        "done",
    ):
        assert _work_item(status=status).status == status


def test_work_item_active_carries_assignee() -> None:
    # `assignee` is REUSED in place as the claimed-by/owner field;
    # REQUIRED once `status == "active"` (the `active ⟹ assignee`
    # invariant the doctor enforces — the dataclass carries the value).
    item = _work_item(status="active", assignee="agent-7")
    assert item.assignee == "agent-7"


def test_work_item_has_twenty_two_schema_fields() -> None:
    # The unified shape is the 22-field record: 15 required (including
    # the `rank` ordering key, `priority` removed), then 7 optional-on-
    # read (spec_commitment_hint, acceptance_criteria, notes,
    # supersedes, admission_policy, acceptance_policy, blocked_reason).
    field_names = set(WorkItem.__dataclass_fields__)
    assert field_names == set(_EXPECTED_FIELD_ORDER)
    assert "priority" not in field_names
    assert "rank" in field_names


def test_work_item_field_order_matches_contract() -> None:
    # The ratified `### livespec_runtime.work_items.types` pins the exact
    # 22-field order (required block, then optional-on-read block).
    assert tuple(WorkItem.__dataclass_fields__) == _EXPECTED_FIELD_ORDER


def test_work_item_carries_audit_record() -> None:
    audit = AuditRecord(
        verification_timestamp="2026-06-20T01:00:00Z",
        commits=("abc",),
        files_changed=("a.py",),
        merge_sha="f00",
    )
    item = _work_item(audit=audit, status="done", resolution="completed", reason="done")
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
