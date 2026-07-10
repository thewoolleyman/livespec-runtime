# L0 spec deltas — `SPECIFICATION/contracts.md` (the propose-change payload)

This is the **drafted propose-change payload**, human-readable. The
machine payload for `/livespec:propose-change` is
`02-propose-change-findings.json`. The **maintainer-owned `revise`
gate** ratifies it. Authority for every value below: the cross-repo
design of record (`02-design.md` §2/§3/§5/§6; `03-decision-log.md`
decisions 24/26/28/32/35/36/38/39/40/42/44).

All edits land under the existing `## Module-level public surface` h2.
Two new `### ` subheadings are added; one existing `### ` subheading is
rewritten; one prose drift line is corrected.

---

## Delta 1 — rewrite `### livespec_runtime.work_items.types`

**Current** (contracts.md lines ~118–141) describes a 17-field
`WorkItem` with `priority: int` and the legacy 5-value status enum, and
ends with the drifted cross-reference (see Delta 4). **Replace the
`WorkItem`, `WorkItemStatus`, and alias bullets with:**

- `WorkItem` — frozen, slotted, kw-only dataclass: the unified
  work-item record shared by every impl-plugin store. **Twenty fields.**
  Required (no default), in order: `id: str`, `type: WorkItemType`,
  `status: WorkItemStatus`, `title: str`, `description: str`,
  `origin: Origin`, `gap_id: str | None`, **`rank: str`**,
  `assignee: str | None`, `depends_on: tuple[DependsOnRaw, ...]`,
  `captured_at: str`, `resolution: Resolution | None`,
  `reason: str | None`, `audit: AuditRecord | None`,
  `superseded_by: str | None`. Optional-on-read (defaulted `= None`,
  written explicitly on append): `spec_commitment_hint: str | None`,
  `supersedes: str | None`, **`admission_policy: AdmissionPolicy | None`**,
  **`acceptance_policy: AcceptancePolicy | None`**,
  **`blocked_reason: StoredBlockedReason | None`**.
  - **`rank`** is the fractional/lexicographic ordering key — the **sole
    ordering authority** (decisions 11/12/39). Strictly required,
    non-null, no default: a field this library owns is set on every
    record it writes. Legacy pre-`rank` lines on disk read back through
    a **store-adapter bottom-sentinel** (Delta 3 / `### …work_items.rank`),
    NOT through nullability in the domain type.
  - **`priority: int` is REMOVED** (decision 39 — two order sources =
    two conflicting truths). Legacy physical lines keep `priority`
    harmlessly in append-only history; new/backfilled records omit it
    (no data scrub).
  - **`admission_policy` / `acceptance_policy` / `blocked_reason`**
    follow the blessed `… | None` optional-on-read pattern (legacy
    records read back as the default; no in-place migration). `None` =
    inherit from the nearest ancestor epic, else the system safe default
    (`manual` admission, `ai-then-human` acceptance). **`blocked_reason`
    stores ONLY `{needs-human, infra-external}`; the third reason
    `dependency` is DERIVED, never stored** (it appears only as a
    rendered `Lane.reason` — see `### …work_items.lifecycle`).
  - **`assignee: str | None` is REUSED in place** as the
    claimed-by/owner field (decision 35 — beads has no native `owner`;
    `assignee` maps 1:1 to its native field). Set by the Dispatcher on
    `admit`; **REQUIRED once `status == "active"`** (the
    `active ⟹ assignee` invariant). No new `owner` field is added.
- `WorkItemStatus` — `Literal["backlog", "pending-approval", "ready",
  "active", "acceptance", "blocked", "done"]` (the seven stored
  lifecycle states; decisions 24/32). Was
  `open/in_progress/blocked/closed/deferred`.
- `AdmissionPolicy` — `Literal["auto", "manual"]`.
- `AcceptancePolicy` — `Literal["ai-only", "human-only",
  "ai-then-human"]`.
- `StoredBlockedReason` — `Literal["needs-human", "infra-external"]`
  (the STORED reasons only; `dependency` is derived).
- `WorkItemType`, `Origin`, `Resolution` — unchanged `Literal` aliases.
- `DependsOnRaw` — unchanged.

