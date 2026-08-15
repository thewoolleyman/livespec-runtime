---
topic: awaits-scope-override-field
author: claude-code
created_at: 2026-08-15T10:15:00Z
---

## Proposal: Ratify the `awaits_scope_override` field on `WorkItem`, and correct the stale field count/list it sits beside

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Two coordinated fixes to the same bullet in `### livespec_runtime.work_items.types`: (1) ratify a new `awaits_scope_override: bool = False` optional-on-read field on `WorkItem` — a materialized current-state signal backed by the `awaits-scope-override` beads label, needed by consumer `livespec_orchestrator_beads_fabro`; (2) correct the bullet's field count ("Twenty fields") and its optional-field enumeration, both of which are ALREADY stale independent of this proposal — the live dataclass has had `acceptance_criteria`, `notes`, `factory_safety`, and `review_requirement` for some time, none of which the ratified bullet lists.

### Motivation

Discovered 2026-08-15 while root-causing a cross-repo pin-staleness defect: `livespec_orchestrator_beads_fabro`'s vendored copy of this repo's `types.py` was hand-patched to add `awaits_scope_override` directly, in violation of the read-only vendoring rule, because that consumer needed the field and this repo never had it. Confirmed absent from this repo at every tagged release through the latest (`v0.19.0`) and at current `origin/master`. Since `WorkItem`'s schema is ratified spec content here (this repo owns the normative copy per the bullet's own closing sentence), adding the field to code without ratifying it here first is exactly the shape of defect this fleet's vendoring discipline exists to prevent.

While drafting the field addition, the target bullet's own field count and enumeration were re-derived by hand against the live dataclass (`livespec_runtime/work_items/types.py`) rather than trusted, per this fleet's standing clause-lockstep discipline. The ratified text says "Twenty fields" and lists only five optional-on-read fields; the live dataclass has NINE optional-on-read fields before this proposal's addition (24 total), meaning the ratified count and list were already wrong, unrelated to this change. Since this proposal edits that exact sentence, both defects are fixed together rather than compounding a third inaccuracy on top of two existing ones.

### Proposed Changes

In `SPECIFICATION/contracts.md`, section `### livespec_runtime.work_items.types`, replace:

```
- `WorkItem` — frozen, slotted, kw-only dataclass: the unified
  work-item record shared by every impl-plugin store. **Twenty fields.**
  Required (no default), in order: `id: str`, `type: WorkItemType`,
  `status: WorkItemStatus`, `title: str`, `description: str`,
  `origin: Origin`, `gap_id: str | None`, `rank: str`,
  `assignee: str | None`, `depends_on: tuple[DependsOnRaw, ...]`,
  `captured_at: str`, `resolution: Resolution | None`,
  `reason: str | None`, `audit: AuditRecord | None`,
  `superseded_by: str | None`. Optional-on-read (defaulted `= None`,
  written explicitly on append): `spec_commitment_hint: str | None`,
  `supersedes: str | None`, `admission_policy: AdmissionPolicy | None`,
  `acceptance_policy: AcceptancePolicy | None`,
  `blocked_reason: StoredBlockedReason | None`. The optional-on-read
  fields read back as the default (`None`) for legacy records lacking
  them. The record schema is codified HERE, in this repo's own
  `### livespec_runtime.work_items.types`; livespec CORE's
  `SPECIFICATION/` delegates the work-item schema to the runtime +
  orchestrator spec trees and hosts no normative copy of it.
```

with:

```
- `WorkItem` — frozen, slotted, kw-only dataclass: the unified
  work-item record shared by every impl-plugin store. **Twenty-five
  fields.** Required (no default), in order: `id: str`, `type: WorkItemType`,
  `status: WorkItemStatus`, `title: str`, `description: str`,
  `origin: Origin`, `gap_id: str | None`, `rank: str`,
  `assignee: str | None`, `depends_on: tuple[DependsOnRaw, ...]`,
  `captured_at: str`, `resolution: Resolution | None`,
  `reason: str | None`, `audit: AuditRecord | None`,
  `superseded_by: str | None`. Optional-on-read (defaulted `= None`
  unless noted, written explicitly on append), in order:
  `spec_commitment_hint: str | None`, `acceptance_criteria: str | None`,
  `notes: str | None`, `supersedes: str | None`,
  `admission_policy: AdmissionPolicy | None`,
  `acceptance_policy: AcceptancePolicy | None`,
  `blocked_reason: StoredBlockedReason | None`,
  `factory_safety: FactorySafety | None`,
  `review_requirement: ReviewRequirement | None`,
  `awaits_scope_override: bool = False`. Every optional-on-read field
  reads back as its default (`None`, or `False` for
  `awaits_scope_override`) for a legacy record lacking it.
  `awaits_scope_override` is a materialized current-state signal,
  backed by the `awaits-scope-override` beads label in the beads
  substrate — consumer `livespec_orchestrator_beads_fabro` sets it to
  reflect that label. The record schema is codified HERE, in this
  repo's own `### livespec_runtime.work_items.types`; livespec CORE's
  `SPECIFICATION/` delegates the work-item schema to the runtime +
  orchestrator spec trees and hosts no normative copy of it.
```

No heading is added, changed, or removed.
