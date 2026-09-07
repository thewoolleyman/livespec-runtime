"""Tests for `livespec_runtime.work_items.lifecycle`.

Exercises the single lane authority:

- `lane_of` overlay truth-table (the recommended scenarios in
  `plan/work-item-state-machine/research/01-spec-deltas.md`): stored
  `ready` + open dependency renders `blocked:dependency`; stored
  `blocked` renders its stored reason; every non-overlay state passes
  straight through;
- `is_item_ready` agrees with `lane_of(...).name == "ready"` by
  construction;
- `ready_sort_key` orders by `rank`, then by the ready-aging tiebreak,
  then by `id`;
- the dependency-blocking predicate's fail-closed + status-mapping
  branches (open / done / missing / sibling-unknown / unparseable),
  all resolved OFFLINE (local + sibling deps only — no `gh`). Note the
  deliberate asymmetry the sibling cases pin: an UNRESOLVED (`UNKNOWN`)
  sibling work-item dependency BLOCKS (fail-closed), while an
  unresolved LOCAL dependency does NOT.

Schema reference: this repo's own `SPECIFICATION/contracts.md`
§`### livespec_runtime.work_items.lifecycle`.
"""

from datetime import datetime, timedelta, timezone

import pytest

from livespec_runtime.cross_repo.types import CrossRepoManifest, CrossRepoTarget, RefStatus
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


# ---------------------------------------------------------------------------
# Scenario: a `sibling_status_lookup` IS injected (the orchestrator's job).
# Clause 2 of bd-ib-qiqz6b: a genuinely-CLOSED sibling is SATISFIED (does not
# over-block), while an OPEN sibling still blocks — now by a real resolution
# rather than the fail-closed UNKNOWN default. The lookup is called
# positionally as `(repo, work_item_id)`, matching `resolve_ref`.
# ---------------------------------------------------------------------------


def _closed_sibling_lookup(_repo: str, _work_item_id: str) -> RefStatus:
    return RefStatus.CLOSED


def _open_sibling_lookup(_repo: str, _work_item_id: str) -> RefStatus:
    return RefStatus.OPEN


_SIBLING_DEP_ITEM = {
    "kind": "sibling_work_item",
    "repo": "livespec-dev-tooling",
    "work_item_id": "x-1",
}


def test_lane_of_ready_with_closed_sibling_via_lookup_is_ready() -> None:
    item = _item(id="li-a", status="ready", depends_on=(_SIBLING_DEP_ITEM,))
    lane = lane_of(
        item=item,
        index={"li-a": item},
        manifest=SIBLING_MANIFEST,
        sibling_status_lookup=_closed_sibling_lookup,
    )
    assert lane == Lane(name="ready", reason=None)


def test_lane_of_ready_with_open_sibling_via_lookup_is_blocked_dependency() -> None:
    item = _item(id="li-a", status="ready", depends_on=(_SIBLING_DEP_ITEM,))
    lane = lane_of(
        item=item,
        index={"li-a": item},
        manifest=SIBLING_MANIFEST,
        sibling_status_lookup=_open_sibling_lookup,
    )
    assert lane == Lane(name="blocked", reason="dependency")


def test_is_item_ready_true_for_ready_with_closed_sibling_via_lookup() -> None:
    item = _item(id="li-a", status="ready", depends_on=(_SIBLING_DEP_ITEM,))
    assert (
        is_item_ready(
            item=item,
            index={"li-a": item},
            manifest=SIBLING_MANIFEST,
            sibling_status_lookup=_closed_sibling_lookup,
        )
        is True
    )


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
# Scenario: ready_sort_key orders by rank, then the ready-aging tiebreak,
# then id.
#
# `ready_sort_key` is a FACTORY (`next` and the Dispatcher both call it to
# compose ONE ordering). Its only age input is the injected
# `ready_since_lookup`, which resolves the DURABLE `ready_since` instant —
# there is no machine-local dispatch journal at this layer and no way to
# smuggle one in, which is what the no-lookup case below pins.
# ---------------------------------------------------------------------------

NOW = datetime(2026, 9, 7, 0, 0, tzinfo=timezone.utc)

# li-c has waited longest, li-b is past the 24h bound too, li-a is fresh.
# The ids are chosen so lexicographic order is the EXACT REVERSE of the
# aging order — an assertion that passes only if aging really decided.
_READY_SINCE = {
    "li-c": NOW - timedelta(hours=100),
    "li-b": NOW - timedelta(hours=30),
    "li-a": NOW - timedelta(hours=1),
}


def _ready_since_lookup(work_item_id: str) -> datetime | None:
    return _READY_SINCE.get(work_item_id)


