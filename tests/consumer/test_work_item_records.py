"""Consumer-tier scenario tests: the WorkItem record, its identity, its store.

Covers SIX of the thirty-two `## Scenario:` headings ratified as v025 in
`SPECIFICATION/scenarios.md` — the optional-on-read defaults, the per-record
identity, the canonical head reduction, `materialize_work_items`,
`random_id_suffix`, and `WorkItemStore` conformance.

The consumer here is an impl-plugin: it constructs `WorkItem` records, hands
streams of them to the shared reducer, and exposes its own store facade over
whatever backend it owns. Every name imported below is ratified in
`SPECIFICATION/contracts.md` section "Module-level public surface".
"""

import inspect
import re
import string
from collections.abc import Iterator

from livespec_runtime.work_items.reduce import (
    materialize_work_items,
    random_id_suffix,
    reduce_work_item_heads,
    work_item_record_identity,
)
from livespec_runtime.work_items.store import WorkItemStore
from livespec_runtime.work_items.types import WorkItem

__all__: list[str] = []

# The lowercase base32 alphabet `random_id_suffix` draws from.
_BASE32_LOWER = string.ascii_lowercase + "234567"
_SUFFIX_LENGTH = 6
_SUFFIX_SAMPLES = 200


def _record(
    *,
    id: str,
    captured_at: str,
    title: str = "Title",
    supersedes: str | None = None,
) -> WorkItem:
    """Build a record from ONLY the fifteen required fields (plus `supersedes`)."""
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


class _InMemoryStoreFacade:
    """An in-memory store facade shaped exactly like a consumer's own.

    Structural conformance ONLY: it inherits from nothing, and in particular
    NOT from `WorkItemStore` — which is the whole point of the Protocol.
    """

    def __init__(self) -> None:
        self._records: list[WorkItem] = []

    def read_work_items(self) -> Iterator[WorkItem]:
        yield from self._records

    def append_work_item(self, *, item: WorkItem) -> None:
        self._records.append(item)


# ===========================================================================
# Record shape + identity scenarios
# ===========================================================================