> **Invariants (doctor-checkable; restated for the consumer):**
> `active ⟹ assignee` set; stored `blocked ⟹ blocked_reason ∈
> {needs-human, infra-external}`; reaching `ready` requires transiting
> `pending-approval` (the structural grooming gate); every live (head,
> non-superseded) record has a real, non-sentinel `rank`. These
> invariants are *enforced* by the orchestrators' `doctor` (L1), not by
> the runtime dataclass; the runtime states them as the contract.

---

## Delta 2 — new `### livespec_runtime.work_items.lifecycle`

Insert a new `### ` subheading (after `### …work_items.store`), under
`## Module-level public surface`:

- `lane_of(*, item: WorkItem, index: dict[str, WorkItem], manifest:
  CrossRepoManifest) -> Lane` — the single lane authority (net-new;
  decisions 40/42). The board lane **is** the state, with one derived
  overlay. Overlay logic: stored `ready` + any open dep →
  `Lane("blocked", "dependency")`; stored `blocked` →
  `Lane("blocked", <stored blocked_reason>)`; every other state →
  `Lane(<status>, None)`. "Open dep" reuses the `resolve_ref`/`RefStatus`
  notion: a dep blocks iff it resolves to `OPEN`, or is unparseable
  (fail-closed); `CLOSED`/`UNKNOWN` do not block — so lane and readiness
  agree by construction.
- `Lane` — frozen, slotted, kw-only dataclass: `name: LaneName`,
  `reason: BlockedReason | None` (non-None iff `name == "blocked"`).
- `LaneName` — `Literal["backlog", "pending-approval", "ready",
  "active", "acceptance", "blocked", "done"]` (the 7 rendered lanes).
- `BlockedReason` — `Literal["needs-human", "infra-external",
  "dependency"]` (the *rendered* reason; note the asymmetry vs. the
  2-valued stored `StoredBlockedReason`).
- `is_item_ready(*, item: WorkItem, index: dict[str, WorkItem],
  manifest: CrossRepoManifest) -> bool` — re-expressed as
  `lane_of(...).name == "ready"`. Relocated from the beads-fabro
  orchestrator's `commands/_cross_repo.py` as a **pure predicate** that
  takes **injected status-lookup callables** (`local_status_lookup`,
  optional `sibling_status_lookup`) so there is **no `runtime → beads`
  back-edge** (decision 42). The beads store-reading stays in the
  orchestrator.
- `ready_sort_key(item: WorkItem) -> tuple[...]` — the single canonical
  ranking key both `next` and the Dispatcher compose. Lead key switches
  from `priority` to **`rank`**, then `id` as the deterministic
  tie-break (decision 39). The old `priority → origin → captured_at`
  heuristic is retired.
- The open/closed-dependency determination (`parse_entry` /
  `_entry_blocks` / local-status-lookup construction) is lifted here too,
  reusing `resolve_ref`/`RefStatus` from `livespec_runtime.cross_repo` —
  so "open deps" is computed in exactly ONE place and the Dispatcher's
  drain order can never diverge from what `next` advertises.

> The exact callable signatures the orchestrator injects mirror the
> existing `resolve_ref(local_status_lookup=…, sibling_status_lookup=…)`
> contract (`### livespec_runtime.cross_repo.resolve`), so the
> consumer wires its beads store-reads through the same seam it already
> uses. The precise public-vs-helper split (which `_`-prefixed helpers
> are part of the surface) is a `groom`/implement detail; see
> `03-code-slices.md`.

---

## Delta 3 — new `### livespec_runtime.work_items.rank`

Insert a new `### ` subheading (after the new `…lifecycle` heading),
under `## Module-level public surface`:

- `key_between(*, a: str | None, b: str | None) -> str` — thin
  livespec-facing wrapper over the ported `generate_key_between`. `a` /
  `b` are the neighbor keys (`None` = open end); returns a fresh key
  ordering strictly between them.
- `n_keys_between(*, a: str | None, b: str | None, n: int) ->
  list[str]` — wrapper over `generate_n_keys_between`; returns `n`
  evenly-spaced keys between the neighbors (the `rebalance-ranks` /
  backfill generator).
