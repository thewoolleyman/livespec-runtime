# L0 groom cut — DRAFT (maintainer-owned; file nothing until approved)

The `revise` gate is **DONE** (commit `42d3d5e`, history `v008`;
`SPECIFICATION/contracts.md` ratified the L0 contract). This is the
**drafted `groom` decomposition** of epic **`livespec-runtime-l4yojx`**
into ready, dependency-layered children. **The maintainer/coordinator
owns the cut — nothing here is filed to the ledger until approval is
relayed.**

Source of the slices: `03-code-slices.md` (S1–S5). Each child carries
`spec_commitment_hint =` the matching `id_hint` from
`02-propose-change-findings.json` (`spec_commitments.impl_followups[]`),
pairing it back to the ratified propose-change.

## Dependency layering

```
layer 0:  S1 (rank)      S3 (types)         ← independent; parallel
layer 1:                 S2 (lifecycle)     ← depends on S3 (new WorkItem shape)
layer 2:  S4 (tests) ────────────┘          ← depends on S1, S2, S3
layer 3:  S5 (release)                       ← depends on S1, S2, S3, S4 (exit gate)
```

All slices target the **`livespec-runtime`** repo. All are `factory`
(autonomously dispatchable); none is `is_spec_change` (the spec already
landed via `revise`). `depends_on` below uses draft-local **titles**
(the groom handle form), resolved to minted ids at file time.

## The slices (CandidateSlice-shaped)

### S1 — `port-fractional-indexing`  ·  layer 0  ·  deps: none
- **title:** `L0/S1: port fractional-indexing + rank.py wrapper + NOTICES`
- **spec_commitment_hint:** `port-fractional-indexing`
- **scope:** Port `httpie/fractional-indexing-python` VERBATIM (CC0-1.0)
  → `livespec_runtime/work_items/_fractional_indexing.py` (attribution
  header naming upstream + commit/tag + CC0-1.0). Add `rank.py`
  (`key_between`, `n_keys_between`, `BOTTOM_SENTINEL`) and a repo-root
  `NOTICES` entry. Keyword-only args; do NOT refactor the ported module.
- **acceptance:** `key_between`/`n_keys_between` emit valid base-62 keys
  ordering strictly between neighbors; `BOTTOM_SENTINEL` sorts strictly
  after every real key (`"~" > "z"`); attribution header + `NOTICES`
  present; `just check` green. Matches ratified
  `### livespec_runtime.work_items.rank`.

### S3 — `types-schema-edits`  ·  layer 0  ·  deps: none (parallel S1)
- **title:** `L0/S3: WorkItem schema — 7-state status, +rank, −priority, policy fields`
- **spec_commitment_hint:** `types-schema-edits`
- **scope:** `livespec_runtime/work_items/types.py`: `WorkItemStatus` →
  the 7-state `Literal`; `+ rank: str` (required, no default, where
  `priority` was); `− priority: int`; add `AdmissionPolicy` /
  `AcceptancePolicy` / `StoredBlockedReason` aliases + the three
  `… | None = None` policy fields; keep `assignee` in place (document the
  `active ⟹ assignee` requirement); update `__all__`; fix the module
  docstring's `codified by livespec/SPECIFICATION/contracts.md` drift to
  point at this repo's own `### …work_items.types`.
- **acceptance:** `WorkItem` matches ratified
  `### livespec_runtime.work_items.types` (20 fields, exact order);
  `reduce.py` identity reducer stays deterministic over the new shape;
  `test_types.py` updated; `just check` + type-check green.

### S2 — `lifecycle-module`  ·  layer 1  ·  deps: S3
- **title:** `L0/S2: lifecycle.py — lane_of + relocated is_item_ready/ready_sort_key (DI)`
- **spec_commitment_hint:** `lifecycle-module`
- **deps (titles):** `L0/S3: WorkItem schema — 7-state status, +rank, −priority, policy fields`
- **scope:** Net-new `livespec_runtime/work_items/lifecycle.py`: `Lane`/
  `LaneName`/`BlockedReason`; `lane_of` (overlay per ratified spec);
  `is_item_ready` = `lane_of(...).name=="ready"` as a **pure predicate
  with INJECTED `local_status_lookup` / `sibling_status_lookup`** (no
  `runtime → beads` back-edge); `ready_sort_key` keyed on `rank` then
  `id`; the dep predicate helpers lifted from the orchestrator's
  `_cross_repo.py`, reusing `livespec_runtime.cross_repo.resolve_ref`/
  `RefStatus`. **No orchestrator-repo edits here** (the `_cross_repo.py`
  shrink is L1a, gating on the L0 release).
