---
topic: workitem-carries-rework-pending
author: claude-opus-5-5
created_at: 2026-10-24T16:05:36Z
---

## Proposal: WorkItem carries rework_pending as an optional-on-read field

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Add `rework_pending: bool = False` to `WorkItem`'s optional-on-read fields in `### livespec_runtime.work_items.types`, immediately after `awaits_scope_override`, in the same shape. It is a materialized current-state signal backed by the `rework:pending` beads label, and it reads back False for a legacy record lacking it. The field count goes from twenty-five to twenty-six, and the legacy-defaults scenario gains `rework_pending is False`.

### Motivation

livespec-orchestrator-beads-fabro has carried `rework_pending: bool = False` as a local patch in its VENDORED copy of this library since its commit 74a97bf9 (2026-08-28, "feat(dispatcher): stamp and materialize the rework:pending marker"), so every re-vendor carries it by hand. Measured 2026-10-21 on work-item livespec-runtime-gfhy2a: none of v0.20.0, v0.27.0 or v0.28.0 of this repository defines the field, and the vendored tree differs from v0.27.0 only in that field and its docstring. gfhy2a, which implements the field upstream, is held at backlog under a governance hold because it changes this repository's ratified WorkItem field list, so it is spec-change tier and needs this proposal ratified before dispatch. The generalization target is the existing `awaits_scope_override` entry in the same field list, which already states the shape this field takes: an optional-on-read boolean, default False, materialized from a beads label by the orchestrator. The proposal therefore extends that one sentence pattern rather than adding a new clause.

### Proposed Changes

Two edits that land in one revision. No `## ` heading is added, changed or removed.

**1. `SPECIFICATION/contracts.md`, `### livespec_runtime.work_items.types`, the `WorkItem` bullet.**

(a) Replace `**Twenty-five
  fields.**` with `**Twenty-six
  fields.**`.

(b) In the optional-on-read list, replace

```
  `review_requirement: ReviewRequirement | None`,
  `awaits_scope_override: bool = False`. Every optional-on-read field
  reads back as its default (`None`, or `False` for
  `awaits_scope_override`) for a legacy record lacking it.
```

with

```
  `review_requirement: ReviewRequirement | None`,
  `awaits_scope_override: bool = False`, `rework_pending: bool = False`.
  Every optional-on-read field reads back as its default (`None`, or
  `False` for `awaits_scope_override` and `rework_pending`) for a legacy
  record lacking it.
```

(c) Immediately after the sentence that ends `consumer \`livespec_orchestrator_beads_fabro\` sets it to
  reflect that label.`, insert the sentence:

```
  `rework_pending` is likewise a materialized current-state signal,
  backed by the `rework:pending` beads label — the same consumer sets
  it to reflect that label.
```

The rest of the bullet, including the sentence beginning "The record schema is codified HERE", is unchanged.

**2. `SPECIFICATION/scenarios.md`, the scenario "a legacy record reads its optional-on-read fields back as their defaults".** Replace its last step

```
And awaits_scope_override is False
```

with

```
And awaits_scope_override is False
And rework_pending is False
```
