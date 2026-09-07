---
topic: ready-sort-key-aging-signature
author: claude-opus-5
created_at: 2026-09-07T15:52:00Z
spec_commitments:
  impl_followups:
    - id_hint: ready-sort-key-aging-signature-carrier-close
      description: |
        The carrier work-item closes on ratification; no product .py changes are owed, because the shipped code is already correct and is the authority this proposal defers to. Verify by re-reading the ratified bullet against livespec_runtime/work_items/lifecycle.py's ready_sort_key factory and its _ReadySortKey key tuple after the revise pass.
    - id_hint: bda-ready-sort-key-scenario-unblocked
      description: |
        livespec-runtime-bda's ready_sort_key scenario is gated on this ratification. Once it lands, scenarios-github-auth-and-work-items may be revised; that proposal is OLDER by creation time, so this one MUST be ratified with --only-topic ready-sort-key-aging-signature first.
---

## Proposal: ready-sort-key-aging-signature

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Correct `contracts.md` §"Module-level public surface" → `livespec_runtime.work_items.lifecycle` so its `ready_sort_key` bullet declares the aging-aware factory the tree actually ships, instead of the retired `ready_sort_key(item: WorkItem) -> tuple[...]` shape. Impl→spec drift only: the code is the authority and is not touched.

### Motivation

`livespec-runtime-pi3` landed the aging-aware equal-rank tiebreak in commit `b678542` ("feat(work_items): aging-aware ready_sort_key equal-rank tiebreak") on 2026-09-07. That changeset touched `livespec_runtime/work_items/lifecycle.py`, `tests/livespec_runtime/work_items/test_lifecycle.py` and a `CLAUDE.md`, and did NOT touch `SPECIFICATION/contracts.md`. The ratified bullet therefore still declares a single-positional-argument callable returning a tuple, while the shipped symbol is a keyword-only FACTORY returning a callable:

```
def ready_sort_key(
    *,
    now: datetime,
    ready_since_lookup: _ReadySinceLookup | None = None,
    ready_aging_threshold_hours: float = _DEFAULT_READY_AGING_THRESHOLD_HOURS,
) -> Callable[[WorkItem], _ReadySortKeyTuple]:
```

with `_ReadySinceLookup = Callable[[str], datetime | None]`, `_ReadySortKeyTuple = tuple[str, int, float, str]`, `_DEFAULT_READY_AGING_THRESHOLD_HOURS = 24.0`, `_AGED_TIER = 0`, `_UNAGED_TIER = 1` and `_NO_AGE_ORDER = 0.0` (`lifecycle.py:69-92,184-252`).

This is the same defect class as `livespec-runtime-zvj`, which corrected three `github_auth` signatures the tree had already moved to the Result/IOResult railway: prose that a consumer could read and then "fix" three working call sites to match. It was surfaced by the same mechanism — a mechanical re-check of `livespec-runtime-bda`'s scenario citations against the tree found that the unit-tier test `bda` cited, `test_ready_sort_key_orders_by_rank_then_id`, no longer exists. The code is the authority; only the prose moves.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"Module-level public surface", subsection `### `livespec_runtime.work_items.lifecycle``, the bullet that currently reads:

```
- `ready_sort_key(item: WorkItem) -> tuple[...]` — the single canonical
  ranking key both `next` and the Dispatcher compose. Lead key switches
  from `priority` to **`rank`**, then `id` as the deterministic
  tie-break. The old `priority → origin → captured_at` heuristic is
  retired.
```

MUST be replaced, verbatim, by:

```
- `ready_sort_key(*, now: datetime, ready_since_lookup: Callable[[str],
  datetime | None] | None = None, ready_aging_threshold_hours: float =
  24.0) -> Callable[[WorkItem], tuple[str, int, float, str]]` — a
  FACTORY for the single canonical ready ordering key both `next` and
  the Dispatcher compose. Each calls it ONCE per pass and hands the
  result to `sorted(..., key=...)`, so there is no dispatcher-local
  sort key that can drift from this one. The composed key is
  `(rank, aging tier, ready-instant order, id)`. `rank` stays the
  PRIMARY key: the aging tiebreak is strictly WITHIN a rank tier and
  MUST NOT promote an item across tiers, so a higher-`rank` item is
  never overtaken by a lower-`rank` aged one. An item that has been
  ready LONGER than `ready_aging_threshold_hours` sorts into the aged
  tier, ahead of its equal-rank newer siblings, ordered by ready
  instant ASCENDING so the longest wait goes first; every other item
  carries a constant in that position and keeps the deterministic `id`
  lexicographic tie-break. `ready_since_lookup` is the ONLY age input
  and MUST resolve the DURABLE, clone-independent `ready_since`
  instant; an item whose instant is unknowable — the lookup returns
  `None`, or no lookup was injected — takes NO age advantage, so
  omitting the lookup degrades cleanly to the previous `(rank, id)`
  ordering rather than to an arbitrary one. Naive datetimes, whether
  `now` or a looked-up instant, MUST be read as UTC, the durable
  store's own convention. The old `priority → origin → captured_at`
  heuristic is retired.
```

No other clause changes, and no product code changes: the shipped implementation already satisfies every sentence above, and this proposal exists only because the prose was left behind.
