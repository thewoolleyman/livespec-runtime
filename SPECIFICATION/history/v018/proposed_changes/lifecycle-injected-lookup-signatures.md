---
topic: lifecycle-injected-lookup-signatures
author: claude-opus-5
created_at: 2026-08-26T10:46:09Z
---

## Proposal: Restate the lane_of and is_item_ready signatures and their injected-callable prose as shipped

### Target specification files

- SPECIFICATION/contracts.md

### Summary

The documented signatures for `lane_of` and `is_item_ready` both omit the fourth keyword-only parameter `sibling_status_lookup` that the shipped functions accept, and the `is_item_ready` bullet's prose claims the predicate takes an injected `local_status_lookup` when the shipped signature takes `index` and constructs the local lookup internally. Restate all three as shipped, while preserving the still-true no-back-edge property the prose exists to assert.

### Motivation

Measured on livespec-runtime master at be744d4 on 2026-08-26. `livespec_runtime/work_items/lifecycle.py` declares both `lane_of` and `is_item_ready` with four keyword-only parameters: `item`, `index`, `manifest`, and `sibling_status_lookup: Callable[[str, str], RefStatus] | None = None`. `contracts.md` documents both with only the first three. Separately, the `is_item_ready` bullet describes the function as a pure predicate that takes injected status-lookup callables naming `local_status_lookup` first; the shipped signature has no such parameter, and the local lookup is built inside the module from the in-memory index (`_LocalStatusLookup(index=index)`), which returns `UNKNOWN` for a missing id, `CLOSED` for a `done` record, and otherwise `OPEN`. Only `sibling_status_lookup` is genuinely injected. This drift was surfaced by the independent ratification review of the v017 pass and deliberately left out of it, because no proposal described it and amending a clause during a ratification would be the out-of-band spec edit the process forbids. It matters because a reader who trusts the documented signature concludes that no resolver can ever be injected into `lane_of`, hence that a `sibling_work_item` dependency can never resolve to `CLOSED`, hence -- under the per-kind blocking rule ratified in v017 -- that every sibling dependency blocks forever. The same section already documents `sibling_status_lookup` twice in prose (the injected-callables sentence and the blockquote pointing at the `resolve_ref` seam), so the signature lines are the outlier rather than the rule, and the omission reads as an oversight rather than a deliberate abbreviation. The no-back-edge property the prose asserts is NOT affected and must survive the correction: sibling status still arrives by injection and local status is still computed from an in-memory index, so there is still no `runtime` to `beads` back-edge.

### Proposed Changes

In `SPECIFICATION/contracts.md`, section `### livespec_runtime.work_items.lifecycle`, the documented signatures MUST match the shipped keyword-only parameter lists, and the injected-callable prose MUST name only the callable that is actually injected.

1. In the `lane_of` bullet, REPLACE the signature:

    `lane_of(*, item: WorkItem, index: dict[str, WorkItem], manifest: CrossRepoManifest) -> Lane`

   WITH:

    `lane_of(*, item: WorkItem, index: dict[str, WorkItem], manifest: CrossRepoManifest, sibling_status_lookup: Callable[[str, str], RefStatus] | None = None) -> Lane`

2. In the `is_item_ready` bullet, REPLACE the signature:

    `is_item_ready(*, item: WorkItem, index: dict[str, WorkItem], manifest: CrossRepoManifest) -> bool`

   WITH:

    `is_item_ready(*, item: WorkItem, index: dict[str, WorkItem], manifest: CrossRepoManifest, sibling_status_lookup: Callable[[str, str], RefStatus] | None = None) -> bool`

3. In the same `is_item_ready` bullet, REPLACE the clause:

    as a **pure predicate** that takes **injected status-lookup callables** (`local_status_lookup`, optional `sibling_status_lookup`) so there is **no `runtime → beads` back-edge**

   WITH:

    as a **pure predicate**: sibling status arrives through the optional injected `sibling_status_lookup`, and local status is derived in-module from the supplied `index` rather than injected, so there is **no `runtime → beads` back-edge**

The absent-lookup semantics MUST remain as already ratified elsewhere in this section and in `### livespec_runtime.cross_repo.resolve`: when `sibling_status_lookup` is absent, sibling dependencies resolve to `UNKNOWN`, which under the per-kind blocking rule fails closed. Nothing in this change alters behaviour; it corrects the description of a surface that has shipped since the callable was threaded through.

Only prose and signature text inside two existing bullets under an existing H3 changes. No `## ` heading is added, changed, or removed, so `tests/heading-coverage.json` requires no co-edit.
