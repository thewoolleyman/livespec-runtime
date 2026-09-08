"""Consumer-tier scenario tests: the lane authority and the rank ordering key.

Covers NINE of the thirty-two `## Scenario:` headings ratified as v025 in
`SPECIFICATION/scenarios.md` — the three `lane_of` scenarios, the
sibling-dependency fail-closed rule, the `is_item_ready` / `lane_of`
agreement, the aging-aware `ready_sort_key`, and the three
`livespec_runtime.work_items.rank` scenarios.

The consumer here is an orchestrator: it holds an in-memory index of the
records it read, parses its `.livespec.jsonc` `cross_repo_targets` block into
a manifest, injects the sibling-status resolver it alone can supply, and asks
the shared lane authority what to render. Every name imported below is
ratified in `SPECIFICATION/contracts.md` section "Module-level public
surface"; all resolution stays OFFLINE (local + sibling entries only, so no
`gh` shell-out is reachable).
"""

import string
from datetime import datetime, timedelta, timezone

from livespec_runtime.cross_repo.types import (
    CrossRepoManifest,
    RefStatus,
    parse_cross_repo_manifest,
)
from livespec_runtime.work_items.lifecycle import (
    Lane,
    is_item_ready,
    lane_of,
    ready_sort_key,
)
from livespec_runtime.work_items.rank import BOTTOM_SENTINEL, key_between, n_keys_between
from livespec_runtime.work_items.types import (
    DependsOnRaw,
    StoredBlockedReason,
    WorkItem,
    WorkItemStatus,
)

__all__: list[str] = []

_SIBLING_REPO = "livespec"
_SIBLING_ITEM = "li-e7h6ki"
_SIBLING_ENTRY: DependsOnRaw = {
    "kind": "sibling_work_item",
    "repo": _SIBLING_REPO,
    "work_item_id": _SIBLING_ITEM,
}

# The manifest a consumer parses from its `.livespec.jsonc`; it DECLARES the
# sibling repo, which the sibling scenario below shows is load-bearing.
_MANIFEST = parse_cross_repo_manifest(
    parsed={_SIBLING_REPO: {"github_url": "https://github.com/thewoolleyman/livespec"}}
)
_EMPTY_MANIFEST = CrossRepoManifest(targets={})

_NOW = datetime(2026, 9, 7, 0, 0, tzinfo=timezone.utc)
_READY_AGING_THRESHOLD_HOURS = 24


def _item(
    *,
    id: str,
    status: WorkItemStatus = "ready",
    rank: str = "a0",
    depends_on: tuple[DependsOnRaw, ...] = (),
    blocked_reason: StoredBlockedReason | None = None,
) -> WorkItem:
    return WorkItem(
        id=id,
        type="task",
        status=status,
        title="Title",
        description="Description",
        origin="freeform",
        gap_id=None,
        rank=rank,
        assignee=None,
        depends_on=depends_on,
        captured_at="2026-09-01T00:00:00Z",
        resolution=None,
        reason=None,
        audit=None,
        superseded_by=None,
        blocked_reason=blocked_reason,
    )


class _RecordingSiblingLookup:
    """The resolver an orchestrator injects, recording whether it was consulted."""

    def __init__(self, *, status: RefStatus) -> None:
        self.status = status
        self.calls: list[tuple[str, str]] = []

    def __call__(self, repo: str, work_item_id: str) -> RefStatus:
        self.calls.append((repo, work_item_id))
        return self.status


# ===========================================================================
# `lane_of` — the single lane authority
# ===========================================================================


def test_lane_of_overlays_blocked_dependency_on_a_ready_item_with_an_open_dependency() -> None:
    """Covers scenario "lane_of overlays blocked/dependency on a ready item with an open dependency"."""
    item = _item(id="li-a", depends_on=("li-dep",))
    open_dependency = _item(id="li-dep", status="active")
    open_index = {"li-a": item, "li-dep": open_dependency}

    assert lane_of(item=item, index=open_index, manifest=_EMPTY_MANIFEST) == Lane(
        name="blocked", reason="dependency"
    )

    done_index = {"li-a": item, "li-dep": _item(id="li-dep", status="done")}

    assert lane_of(item=item, index=done_index, manifest=_EMPTY_MANIFEST) == Lane(
        name="ready", reason=None
    )


