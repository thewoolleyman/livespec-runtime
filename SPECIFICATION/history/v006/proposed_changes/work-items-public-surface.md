---
topic: work-items-public-surface
author: E2E Test
created_at: 2026-06-20T22:00:57Z
---

## Proposal: Declare livespec_runtime.work_items public surface

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add the three new H3 entries for the additive livespec_runtime.work_items.{types,reduce,store} surface under the existing "## Module-level public surface" H2 in contracts.md, declaring the WorkItem/AuditRecord model, the canonical supersession reducer, and the WorkItemStore Protocol as part of the library's stable v1 public API.

### Motivation

W7 step 4 (livespec-4jsi) lifts the duplicated WorkItem model, the canonical supersession reducer, and the WorkItemStore Protocol out of the impl-plugins into livespec-runtime as a shared surface. Because livespec-runtime dogfoods livespec, every stable public-API addition must be declared via the propose-change -> revise lifecycle (self-application rule) before the code extraction lands.

### Proposed Changes

Append three new H3 entries to SPECIFICATION/contracts.md, AFTER the existing `### livespec_runtime.cross_repo.resolve` entry and BEFORE the next `## Resolution semantics` H2, under the existing `## Module-level public surface` H2 (no new H2 is introduced). The entries declare:

### livespec_runtime.work_items.types
- WorkItem (frozen, slotted, kw-only dataclass; sixteen fields, two defaulted/optional-on-read), AuditRecord (merge-evidence record), WorkItemStatus/WorkItemType/Origin/Resolution (Literal string aliases enumerating the schema's closed value sets), DependsOnRaw (TypeAlias str | dict[str, Any]).

### livespec_runtime.work_items.reduce
- work_item_record_identity (stable per-record sha256 identity), reduce_work_item_heads (order-independent supersession reduction to head record(s) per entity id), materialize_work_items (current-head-per-id dict), random_id_suffix (fresh six-character base32 li-<suffix> body).

### livespec_runtime.work_items.store
- WorkItemStore (typing.Protocol; structural, no inheritance) with read_work_items and append_work_item; the conformance contract every impl-plugin's work-item store satisfies via a thin per-impl facade over its backend I/O. Comments are deliberately NOT part of this contract.

The full updated contracts.md text is supplied via the revise resulting_files[] mechanism. The record schema itself is codified upstream in livespec/SPECIFICATION/contracts.md §"Work-items JSONL record schema".
