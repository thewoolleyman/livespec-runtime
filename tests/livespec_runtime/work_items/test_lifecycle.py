"""Tests for `livespec_runtime.work_items.lifecycle`.

Exercises the single lane authority:

- `lane_of` overlay truth-table (the recommended scenarios in
  `plan/work-item-state-machine/research/01-spec-deltas.md`): stored
  `ready` + open dependency renders `blocked:dependency`; stored
  `blocked` renders its stored reason; every non-overlay state passes
  straight through;
- `is_item_ready` agrees with `lane_of(...).name == "ready"` by
  construction;
- `ready_sort_key` orders by `rank` then `id`;
- the dependency-blocking predicate's fail-closed + status-mapping
  branches (open / done / missing / sibling-unknown / unparseable),
  all resolved OFFLINE (local + manifest-absent deps only — no `gh`).

Schema reference: this repo's own `SPECIFICATION/contracts.md`
§`### livespec_runtime.work_items.lifecycle`.
"""

import pytest

from livespec_runtime.cross_repo.types import CrossRepoManifest
from livespec_runtime.work_items.lifecycle import (
    Lane,
    is_item_ready,
    lane_of,
    ready_sort_key,
)
from livespec_runtime.work_items.types import WorkItem

__all__: list[str] = []

EMPTY_MANIFEST = CrossRepoManifest(targets={})


def _item(**overrides: object) -> WorkItem:
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


# ---------------------------------------------------------------------------
# Scenario: every non-overlay state passes straight through.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "status",
    ["backlog", "pending-approval", "active", "acceptance", "done"],
)
def test_lane_of_passes_non_overlay_states_through(status: str) -> None:
    item = _item(id="li-a", status=status)
    lane = lane_of(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name=status, reason=None)  # type: ignore[arg-type]


def test_lane_of_ready_with_no_deps_is_ready() -> None:
    item = _item(id="li-a", status="ready")
    lane = lane_of(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="ready", reason=None)


# ---------------------------------------------------------------------------
# Scenario: stored `blocked` renders its stored reason.
# ---------------------------------------------------------------------------


def test_lane_of_stored_blocked_renders_needs_human() -> None:
    item = _item(id="li-a", status="blocked", blocked_reason="needs-human")
    lane = lane_of(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="blocked", reason="needs-human")


def test_lane_of_stored_blocked_renders_infra_external() -> None:
    item = _item(id="li-a", status="blocked", blocked_reason="infra-external")
    lane = lane_of(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="blocked", reason="infra-external")


def test_lane_of_stored_blocked_wins_over_open_dependency() -> None:
    # The stored-`blocked` branch returns first: a stored-blocked item
    # renders its stored reason even if it carries an open dependency
    # (the `dependency` overlay applies only to stored-`ready`).
    dep = _item(id="li-dep", status="active")
    item = _item(
        id="li-a",
        status="blocked",
        blocked_reason="needs-human",
        depends_on=("li-dep",),
    )
    index = {"li-dep": dep, "li-a": item}
    lane = lane_of(item=item, index=index, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="blocked", reason="needs-human")


# ---------------------------------------------------------------------------
# Scenario: stored `ready` + open dependency renders `blocked:dependency`.
# ---------------------------------------------------------------------------


def test_lane_of_ready_with_open_local_dep_is_blocked_dependency() -> None:
    dep = _item(id="li-dep", status="active")  # not done → OPEN → blocks
    item = _item(id="li-a", status="ready", depends_on=("li-dep",))
    index = {"li-dep": dep, "li-a": item}
    lane = lane_of(item=item, index=index, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="blocked", reason="dependency")


def test_lane_of_ready_with_done_local_dep_is_ready() -> None:
    dep = _item(id="li-dep", status="done")  # done → CLOSED → does not block
    item = _item(id="li-a", status="ready", depends_on=("li-dep",))
    index = {"li-dep": dep, "li-a": item}
    lane = lane_of(item=item, index=index, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="ready", reason=None)


def test_lane_of_ready_with_missing_local_dep_is_ready_unknown_non_blocking() -> None:
    # A missing dependency id resolves to UNKNOWN, which does NOT block
    # (the doctor's orphan-dependency invariant is the right surface).
    item = _item(id="li-a", status="ready", depends_on=("li-missing",))
    lane = lane_of(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="ready", reason=None)


def test_lane_of_ready_with_typed_dict_local_dep_open_is_blocked_dependency() -> None:
    dep = _item(id="li-dep", status="backlog")  # not done → OPEN → blocks
    item = _item(
        id="li-a",
        status="ready",
        depends_on=({"kind": "local", "work_item_id": "li-dep"},),
    )
    index = {"li-dep": dep, "li-a": item}
    lane = lane_of(item=item, index=index, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="blocked", reason="dependency")


def test_lane_of_ready_with_sibling_dep_is_ready_unknown_non_blocking() -> None:
    # A sibling work-item dep whose repo is absent from the manifest
    # resolves to UNKNOWN (no runtime→beads back-edge, no network) and
    # therefore does NOT block.
    item = _item(
        id="li-a",
        status="ready",
        depends_on=({"kind": "sibling_work_item", "repo": "other", "work_item_id": "x-1"},),
    )
    lane = lane_of(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="ready", reason=None)


def test_lane_of_ready_with_malformed_typed_dep_is_blocked_dependency() -> None:
    # A typed dict failing schema validation (`local` missing its
    # `work_item_id`) is unparseable → fail-closed → blocks.
    item = _item(id="li-a", status="ready", depends_on=({"kind": "local"},))
    lane = lane_of(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="blocked", reason="dependency")


def test_lane_of_ready_with_non_str_non_dict_dep_is_blocked_dependency() -> None:
    # A depends_on cell that is neither a bare string nor a typed dict is
    # unparseable → fail-closed → blocks (the final `_parse_entry` guard).
    item = _item(id="li-a", status="ready", depends_on=(123,))
    lane = lane_of(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="blocked", reason="dependency")


# ---------------------------------------------------------------------------
# is_item_ready agrees with lane_of by construction.
# ---------------------------------------------------------------------------


def test_is_item_ready_true_for_ready_with_no_open_deps() -> None:
    item = _item(id="li-a", status="ready")
    assert is_item_ready(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST) is True


def test_is_item_ready_false_for_ready_with_open_dep() -> None:
    dep = _item(id="li-dep", status="active")
    item = _item(id="li-a", status="ready", depends_on=("li-dep",))
    index = {"li-dep": dep, "li-a": item}
    assert is_item_ready(item=item, index=index, manifest=EMPTY_MANIFEST) is False


def test_is_item_ready_false_for_non_ready_status() -> None:
    item = _item(id="li-a", status="backlog")
    assert is_item_ready(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST) is False


# ---------------------------------------------------------------------------
# Scenario: ready_sort_key orders by rank then id.
# ---------------------------------------------------------------------------


def test_ready_sort_key_is_rank_then_id() -> None:
    item = _item(id="li-z", rank="a5")
    assert ready_sort_key(item) == ("a5", "li-z")


def test_ready_sort_key_orders_by_rank_then_id() -> None:
    a = _item(id="li-b", rank="a1")
    b = _item(id="li-a", rank="a2")
    c = _item(id="li-c", rank="a1")
    ordered = sorted([b, a, c], key=ready_sort_key)
    # rank "a1" sorts before "a2"; within "a1", id "li-b" before "li-c".
    assert [w.id for w in ordered] == ["li-b", "li-c", "li-a"]
