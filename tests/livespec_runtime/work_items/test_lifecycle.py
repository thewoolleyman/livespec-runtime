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
  all resolved OFFLINE (local + sibling deps only — no `gh`). Note the
  deliberate asymmetry the sibling cases pin: an UNRESOLVED (`UNKNOWN`)
  sibling work-item dependency BLOCKS (fail-closed), while an
  unresolved LOCAL dependency does NOT.

Schema reference: this repo's own `SPECIFICATION/contracts.md`
§`### livespec_runtime.work_items.lifecycle`.
"""

import pytest

from livespec_runtime.cross_repo.types import CrossRepoManifest, CrossRepoTarget
from livespec_runtime.work_items.lifecycle import (
    Lane,
    is_item_ready,
    lane_of,
    ready_sort_key,
)
from livespec_runtime.work_items.types import WorkItem

__all__: list[str] = []

EMPTY_MANIFEST = CrossRepoManifest(targets={})

# A manifest that DOES declare the sibling repo, so the sibling cases below
# exercise the `repo in manifest.targets` arm of `_resolve_sibling_work_item`
# (which still yields `UNKNOWN`, because no `sibling_status_lookup` exists at
# this layer) rather than short-circuiting on an absent target.
SIBLING_MANIFEST = CrossRepoManifest(
    targets={
        "livespec-dev-tooling": CrossRepoTarget(
            github_url="https://github.com/thewoolleyman/livespec-dev-tooling",
        )
    }
)


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
    # This is the deliberate counterpart to the sibling fail-closed rule
    # below: UNKNOWN blocks for a `sibling_work_item` entry ONLY.
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


def test_lane_of_ready_with_sibling_dep_unknown_is_blocked_dependency() -> None:
    # A sibling work-item dep resolves to UNKNOWN at this layer (no
    # runtime→beads back-edge, no network, no `sibling_status_lookup`).
    # An UNRESOLVED cross-repo blocker must FAIL CLOSED: a well-formed
    # sibling entry must never be treated as LESS blocking than a
    # malformed one, or a candidate whose cross-repo blocker is still
    # open is dispatched anyway.
    item = _item(
        id="li-a",
        status="ready",
        depends_on=(
            {
                "kind": "sibling_work_item",
                "repo": "livespec-dev-tooling",
                "work_item_id": "x-1",
            },
        ),
    )
    lane = lane_of(item=item, index={"li-a": item}, manifest=SIBLING_MANIFEST)
    assert lane == Lane(name="blocked", reason="dependency")


def test_lane_of_ready_with_sibling_dep_absent_from_manifest_is_blocked_dependency() -> None:
    # Same fail-closed rule on the other `_resolve_sibling_work_item`
    # arm: a repo absent from the manifest is equally unresolved, so it
    # equally blocks.
    item = _item(
        id="li-a",
        status="ready",
        depends_on=({"kind": "sibling_work_item", "repo": "other", "work_item_id": "x-1"},),
    )
    lane = lane_of(item=item, index={"li-a": item}, manifest=EMPTY_MANIFEST)
    assert lane == Lane(name="blocked", reason="dependency")


def test_is_item_ready_false_for_ready_with_unresolved_sibling_dep() -> None:
    # The readiness gate the dispatcher consults agrees with the lane:
    # an unresolved sibling dependency makes the item NOT a dispatch
    # candidate.
    item = _item(
        id="li-a",
        status="ready",
        depends_on=(
            {
                "kind": "sibling_work_item",
                "repo": "livespec-dev-tooling",
                "work_item_id": "x-1",
            },
        ),
    )
    assert is_item_ready(item=item, index={"li-a": item}, manifest=SIBLING_MANIFEST) is False


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


# ---------------------------------------------------------------------------
# Cross-module invariant (S4): `is_item_ready` ⇔ `lane_of(...).name == "ready"`.
#
# `is_item_ready` is DEFINED as `lane_of(...).name == "ready"`, so the two can
# never disagree. This matrix pins that agreement explicitly across the
# overlay-bearing cases (a stored-`ready` item with an open / cleared / absent
# dependency) and the non-`ready` states, so a future refactor that lets the
# readiness gate drift from the rendered board is caught here.
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    ("status", "deps", "dep_status", "blocked_reason"),
    [
        ("ready", (), None, None),  # ready, no deps → ready
        ("ready", ("li-dep",), "active", None),  # ready + open dep → blocked:dependency
        ("ready", ("li-dep",), "done", None),  # ready + cleared dep → ready
        ("ready", ("li-missing",), None, None),  # ready + UNKNOWN dep → ready
        ("backlog", (), None, None),
        ("pending-approval", (), None, None),
        ("active", (), None, None),
        ("acceptance", (), None, None),
        ("blocked", (), None, "needs-human"),
        ("done", (), None, None),
    ],
)
def test_is_item_ready_agrees_with_lane_of_by_construction(
    status: str,
    deps: tuple[str, ...],
    dep_status: str | None,
    blocked_reason: str | None,
) -> None:
    index: dict[str, WorkItem] = {}
    if dep_status is not None:
        dep = _item(id="li-dep", status=dep_status)
        index["li-dep"] = dep
    item = _item(
        id="li-a",
        status=status,
        depends_on=deps,
        blocked_reason=blocked_reason,
    )
    index["li-a"] = item
    lane = lane_of(item=item, index=index, manifest=EMPTY_MANIFEST)
    ready = is_item_ready(item=item, index=index, manifest=EMPTY_MANIFEST)
    assert ready == (lane.name == "ready")
