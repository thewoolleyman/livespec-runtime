# L0 foundation — overview and read-first chain

This is the `livespec-runtime` (L0 foundation) track of the fleet-wide
**work-item-lifecycle** epic — the deterministic work-item state machine.
L0 implements the shared core that both L1 orchestrators vendor; it is
the **critical path** (L1 code gates on the L0 release).

- **Ledger anchor (this repo's tenant):** epic
  **`livespec-runtime-l4yojx`** (`livespec-runtime` beads tenant).
- **Fleet anchor (prose reference, NOT a typed cross-tenant
  `depends_on`):** `livespec-35s3zo` in the livespec core tenant
  (decisions 41/44/45 — a cross-tenant id would dangle in the flat
  same-tenant id list and pollute the `blocked:dependency` derivation).
- **Branch / worktree for this track:** `wism-l0-foundation`.

## The reframe (load-bearing finding)

This redesign is **overwhelmingly a `livespec-runtime` + orchestrator
change; livespec CORE's own spec is barely touched** (decision 44).
CORE's `SPECIFICATION/` explicitly delegates the entire lifecycle /
schema surface to the orchestrators as NON-normative. So the L0
contract lands in **THIS repo's `SPECIFICATION/contracts.md`**, not in
CORE. The epic stays *anchored* in core, but core is the anchor, not
the work site.

## Read-first chain (cold-start)

Read in order, then execute the next action in `../handoff.md`:

1. **This file** — the slice, the anchor, the reframe.
2. `01-spec-deltas.md` — the exact `SPECIFICATION/contracts.md` deltas
   (the propose-change payload, human-readable) + the
   heading-coverage reasoning. **The maintainer-owned `revise` gate
   ratifies this.**
3. `02-propose-change-findings.json` — the ready-to-feed
   `/livespec:propose-change` findings payload for `01`.
4. `03-code-slices.md` — the code-slice breakdown. **The
   maintainer-owned `groom` gate cuts this into ready children of
   `livespec-runtime-l4yojx`.**
5. Cross-repo design of record (already on disk, authoritative):
   - `/data/projects/livespec/plan/work-item-state-machine/research/02-design.md`
     (§2 states, §3 `lane_of`, §5 `rank`, §6 schema)
   - `/data/projects/livespec/plan/work-item-state-machine/research/03-decision-log.md`
     (decisions 1–46; authoritative on any conflict)
   - `/data/projects/livespec/plan/work-item-state-machine/research/04-slice-plan.md`
     (the "L0 — livespec-runtime" section; "The reframe"; "Execution model")
   - `/data/projects/livespec/plan/work-item-state-machine/briefs/l0-runtime.md`
     (this track's kickoff brief)

## The L0 slice (what lands in this repo)

**Spec** (propose-change → `SPECIFICATION/contracts.md`; see `01`):
- `### …work_items.types` — 7-state `status` enum; `+ rank: str`
  (required, non-null, no default); `− priority: int`;
  `+ admission_policy` / `+ acceptance_policy` / `+ blocked_reason`
  (`… | None`, optional-on-read); the `active ⟹ assignee` invariant.
- new `### …work_items.lifecycle` — `lane_of` + `Lane`/`LaneName`/
  `BlockedReason`; `is_item_ready` (= `lane_of(...).name == "ready"`);
  `ready_sort_key` (keyed on `rank`); the dependency predicate moved in
  as a **pure predicate with injected status-lookup callables** (no
  `runtime → beads` back-edge — decision 42).
- new `### …work_items.rank` — the `rank.py` wrapper API, the ported
  CC0 module, the shared bottom-sentinel constant.
- Fix the `:131` upstream-schema drift (decision 44).

**Code** (this repo; see `03`): port `_fractional_indexing.py` (CC0
verbatim) + `rank.py` + `NOTICES`; net-new `lifecycle.py`; `types.py`
schema edits; the shared bottom-sentinel constant; paired tests.

**Gate:** cut a `livespec-runtime` release (a `feat:` push triggers
release-please) — the artifact L1a/L1b vendor.

## Maintainer-owned gates (do NOT auto-pass)

- **`revise`** ratifies the spec propose-change (`01`/`02`). This track
  drafts it; it does NOT auto-ratify.
- **`groom`** cuts `03` into dispatchable `ready` children of
  `livespec-runtime-l4yojx`. This track drafts the breakdown; it does
  NOT auto-file ready slices or auto-merge code past the gate.
