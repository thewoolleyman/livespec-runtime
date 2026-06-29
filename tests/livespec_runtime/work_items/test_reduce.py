"""Tests for `livespec_runtime.work_items.reduce`.

Exercises the canonical PURE order-independent head reduction byte-faithfully
lifted from livespec-impl-git-jsonl:

- per-record identity STABILITY (pure function of record content);
- the DEGENERATE one-record-per-id case (the beads collection — every id
  has exactly one head, the record itself);
- a genuine OUT-OF-ORDER supersession chain (deterministic head
  selection independent of stream order);
- the `(captured_at, identity)` tie-break among divergent heads;
- DIVERGENT-head detection (two un-superseded heads for one id);
- the `random_id_suffix` format.

Reference: livespec/SPECIFICATION/contracts.md.
"""

import re

from livespec_runtime.work_items.reduce import (
    materialize_work_items,
    random_id_suffix,
    reduce_work_item_heads,
    work_item_record_identity,
)
from livespec_runtime.work_items.types import AuditRecord, WorkItem

__all__: list[str] = []


def _item(
    *,
    id: str,
    captured_at: str,
    supersedes: str | None = None,
    title: str = "Title",
) -> WorkItem:
    """Build a WorkItem with the fields the reducer reads, others defaulted."""
    return WorkItem(
        id=id,
        type="task",
        status="backlog",
        title=title,
        description="Description",
        origin="freeform",
        gap_id=None,
        rank="a0",
        assignee=None,
        depends_on=(),
        captured_at=captured_at,
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        supersedes=supersedes,
    )


# ---------------------------------------------------------------------------
# Per-record identity.
# ---------------------------------------------------------------------------


def test_record_identity_is_sha256_prefixed_hex() -> None:
    item = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z")
    identity = work_item_record_identity(item=item)
    assert re.fullmatch(r"sha256:[0-9a-f]{64}", identity)


def test_record_identity_is_stable_for_equal_records() -> None:
    a = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z")
    b = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z")
    assert work_item_record_identity(item=a) == work_item_record_identity(item=b)


def test_record_identity_differs_on_content_change() -> None:
    a = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z", title="A")
    b = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z", title="B")
    assert work_item_record_identity(item=a) != work_item_record_identity(item=b)


def test_record_identity_serializes_audit_subobject() -> None:
    # A record carrying a non-None audit exercises the audit-to-dict
    # canonicalization branch; identity stays a stable, content-derived
    # function (the same audit yields the same identity; a changed
    # merge_sha changes it).
    audit = AuditRecord(
        verification_timestamp="2026-06-20T01:00:00Z",
        commits=("c1",),
        files_changed=("a.py",),
        merge_sha="abc123",
        pr_number=7,
    )
    other_audit = AuditRecord(
        verification_timestamp="2026-06-20T01:00:00Z",
        commits=("c1",),
        files_changed=("a.py",),
        merge_sha="different",
        pr_number=7,
    )
    base = dict(
        id="li-aaa111",
        type="task",
        status="done",
        title="Title",
        description="Description",
        origin="freeform",
        gap_id=None,
        rank="a0",
        assignee=None,
        depends_on=(),
        captured_at="2026-06-20T00:00:00Z",
        resolution="completed",
        reason="done",
        superseded_by=None,
    )
    with_audit = WorkItem(audit=audit, **base)  # type: ignore[arg-type]
    with_audit_again = WorkItem(audit=audit, **base)  # type: ignore[arg-type]
    with_other_audit = WorkItem(audit=other_audit, **base)  # type: ignore[arg-type]
    assert work_item_record_identity(item=with_audit) == work_item_record_identity(
        item=with_audit_again
    )
    assert work_item_record_identity(item=with_audit) != work_item_record_identity(
        item=with_other_audit
    )


def test_record_identity_is_independent_of_supersedes_pointer_only() -> None:
    # supersedes is part of the canonical serialization, so a record that
    # supersedes another has a DIFFERENT identity from the original even
    # if all other fields match (the pointer is content).
    original = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z")
    amendment = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:00Z",
        supersedes=work_item_record_identity(item=original),
    )
    assert work_item_record_identity(item=amendment) != work_item_record_identity(item=original)


# ---------------------------------------------------------------------------
# Degenerate one-record-per-id (the beads collection case).
# ---------------------------------------------------------------------------


def test_degenerate_one_record_per_id_each_is_its_own_head() -> None:
    records = [
        _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z"),
        _item(id="li-bbb222", captured_at="2026-06-20T00:00:01Z"),
        _item(id="li-ccc333", captured_at="2026-06-20T00:00:02Z"),
    ]
    heads = reduce_work_item_heads(records=iter(records))
    assert set(heads) == {"li-aaa111", "li-bbb222", "li-ccc333"}
    for entity_id, head_tuple in heads.items():
        assert len(head_tuple) == 1
        assert head_tuple[0].id == entity_id


def test_degenerate_materialize_is_identity_collection() -> None:
    records = [
        _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z"),
        _item(id="li-bbb222", captured_at="2026-06-20T00:00:01Z"),
    ]
    materialized = materialize_work_items(records=iter(records))
    assert set(materialized) == {"li-aaa111", "li-bbb222"}
    assert materialized["li-aaa111"].id == "li-aaa111"
    assert materialized["li-bbb222"].id == "li-bbb222"


def test_duplicate_identical_records_collapse_to_one_head() -> None:
    # Same id, byte-identical content (e.g. a line duplicated by a
    # merge=union merge) collapses to a single head.
    rec = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z")
    dup = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z")
    heads = reduce_work_item_heads(records=iter([rec, dup]))
    assert len(heads["li-aaa111"]) == 1


# ---------------------------------------------------------------------------
# Genuine out-of-order supersession chain.
# ---------------------------------------------------------------------------


