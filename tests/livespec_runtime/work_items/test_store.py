"""Tests for `livespec_runtime.work_items.store`.

Verifies the `WorkItemStore` `typing.Protocol` is a usable structural
contract: a thin in-memory facade (shaped exactly like a consumer's
facade over its per-impl store free functions) satisfies the Protocol
both at type-check time (it is assignable to a `WorkItemStore`-typed
binding) and behaviorally (read/append round-trip + the canonical
reducer composes over its output).

Reference: livespec/SPECIFICATION/contracts.md §"Materialized view".
"""

from collections.abc import Iterator

from livespec_runtime.work_items.reduce import materialize_work_items
from livespec_runtime.work_items.store import WorkItemStore
from livespec_runtime.work_items.types import WorkItem

__all__: list[str] = []


class _InMemoryStore:
    """A minimal in-memory `WorkItemStore` facade (consumer-shaped).

    Stands in for a real consumer facade (`JsonlWorkItemStore` /
    `BeadsWorkItemStore`) that would wrap the per-impl `read_work_items`
    / `append_work_item` free functions. It conforms to the Protocol
    structurally — no inheritance from `WorkItemStore`.
    """

    def __init__(self) -> None:
        self._records: list[WorkItem] = []

    def read_work_items(self) -> Iterator[WorkItem]:
        yield from self._records

    def append_work_item(self, *, item: WorkItem) -> None:
        self._records.append(item)


def _item(*, id: str, captured_at: str) -> WorkItem:
    return WorkItem(
        id=id,
        type="task",
        status="open",
        title="Title",
        description="Description",
        origin="freeform",
        gap_id=None,
        priority=2,
        assignee=None,
        depends_on=(),
        captured_at=captured_at,
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
    )


def test_in_memory_facade_satisfies_protocol() -> None:
    # Structural conformance: the concrete facade binds to a
    # WorkItemStore-typed variable with no inheritance.
    store: WorkItemStore = _InMemoryStore()
    assert isinstance(store, _InMemoryStore)


def test_append_then_read_round_trips() -> None:
    store: WorkItemStore = _InMemoryStore()
    item = _item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z")
    store.append_work_item(item=item)
    read_back = list(store.read_work_items())
    assert read_back == [item]


def test_read_is_empty_before_any_append() -> None:
    store: WorkItemStore = _InMemoryStore()
    assert list(store.read_work_items()) == []


def test_canonical_reducer_composes_over_store_output() -> None:
    # The whole reason the Protocol exists: tools over the shared model
    # consume a WorkItemStore and the canonical reducer composes over its
    # stream regardless of substrate.
    store: WorkItemStore = _InMemoryStore()
    store.append_work_item(item=_item(id="li-aaa111", captured_at="2026-06-20T00:00:00Z"))
    store.append_work_item(item=_item(id="li-bbb222", captured_at="2026-06-20T00:00:01Z"))
    materialized = materialize_work_items(records=store.read_work_items())
    assert set(materialized) == {"li-aaa111", "li-bbb222"}
