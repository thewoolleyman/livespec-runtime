# tests/livespec_runtime/work_items/

Mirrors `livespec_runtime/work_items/` one-to-one. One test module per
source module under `livespec_runtime/work_items/`:

- `test_types.py` — the unified `WorkItem` model + `AuditRecord` +
  the schema enums/aliases (construction, the `supersedes` default,
  frozenness).
- `test_reduce.py` — the canonical PURE head reduction: per-record
  identity stability, the degenerate one-record-per-id case, a genuine
  out-of-order supersession chain (deterministic head selection +
  `(captured_at, identity)` tie-break), divergent-head detection, and
  the `random_id_suffix` format.
- `test_store.py` — structural conformance to the `WorkItemStore`
  `typing.Protocol` (a thin in-memory facade, like a consumer's, that
  the Protocol accepts at type-check and runtime).

Assertions are BEHAVIORAL — they exercise the real reduction
semantics, not smoke imports.
