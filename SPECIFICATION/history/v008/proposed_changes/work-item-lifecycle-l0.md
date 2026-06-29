---
topic: work-item-lifecycle-l0
author: wism-l0-runtime
created_at: 2026-06-29T07:50:10Z
spec_commitments:
  impl_followups:
    - id_hint: port-fractional-indexing
      description: |
        Port httpie/fractional-indexing-python VERBATIM (CC0-1.0) to livespec_runtime/work_items/_fractional_indexing.py with an attribution header; add a thin rank.py wrapper (key_between / n_keys_between), the shared BOTTOM_SENTINEL constant, and a NOTICES entry at the repo root. Paired tests mirror the source tree.
    - id_hint: lifecycle-module
      description: |
        Net-new livespec_runtime/work_items/lifecycle.py: lane_of + Lane/LaneName/BlockedReason; is_item_ready re-expressed as lane_of(...).name=='ready'; ready_sort_key keyed on rank; the open/closed-dependency predicate relocated from the beads-fabro orchestrator's commands/_cross_repo.py as a PURE predicate with INJECTED status-lookup callables (no runtime->beads back-edge; decision 42), reusing resolve_ref/RefStatus.
    - id_hint: types-schema-edits
      description: |
        livespec_runtime/work_items/types.py: status -> 7-state WorkItemStatus enum; + rank: str (required non-null, no default); - priority: int; + admission_policy/acceptance_policy/blocked_reason (… | None, optional-on-read defaults); AdmissionPolicy/AcceptancePolicy/StoredBlockedReason aliases; assignee reused as claimed-by/owner (active⟹assignee invariant); correct the module-docstring 'codified by livespec/SPECIFICATION/contracts.md' drift to point at this repo's own work_items.types.
    - id_hint: lifecycle-rank-paired-tests
      description: |
        Paired tests under tests/livespec_runtime/work_items/ mirroring the new/changed modules (test_lifecycle.py, test_rank.py, _fractional_indexing tests, updated test_types.py), covering the lane_of derivation truth-table, ready_sort_key rank ordering, key_between/n_keys_between, and the bottom-sentinel sort property — per the recommended scenarios in 01-spec-deltas.md.
    - id_hint: cut-runtime-release
      description: |
        GATE: cut a livespec-runtime release (a feat: push triggers release-please) once the schema/lifecycle/rank code lands. This release artifact is what L1a (beads-fabro) and L1b (git-jsonl) vendor; the whole L1 layer gates on it.
---

## Proposal: Work-item lifecycle schema — 7-state status, required rank, policy fields, assignee-as-owner

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Rewrite `### livespec_runtime.work_items.types` for the deterministic work-item lifecycle: status becomes the 7-state enum (backlog · pending-approval · ready · active · acceptance · blocked · done); add rank: str (required, non-null, no default) as the sole ordering authority; remove priority: int; add admission_policy / acceptance_policy / blocked_reason (… | None, optional-on-read); reuse assignee in place as the claimed-by/owner field with the active⟹assignee invariant. Also correct the line-131 drift that wrongly claims the record schema is codified upstream in livespec CORE.

### Motivation

L0 foundation of the fleet-wide work-item-lifecycle epic (anchor livespec-35s3zo; runtime epic livespec-runtime-l4yojx). The WorkItem schema is the source of truth both orchestrators vendor; the lifecycle redesign (decisions 24/26/28/32/35/36/39/44) lands its schema contract HERE, not in CORE (the reframe, decision 44).

### Proposed Changes