- **acceptance:** lane truth-table holds (the 6 scenarios in
  `01-spec-deltas.md`); `is_item_ready` agrees with `lane_of` by
  construction; `lifecycle.py` imports NO beads/orchestrator symbol;
  `just check` green. Matches ratified
  `### livespec_runtime.work_items.lifecycle`.

### S4 — `lifecycle-rank-paired-tests`  ·  layer 2  ·  deps: S1, S2, S3
- **title:** `L0/S4: paired tests + coverage completion (rank, lifecycle, types)`
- **spec_commitment_hint:** `lifecycle-rank-paired-tests`
- **deps (titles):** S1, S3, S2 titles (above).
- **scope:** Paired tests mirroring the source tree
  (`tests/livespec_runtime/work_items/test_rank.py`, `test_lifecycle.py`,
  updated `test_types.py`, `_fractional_indexing` round-trip /
  `validate_order_key`). NB: the per-module Red test rides with its impl
  in S1–S3's red-green-replay commits; **S4 is the cross-module +
  coverage-completion slice** (e.g. the lane↔readiness agreement test and
  any gap to the per-file 100% gate).
- **acceptance:** `just check-per-file-coverage` green; the 6
  recommended scenarios covered; heading/claude-md coverage green.

### S5 — `cut-runtime-release`  ·  layer 3  ·  deps: S1, S2, S3, S4  (EXIT GATE)
- **title:** `L0/S5: cut livespec-runtime release (the L0 exit gate)`
- **spec_commitment_hint:** `cut-runtime-release`
- **deps (titles):** S1, S2, S3, S4 titles.
- **scope:** The product `.py` of S1–S3 lands under `feat:`-subject
  red-green-replay commits, so release-please opens a release PR. Merge
  it, cut the tag, and bump in-repo self-refs as release-please dictates.
- **acceptance:** release-please PR merged; new `livespec-runtime` tag;
  `livespec_runtime.work_items.{lifecycle,rank}` + the new `types` shape
  importable from the released artifact. **This tag is what L1a/L1b
  vendor — the whole L1 layer gates on it.**

## Filing mechanism — a decision for the coordinator/maintainer

**Finding:** the native `groom` `file_approved_slices`
(`commands/groom.py`) **hardcodes `spec_commitment_hint=None`** (and
`CandidateSlice` has no hint field). So the native groom path **cannot**
file children that carry their `id_hint` in one step. Two ways to honor
the `spec_commitment_hint = <id_hint>` requirement:

- **Option A (recommended) — `capture-work-item` `append_work_item`
  path.** File each child via the same `append_work_item` machinery with
  `spec_commitment_hint` set explicitly, then wire the beads
  `parent-child` edge to `livespec-runtime-l4yojx` and the `depends_on`
  layering. Honors the hint natively; the cost is wiring parent + dep
  edges by hand (the orchestrator's `_beads_client` exposes
  `add_dependency(edge_type="parent-child")` and the dependency edges).
- **Option B — native `groom` then update.** Transition the epic to
  `needs-regroom`, run `file_approved_slices` (gets ready slices + dep
  edges + regroom-out for free), then `update` each filed child to set
  `spec_commitment_hint`. Two-step; relies on the update path persisting
  the hint under the current schema.

NOTE the current runtime still uses the **pre-migration** schema
(`status=open`, `priority`, no `rank`) — the children are filed under
THAT schema (the tenant migrates to the new schema in L2). The
`spec_commitment_hint` field already exists in the current schema, so
either option can set it today.

## Next step (after the coordinator relays approval)

1. File the 5 children of `livespec-runtime-l4yojx` per the approved cut
   (mechanism per the decision above), each `ready`, dep-linked by the
   layering, carrying its `spec_commitment_hint`.
2. Implement **S1–S4** via this repo's **red-green-replay** TDD
   (worktree → PR → rebase-merge; `mise exec -- git`; never
   `--no-verify`; halt + report on any hook failure).
3. Cut the **S5** `livespec-runtime` release — the L0 exit gate.