def test_ready_sort_key_without_lookup_orders_by_rank_then_id() -> None:
    # No durable ready instant is resolvable, so every item is un-aged and
    # the ordering degrades exactly to the previous `(rank, id)` key.
    a = _item(id="li-b", rank="a1")
    b = _item(id="li-a", rank="a2")
    c = _item(id="li-c", rank="a1")
    ordered = sorted([b, a, c], key=ready_sort_key(now=NOW))
    # rank "a1" sorts before "a2"; within "a1", id "li-b" before "li-c".
    assert [w.id for w in ordered] == ["li-b", "li-c", "li-a"]


def test_ready_sort_key_is_rank_then_unaged_tier_then_id_without_lookup() -> None:
    item = _item(id="li-z", rank="a5")
    assert ready_sort_key(now=NOW)(item) == ("a5", 1, 0.0, "li-z")


def test_ready_sort_key_orders_aged_equal_rank_items_ahead_of_newer_ones() -> None:
    # All three share rank "a1", so only the tiebreak can reorder them.
    items = [_item(id=item_id, rank="a1", status="ready") for item_id in ("li-a", "li-b", "li-c")]
    ordered = sorted(items, key=ready_sort_key(now=NOW, ready_since_lookup=_ready_since_lookup))
    # li-c (100h) and li-b (30h) are past the 24h bound and lead, longest
    # wait first; li-a (1h) is not yet aged and falls behind both, even
    # though its id sorts first.
    assert [w.id for w in ordered] == ["li-c", "li-b", "li-a"]


def test_ready_sort_key_keeps_id_tiebreak_for_equal_rank_items_within_the_bound() -> None:
    # Both are ready, neither is past the 24h bound: id decides, and the
    # older-but-not-yet-aged item gets no head start.
    fresh = {"li-z": NOW - timedelta(hours=23), "li-a": NOW - timedelta(hours=1)}
    items = [_item(id=item_id, rank="a1", status="ready") for item_id in ("li-z", "li-a")]
    ordered = sorted(
        items,
        key=ready_sort_key(now=NOW, ready_since_lookup=fresh.get),
    )
    assert [w.id for w in ordered] == ["li-a", "li-z"]


def test_ready_sort_key_gives_an_unknowable_ready_instant_no_age_advantage() -> None:
    # "li-a" has no resolvable ready instant. Against a same-rank item that
    # is equally un-aged it keeps the plain id tiebreak, and against an aged
    # same-rank item it does NOT lead — the unknowable instant buys nothing.
    known = {"li-z": NOW - timedelta(hours=100)}
    unknowable = _item(id="li-a", rank="a1", status="ready")
    aged = _item(id="li-z", rank="a1", status="ready")
    other_unknowable = _item(id="li-b", rank="a1", status="ready")
    key = ready_sort_key(now=NOW, ready_since_lookup=known.get)
    assert [w.id for w in sorted([other_unknowable, unknowable], key=key)] == ["li-a", "li-b"]
    assert [w.id for w in sorted([unknowable, aged], key=key)] == ["li-z", "li-a"]


def test_ready_sort_key_never_promotes_an_aged_item_across_rank_tiers() -> None:
    # li-c has waited 100h but ranks below li-a, which is fresh. `rank` is
    # the primary key, so the aged item must NOT overtake it.
    higher_rank_fresh = _item(id="li-a", rank="a1", status="ready")
    lower_rank_aged = _item(id="li-c", rank="a2", status="ready")
    ordered = sorted(
        [lower_rank_aged, higher_rank_fresh],
        key=ready_sort_key(now=NOW, ready_since_lookup=_ready_since_lookup),
    )
    assert [w.id for w in ordered] == ["li-a", "li-c"]


def test_ready_sort_key_honors_a_non_default_aging_bound() -> None:
    # The bound is the orchestrator's `dispatcher.ready_aging_threshold_hours`
    # value passed through: at 1h, li-a's 1h wait is not PAST the bound while
    # li-b's 30h wait is, so li-b leads despite the later id.
    items = [_item(id=item_id, rank="a1", status="ready") for item_id in ("li-a", "li-b")]
    ordered = sorted(
        items,
        key=ready_sort_key(
            now=NOW,
            ready_since_lookup=_ready_since_lookup,
            ready_aging_threshold_hours=1.0,
        ),
    )
    assert [w.id for w in ordered] == ["li-b", "li-a"]


def test_ready_sort_key_reads_naive_ready_instants_as_utc() -> None:
    # A store handing back naive timestamps must order identically to one
    # handing back aware ones, rather than failing on mixed-awareness
    # arithmetic. Both the clock and the instants are naive here.
    naive_now = datetime(2026, 9, 7, 0, 0)
    naive = {
        "li-z": naive_now - timedelta(hours=100),
        "li-a": naive_now - timedelta(hours=1),
    }
    items = [_item(id=item_id, rank="a1", status="ready") for item_id in ("li-a", "li-z")]
    ordered = sorted(
        items,
        key=ready_sort_key(now=naive_now, ready_since_lookup=naive.get),
    )
    assert [w.id for w in ordered] == ["li-z", "li-a"]


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