See plan/work-item-state-machine/research/01-spec-deltas.md Delta 1 and Delta 4 for the exact bullet text. Net: WorkItem grows to twenty fields — required (no default): id, type, status, title, description, origin, gap_id, rank: str, assignee, depends_on, captured_at, resolution, reason, audit, superseded_by; optional-on-read (= None): spec_commitment_hint, supersedes, admission_policy: AdmissionPolicy | None, acceptance_policy: AcceptancePolicy | None, blocked_reason: StoredBlockedReason | None. WorkItemStatus = Literal[backlog, pending-approval, ready, active, acceptance, blocked, done]. New aliases: AdmissionPolicy = Literal[auto, manual]; AcceptancePolicy = Literal[ai-only, human-only, ai-then-human]; StoredBlockedReason = Literal[needs-human, infra-external] (the derived `dependency` reason is NEVER stored). priority: int is removed (no scrub; legacy lines keep it harmlessly in append-only history). Restate the doctor-checkable invariants (active⟹assignee; stored blocked⟹reason; reaching ready requires transiting pending-approval; every live record has a real non-sentinel rank). Replace the line-131 sentence 'The record schema is codified upstream in livespec/SPECIFICATION/contracts.md.' with a statement that the schema is codified HERE and CORE hosts no normative copy (decision 44). NO behavior is carried by prose alone; the load-bearing derivation/ordering behavior is specified in the lifecycle/rank findings + recommended scenarios.md additions (01-spec-deltas.md).

## Proposal: lane_of — the single lifecycle/lane authority (livespec_runtime.work_items.lifecycle)

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a new `### livespec_runtime.work_items.lifecycle` subheading documenting lane_of (the one pure lane authority), the Lane/LaneName/BlockedReason types, is_item_ready (re-expressed as lane_of(...).name=='ready'), ready_sort_key (keyed on rank), and the open/closed-dependency predicate relocated from the orchestrator as a pure predicate with injected status-lookup callables (no runtime->beads back-edge).

### Motivation

lane ≡ state with one derived overlay (ready + open dep -> blocked:dependency); lane_of MUST live in the runtime so Python consumers import it and the console consumes its emission (decisions 15/40). Decision 42: the consolidation moves the pure core and INJECTS backend I/O, strengthening the runtime's backend-agnosticism.

### Proposed Changes

See plan/work-item-state-machine/research/01-spec-deltas.md Delta 2 for the exact bullet text. lane_of(*, item: WorkItem, index: dict[str, WorkItem], manifest: CrossRepoManifest) -> Lane. Lane is a frozen/slotted/kw-only dataclass {name: LaneName, reason: BlockedReason | None} (reason non-None iff name=='blocked'). LaneName = the 7 rendered lanes; BlockedReason = Literal[needs-human, infra-external, dependency] (note the asymmetry vs. the 2-valued stored StoredBlockedReason). Overlay: stored ready + any open dep -> Lane('blocked','dependency'); stored blocked -> Lane('blocked', <stored reason>); every other state -> Lane(<status>, None). 'Open dep' reuses resolve_ref/RefStatus (blocks iff OPEN or unparseable; CLOSED/UNKNOWN do not block). is_item_ready and ready_sort_key relocate here from the beads-fabro orchestrator's commands/_cross_repo.py; is_item_ready becomes a pure predicate taking injected local_status_lookup (+ optional sibling_status_lookup), mirroring the existing resolve_ref callable contract.

## Proposal: rank — fractional-index ordering primitive (livespec_runtime.work_items.rank)

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a new `### livespec_runtime.work_items.rank` subheading documenting the rank.py wrapper API (key_between / n_keys_between), the ported CC0-1.0 _fractional_indexing module, and the shared BOTTOM_SENTINEL constant used by store adapters for legacy rank-less lines.

### Motivation

rank is the sole, merge-robust ordering primitive (decisions 11/38/39). The math must live in livespec_runtime (no vendoring machinery; itself copied source-only into consumers), so the reference algorithm is PORTed verbatim (CC0-1.0, attribution + NOTICES) — one file that rides along automatically into every consumer's _vendor tree.

### Proposed Changes

See plan/work-item-state-machine/research/01-spec-deltas.md Delta 3 for the exact bullet text. key_between(*, a: str | None, b: str | None) -> str and n_keys_between(*, a: str | None, b: str | None, n: int) -> list[str] wrap generate_key_between / generate_n_keys_between. BOTTOM_SENTINEL: str is a constant using a char outside the base-62 alphabet (e.g. '~', 0x7E > 'z') so it sorts strictly after every real key; the two backend facades import it for legacy rank-less lines, keeping the domain rank: str strictly non-null. _fractional_indexing is httpie/fractional-indexing-python ported verbatim with an attribution header; a NOTICES entry is added at the repo root.