- `BOTTOM_SENTINEL: str` — the shared bottom-sentinel a store ADAPTER
  substitutes for a legacy line lacking `rank` (decision 39). A constant
  using a char **outside** the lib's base-62 alphabet (`0-9A-Za-z`),
  e.g. `"~"` (`0x7E` > `z` `0x7A`), so it sorts strictly **after** every
  real key. The two backend facades (git-jsonl, beads) import this one
  constant; the strict `rank: str` domain type never carries it.
- `_fractional_indexing` — the PORTED CC0-1.0 module
  (`httpie/fractional-indexing-python`, the official Python port of
  `rocicorp/fractional-indexing`; stdlib-only; public
  `generate_key_between` / `generate_n_keys_between` /
  `validate_order_key`). Vendored verbatim with an attribution header;
  a `NOTICES` entry is added at the repo root (decision 38, G-1). PORT
  (not vendor) because `rank` math must live in `livespec_runtime`,
  which has no vendoring machinery and is itself copied source-only into
  every consumer's `_vendor/` tree — one file rides along
  automatically, no new machinery, no drift.

---

## Delta 4 — fix the `:131` upstream-schema drift

**Current** (contracts.md line ~131, the tail of the `WorkItem`
bullet): *"The record schema is codified upstream in
`livespec/SPECIFICATION/contracts.md`."*

**Replace with** (decision 44 — CORE hosts no such schema; the home is
THIS repo): *"The record schema is codified HERE, in this repo's own
`### livespec_runtime.work_items.types`; livespec CORE's
`SPECIFICATION/` delegates the work-item schema to the runtime +
orchestrator spec trees and hosts no normative copy of it."*

> The matching code-side drift (the `types.py` module docstring's
> "codified by livespec/SPECIFICATION/contracts.md" line) is corrected
> as part of the code slice (`03-code-slices.md`), not this spec
> propose-change.

---

## heading-coverage co-edit — reasoning (a decision point for `revise`)

The `livespec_dev_tooling.checks.heading_coverage` check tracks **only
`## ` (h2) headings** — `_extract_h2_headings` explicitly skips `### `.
All `### …work_items.*` subheadings (existing and the two new ones) live
under the **already-registered** `## Module-level public surface` h2
entry (`tests/heading-coverage.json`, `test: "TODO"`). So **no new
registry row is required for the gate to pass**, and adding granular
`### ` rows would diverge from the existing registry convention (which
has zero `### ` rows) and would not be validated by the check.

**Recommendation:** make NO `heading-coverage.json` change for L0 (the
`## Module-level public surface` TODO already covers the section at the
check's granularity). If the maintainer wants granular `### `-level
tracking, that is a `livespec-dev-tooling` tooling change, out of L0
scope — flag separately. *(The kickoff brief's "co-edit for every
`## `/`### ` heading" instruction is satisfied vacuously here: no `## `
heading is added/changed, and `### ` headings are not tracked.)*

---

## Authoring-discipline note (Gherkin scenarios) — for `revise`/`groom`

Per the propose-change authoring discipline (i) "load-bearing behavior
⇒ Gherkin scenario", `lane_of`'s derivation truth-table and `rank`'s
`key_between`/`n_keys_between` ordering are load-bearing. This L0 draft
keeps the propose-change focused on the **wire-contract surface**
(`contracts.md` API shapes a consumer vendors) and **recommends** the
following `scenarios.md` additions be authored during `revise` (or as a
groomed child), each paired to a runtime unit test:

1. `## Scenario: lane_of renders ready + open dependency as
   blocked:dependency`
2. `## Scenario: lane_of renders stored blocked with its stored reason`
3. `## Scenario: lane_of passes every non-overlay state straight through`
4. `## Scenario: ready_sort_key orders by rank then id`
5. `## Scenario: key_between returns a key strictly between neighbors`
6. `## Scenario: the bottom-sentinel sorts after every real rank key`

These are listed (not yet authored as Gherkin) so the maintainer can
confirm scope before they enter the spec — surfacing the discipline-(i)
requirement rather than silently dropping it.