def test_a_legacy_record_reads_its_optional_on_read_fields_back_as_defaults() -> None:
    """Covers scenario "a legacy record reads its optional-on-read fields back as their defaults".

    A record written before any of the ten optional-on-read fields existed
    carries only the fifteen required ones — including a real, non-sentinel
    `rank` — and every optional field reads back as its documented default
    with no in-place migration.
    """
    legacy = WorkItem(
        id="li-legacy",
        type="task",
        status="backlog",
        title="Title",
        description="Description",
        origin="freeform",
        gap_id=None,
        rank="a0",
        assignee=None,
        depends_on=(),
        captured_at="2026-09-01T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )

    assert legacy.rank == "a0"
    assert legacy.spec_commitment_hint is None
    assert legacy.acceptance_criteria is None
    assert legacy.notes is None
    assert legacy.supersedes is None
    assert legacy.admission_policy is None
    assert legacy.acceptance_policy is None
    assert legacy.blocked_reason is None
    assert legacy.factory_safety is None
    assert legacy.review_requirement is None
    assert legacy.awaits_scope_override is False


def test_record_identity_is_a_stable_sha256_over_the_canonical_serialization() -> None:
    """Covers scenario "record identity is a stable sha256 over the canonical serialization".

    ⚠️ THE SUPERSEDING RECORD HAS A DIFFERENT IDENTITY FROM THE ONE IT
    AMENDS. `supersedes` is itself part of the canonical serialization, so
    the pointer is CONTENT: two records identical in every other field
    still hash differently once one of them carries the pointer. Reading a
    unit test's NAME rather than its body is how that gets inverted.
    """
    one = _record(id="li-aaa111", captured_at="2026-09-01T00:00:00Z")
    same = _record(id="li-aaa111", captured_at="2026-09-01T00:00:00Z")

    identity = work_item_record_identity(item=one)

    assert re.fullmatch(r"sha256:[0-9a-f]{64}", identity)
    assert work_item_record_identity(item=same) == identity
    changed = _record(id="li-aaa111", captured_at="2026-09-01T00:00:00Z", title="Other")
    assert work_item_record_identity(item=changed) != identity
    amendment = _record(id="li-aaa111", captured_at="2026-09-01T00:00:00Z", supersedes=identity)
    assert work_item_record_identity(item=amendment) != identity


# ===========================================================================
# Head-reduction scenarios
# ===========================================================================


def test_supersession_reduction_keeps_only_heads_and_surfaces_divergence() -> None:
    """Covers scenario "supersession reduction keeps only heads and surfaces concurrent divergence"."""
    record_a = _record(id="li-chain", captured_at="2026-09-01T00:00:00Z", title="A")
    record_b = _record(
        id="li-chain",
        captured_at="2026-09-01T00:00:01Z",
        title="B",
        supersedes=work_item_record_identity(item=record_a),
    )
    ancestor = _record(id="li-fork", captured_at="2026-09-01T00:00:00Z", title="ancestor")
    ancestor_identity = work_item_record_identity(item=ancestor)
    record_c = _record(
        id="li-fork", captured_at="2026-09-01T00:00:01Z", title="C", supersedes=ancestor_identity
    )
    record_d = _record(
        id="li-fork", captured_at="2026-09-01T00:00:02Z", title="D", supersedes=ancestor_identity
    )

    heads = reduce_work_item_heads(records=iter([record_d, record_a, ancestor, record_b, record_c]))

    assert heads["li-chain"] == (record_b,)
    expected_fork_order = tuple(
        record
        for _key, record in sorted(
            (
                ((record.captured_at, work_item_record_identity(item=record)), record)
                for record in (record_c, record_d)
            ),
            key=lambda pair: pair[0],
        )
    )
    assert heads["li-fork"] == expected_fork_order
    assert len(heads["li-fork"]) == 2


def test_materialize_picks_one_head_per_id_by_the_full_tie_break() -> None:
    """Covers scenario "materialize picks one head per id and is the identity collection for a one-record-per-id substrate".

    ⚠️ THE TIE-BREAK IS THE FULL `(captured_at, identity)` PAIR, NOT
    `captured_at` ALONE. The divergent pair below shares a `captured_at` to
    the second, so only the per-record identity can decide the winner — a
    `max(..., key=captured_at)` reading picks arbitrarily here and this test
    would catch it.
    """
    ancestor = _record(id="li-fork", captured_at="2026-09-01T00:00:00Z", title="ancestor")
    ancestor_identity = work_item_record_identity(item=ancestor)
    later = _record(
        id="li-fork",
        captured_at="2026-09-01T00:00:09Z",
        title="later",
        supersedes=ancestor_identity,
    )
    earlier = _record(
        id="li-fork",
        captured_at="2026-09-01T00:00:01Z",
        title="earlier",
        supersedes=ancestor_identity,
    )

    by_captured_at = materialize_work_items(records=iter([ancestor, earlier, later]))

    assert by_captured_at["li-fork"] is later

    twin_one = _record(id="li-twin", captured_at="2026-09-01T00:00:00Z", title="ancestor")
    twin_ancestor_identity = work_item_record_identity(item=twin_one)
    twin_a = _record(
        id="li-twin",
        captured_at="2026-09-01T00:00:05Z",
        title="twin-a",
        supersedes=twin_ancestor_identity,
    )
    twin_b = _record(
        id="li-twin",
        captured_at="2026-09-01T00:00:05Z",
        title="twin-b",
        supersedes=twin_ancestor_identity,
    )
    assert twin_a.captured_at == twin_b.captured_at
    greatest_identity = max(
        (twin_a, twin_b), key=lambda record: work_item_record_identity(item=record)
    )

    by_identity = materialize_work_items(records=iter([twin_b, twin_one, twin_a]))

    assert by_identity["li-twin"] is greatest_identity

    solo_one = _record(id="li-solo1", captured_at="2026-09-01T00:00:00Z")
    solo_two = _record(id="li-solo2", captured_at="2026-09-01T00:00:00Z")

    degenerate = materialize_work_items(records=iter([solo_one, solo_two]))

    assert degenerate == {"li-solo1": solo_one, "li-solo2": solo_two}


def test_random_id_suffix_yields_a_six_character_base32_suffix_that_varies() -> None:
    """Covers scenario "random_id_suffix yields a six-character base32 suffix that varies across calls"."""
    suffixes = [random_id_suffix() for _ in range(_SUFFIX_SAMPLES)]

    assert all(len(suffix) == _SUFFIX_LENGTH for suffix in suffixes)
    assert all(set(suffix) <= set(_BASE32_LOWER) for suffix in suffixes)
    assert len(set(suffixes)) > 1


# ===========================================================================
# Store-conformance scenario
# ===========================================================================


def test_a_store_facade_satisfies_workitemstore_and_round_trips_append_then_read() -> None:
    """Covers scenario "a store facade satisfies WorkItemStore structurally and round-trips append then read".

    ⚠️ CONFORMANCE IS ASSERTED BY STATIC ASSIGNABILITY, NEVER BY `isinstance`.
    `WorkItemStore` is a plain `typing.Protocol` and is deliberately NOT
    `@runtime_checkable`, so `isinstance(facade, WorkItemStore)` RAISES
    `TypeError` rather than answering the question. The binding below is the
    static check (a typechecker rejects a facade that does not conform), the
    mro assertion pins that no inheritance is involved, and the signature
    comparison is the runtime evidence that the two operations really do
    match the Protocol's shape.
    """
    facade: WorkItemStore = _InMemoryStoreFacade()

    assert WorkItemStore not in type(facade).__mro__
    for operation in ("read_work_items", "append_work_item"):
        protocol_parameters = list(inspect.signature(getattr(WorkItemStore, operation)).parameters)
        assert protocol_parameters[0] == "self"
        assert (
            list(inspect.signature(getattr(facade, operation)).parameters)
            == (protocol_parameters[1:])
        )

    assert list(facade.read_work_items()) == []

    item = _record(id="li-aaa111", captured_at="2026-09-01T00:00:00Z")
    facade.append_work_item(item=item)

    assert list(facade.read_work_items()) == [item]