def test_lane_of_renders_a_stored_blocked_item_with_its_stored_reason() -> None:
    """Covers scenario "lane_of renders a stored blocked item with its stored reason".

    The derived `dependency` overlay applies to stored-`ready` items only, so
    a stored-`blocked` item keeps its stored reason even while it also has an
    open dependency.
    """
    needs_human = _item(id="li-a", status="blocked", blocked_reason="needs-human")
    infra = _item(id="li-b", status="blocked", blocked_reason="infra-external")
    with_open_dependency = _item(
        id="li-c", status="blocked", blocked_reason="needs-human", depends_on=("li-dep",)
    )
    index = {
        "li-a": needs_human,
        "li-b": infra,
        "li-c": with_open_dependency,
        "li-dep": _item(id="li-dep", status="active"),
    }

    assert lane_of(item=needs_human, index=index, manifest=_EMPTY_MANIFEST) == Lane(
        name="blocked", reason="needs-human"
    )
    assert lane_of(item=infra, index=index, manifest=_EMPTY_MANIFEST) == Lane(
        name="blocked", reason="infra-external"
    )
    assert lane_of(item=with_open_dependency, index=index, manifest=_EMPTY_MANIFEST) == Lane(
        name="blocked", reason="needs-human"
    )


def test_lane_of_leaves_every_other_stored_state_as_its_own_lane_with_no_reason() -> None:
    """Covers scenario "lane_of leaves every other stored state as its own lane with no reason"."""
    states: tuple[WorkItemStatus, ...] = (
        "backlog",
        "pending-approval",
        "active",
        "acceptance",
        "done",
    )

    for state in states:
        item = _item(id="li-a", status=state)
        assert lane_of(item=item, index={"li-a": item}, manifest=_EMPTY_MANIFEST) == Lane(
            name=state, reason=None
        )


# ===========================================================================
# Cross-repo readiness
# ===========================================================================


def test_an_unresolved_sibling_dependency_fails_closed_while_a_missing_local_id_does_not() -> None:
    """Covers scenario "an unresolved sibling_work_item dependency fails closed while a missing local id does not block".

    ⚠️ THE MANIFEST GIVEN IS LOAD-BEARING, AND THE THIRD LEG BELOW IS WHAT
    PROVES IT. `_resolve_sibling_work_item` short-circuits to
    `RefStatus.UNKNOWN` whenever the repo is absent from `manifest.targets`,
    BEFORE the injected lookup is consulted at all. A version of this test
    that skipped the manifest Given would still see its CLOSED leg "pass" —
    but via that early return rather than via a resolved sibling, i.e. for
    entirely the wrong reason. The recorder makes the difference observable:
    with the repo declared the lookup IS called, and without it the call log
    stays empty while the item stays blocked.
    """
    item = _item(id="li-a", depends_on=(_SIBLING_ENTRY,))
    index = {"li-a": item}

    unknown = _RecordingSiblingLookup(status=RefStatus.UNKNOWN)
    assert (
        is_item_ready(item=item, index=index, manifest=_MANIFEST, sibling_status_lookup=unknown)
        is False
    )
    assert unknown.calls == [(_SIBLING_REPO, _SIBLING_ITEM)]

    closed = _RecordingSiblingLookup(status=RefStatus.CLOSED)
    assert (
        is_item_ready(item=item, index=index, manifest=_MANIFEST, sibling_status_lookup=closed)
        is True
    )
    assert closed.calls == [(_SIBLING_REPO, _SIBLING_ITEM)]

    unconsulted = _RecordingSiblingLookup(status=RefStatus.CLOSED)
    assert (
        is_item_ready(
            item=item,
            index=index,
            manifest=_EMPTY_MANIFEST,
            sibling_status_lookup=unconsulted,
        )
        is False
    )
    assert unconsulted.calls == []

    orphan = _item(id="li-b", depends_on=("li-missing",))
    assert is_item_ready(item=orphan, index={"li-b": orphan}, manifest=_MANIFEST) is True


def test_is_item_ready_agrees_with_lane_of_by_construction() -> None:
    """Covers scenario "is_item_ready agrees with lane_of by construction"."""
    blocked_dependency = _item(id="li-a", depends_on=("li-dep",))
    plain_ready = _item(id="li-b")
    stored_blocked = _item(id="li-c", status="blocked", blocked_reason="needs-human")
    sibling_blocked = _item(id="li-d", depends_on=(_SIBLING_ENTRY,))
    index = {
        "li-a": blocked_dependency,
        "li-b": plain_ready,
        "li-c": stored_blocked,
        "li-d": sibling_blocked,
        "li-dep": _item(id="li-dep", status="active"),
        "li-e": _item(id="li-e", status="done"),
    }
    lookup = _RecordingSiblingLookup(status=RefStatus.CLOSED)
    observed: set[str] = set()

    for item in index.values():
        lane = lane_of(item=item, index=index, manifest=_MANIFEST, sibling_status_lookup=lookup)
        observed.add(lane.name)
        assert is_item_ready(
            item=item, index=index, manifest=_MANIFEST, sibling_status_lookup=lookup
        ) is (lane.name == "ready")

    # Non-vacuity: the agreement was exercised on both sides of the predicate.
    assert {"ready", "blocked"} <= observed