def _supersession_chain() -> tuple[WorkItem, WorkItem, WorkItem]:
    """v1 -> v2 -> v3 linear supersession chain over one id.

    Each later record's `supersedes` names the prior record's identity.
    Returned in chronological order; tests shuffle the stream to prove
    order-independence.
    """
    v1 = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z", title="v1")
    v2 = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:01Z",
        title="v2",
        supersedes=work_item_record_identity(item=v1),
    )
    v3 = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:02Z",
        title="v3",
        supersedes=work_item_record_identity(item=v2),
    )
    return v1, v2, v3


def test_supersession_chain_in_order_yields_single_head() -> None:
    v1, v2, v3 = _supersession_chain()
    heads = reduce_work_item_heads(records=iter([v1, v2, v3]))
    assert len(heads["li-aaa111"]) == 1
    assert heads["li-aaa111"][0].title == "v3"


def test_supersession_chain_out_of_order_yields_same_head() -> None:
    # The whole point of the canonical reduction: physical order is
    # irrelevant. Feeding the chain reversed/shuffled still resolves to v3.
    v1, v2, v3 = _supersession_chain()
    for order in ([v3, v1, v2], [v2, v3, v1], [v3, v2, v1]):
        heads = reduce_work_item_heads(records=iter(order))
        assert len(heads["li-aaa111"]) == 1
        assert heads["li-aaa111"][0].title == "v3"


def test_supersession_chain_materialize_picks_head() -> None:
    v1, v2, v3 = _supersession_chain()
    materialized = materialize_work_items(records=iter([v3, v1, v2]))
    assert materialized["li-aaa111"].title == "v3"


# ---------------------------------------------------------------------------
# Divergent heads + the (captured_at, identity) tie-break.
# ---------------------------------------------------------------------------


def test_divergent_heads_are_both_surfaced() -> None:
    # v1 superseded by TWO concurrent amendments (a fork). Neither fork
    # supersedes the other, so both are heads — concurrent divergence,
    # surfaced rather than silently resolved.
    v1 = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z", title="v1")
    v1_identity = work_item_record_identity(item=v1)
    fork_a = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:01Z",
        title="fork-a",
        supersedes=v1_identity,
    )
    fork_b = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:02Z",
        title="fork-b",
        supersedes=v1_identity,
    )
    heads = reduce_work_item_heads(records=iter([fork_a, v1, fork_b]))
    head_titles = [head.title for head in heads["li-aaa111"]]
    assert len(head_titles) == 2
    assert set(head_titles) == {"fork-a", "fork-b"}


def test_divergent_heads_ordered_by_captured_at_ascending() -> None:
    # The heads tuple is ordered ascending by (captured_at, identity), so
    # the materialize tie-break winner (heads[-1]) is the greatest.
    v1 = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z", title="v1")
    v1_identity = work_item_record_identity(item=v1)
    early = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:01Z",
        title="early",
        supersedes=v1_identity,
    )
    late = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:09Z",
        title="late",
        supersedes=v1_identity,
    )
    heads = reduce_work_item_heads(records=iter([late, v1, early]))
    titles_in_order = [head.title for head in heads["li-aaa111"]]
    assert titles_in_order == ["early", "late"]


def test_divergent_heads_materialize_picks_greatest_captured_at() -> None:
    v1 = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z", title="v1")
    v1_identity = work_item_record_identity(item=v1)
    early = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:01Z",
        title="early",
        supersedes=v1_identity,
    )
    late = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:09Z",
        title="late",
        supersedes=v1_identity,
    )
    materialized = materialize_work_items(records=iter([late, v1, early]))
    assert materialized["li-aaa111"].title == "late"


def test_tie_break_falls_through_to_identity_on_equal_captured_at() -> None:
    # Two divergent heads with the SAME captured_at must still order
    # deterministically: the secondary key is the per-record identity.
    v1 = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z", title="v1")
    v1_identity = work_item_record_identity(item=v1)
    fork_a = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:05Z",
        title="fork-a",
        supersedes=v1_identity,
    )
    fork_b = _item(
        id="li-aaa111",
        captured_at="2026-06-20T00:00:05Z",
        title="fork-b",
        supersedes=v1_identity,
    )
    # Determine the expected order purely from identities (the tie-break).
    expected_by_identity = sorted(
        [
            (work_item_record_identity(item=fork_a), "fork-a"),
            (work_item_record_identity(item=fork_b), "fork-b"),
        ]
    )
    expected_titles = [title for _, title in expected_by_identity]

    heads_one = reduce_work_item_heads(records=iter([fork_a, v1, fork_b]))
    heads_two = reduce_work_item_heads(records=iter([fork_b, fork_a, v1]))
    assert [h.title for h in heads_one["li-aaa111"]] == expected_titles
    assert [h.title for h in heads_two["li-aaa111"]] == expected_titles


# ---------------------------------------------------------------------------
# random_id_suffix.
# ---------------------------------------------------------------------------


def test_random_id_suffix_format() -> None:
    suffix = random_id_suffix()
    assert re.fullmatch(r"[a-z2-7]{6}", suffix)


def test_random_id_suffix_is_lowercase_base32_alphabet() -> None:
    # base32 alphabet trimmed to 6 chars: lowercase a-z plus digits 2-7.
    for _ in range(50):
        suffix = random_id_suffix()
        assert len(suffix) == 6
        assert set(suffix) <= set("abcdefghijklmnopqrstuvwxyz234567")


def test_random_id_suffix_varies_across_calls() -> None:
    suffixes = {random_id_suffix() for _ in range(50)}
    # Collisions are negligible; a single distinct value across 50 calls
    # would indicate a broken (constant) generator.
    assert len(suffixes) > 1