# ===========================================================================
# The single canonical ready ordering key
# ===========================================================================


def test_ready_sort_key_orders_by_rank_then_an_aging_tier_within_that_rank_then_id() -> None:
    """Covers scenario "ready_sort_key orders by rank, then an aging tier within that rank, then id"."""
    top = _item(id="z", rank="a0")
    bee = _item(id="b", rank="a1")
    ay = _item(id="a", rank="a1")

    plain = ready_sort_key(now=_NOW)

    assert [item.id for item in sorted([bee, ay, top], key=plain)] == ["z", "a", "b"]

    # `b` has waited longest and `a` is also past the 24h default bound, so
    # the aging tier REVERSES the id tie-break they would otherwise take —
    # an ordering that can only arise if the age really decided it.
    aged_since = {
        "b": _NOW - timedelta(hours=100),
        "a": _NOW - timedelta(hours=30),
    }
    aging = ready_sort_key(now=_NOW, ready_since_lookup=aged_since.get)

    ordered = [item.id for item in sorted([ay, bee, top], key=aging)]

    # `z` is un-aged (its instant is unknowable) yet still leads: rank stays
    # the PRIMARY key, so an aged item is never promoted across a rank tier.
    assert ordered == ["z", "b", "a"]
    assert (
        ready_sort_key(
            now=_NOW,
            ready_since_lookup=aged_since.get,
            ready_aging_threshold_hours=_READY_AGING_THRESHOLD_HOURS,
        )(bee)[0]
        == "a1"
    )

    # An item whose ready instant is unknowable takes NO age advantage and
    # keeps the deterministic id tie-break.
    ex = _item(id="x", rank="a2")
    why = _item(id="y", rank="a2")
    assert [item.id for item in sorted([why, ex], key=aging)] == ["x", "y"]

    # Mixed awareness in both directions is read as UTC rather than failing.
    naive_since = {
        "b": datetime(2026, 9, 2, 0, 0),
        "a": datetime(2026, 9, 5, 12, 0),
    }
    aware_now = ready_sort_key(now=_NOW, ready_since_lookup=naive_since.get)
    naive_now = ready_sort_key(now=datetime(2026, 9, 7, 0, 0), ready_since_lookup=aged_since.get)
    assert [item.id for item in sorted([ay, bee], key=aware_now)] == ["b", "a"]
    assert [item.id for item in sorted([ay, bee], key=naive_now)] == ["b", "a"]


# ===========================================================================
# The fractional-index rank surface
# ===========================================================================


def test_key_between_yields_a_rank_key_strictly_between_its_neighbors() -> None:
    """Covers scenario "key_between yields a rank key strictly between its neighbors, with None as an open end"."""
    first = key_between(a=None, b=None)
    second = key_between(a=first, b=None)
    assert first < second

    middle = key_between(a=first, b=second)

    assert first < middle < second
    assert key_between(a=middle, b=None) > middle
    assert key_between(a=None, b=middle) < middle


def test_n_keys_between_yields_n_evenly_spaced_sorted_keys() -> None:
    """Covers scenario "n_keys_between yields n evenly spaced sorted keys"."""
    low = key_between(a=None, b=None)
    high = key_between(a=low, b=None)

    keys = n_keys_between(a=low, b=high, n=5)

    assert len(keys) == 5
    assert len(set(keys)) == 5
    assert keys == sorted(keys)
    assert all(low < key < high for key in keys)
    assert n_keys_between(a=low, b=high, n=0) == []


def test_the_bottom_sentinel_sorts_strictly_after_every_real_rank_key() -> None:
    """Covers scenario "the bottom sentinel sorts strictly after every real rank key".

    The sentinel is a store-ADAPTER substitution for a legacy line lacking
    `rank`; the domain `WorkItem.rank` field never carries it, so a record
    built here carries a generated key that still sorts ahead of it.
    """
    generated = n_keys_between(a=None, b=None, n=25)

    assert all(key < BOTTOM_SENTINEL for key in generated)
    assert BOTTOM_SENTINEL not in generated
    assert set(BOTTOM_SENTINEL).isdisjoint(set(string.digits + string.ascii_letters))
    assert _item(id="li-a", rank=generated[-1]).rank < BOTTOM_SENTINEL
