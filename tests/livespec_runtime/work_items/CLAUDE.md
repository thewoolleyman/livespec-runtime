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
- `test_rank.py` — the first-party fractional-index `rank` wrapper
  (`key_between` / `n_keys_between` / `BOTTOM_SENTINEL`); covers the
  wrapper to 100% and smoke-tests the ported algorithm through it.
- `test__fractional_indexing.py` — the verbatim-ported (coverage-omitted)
  module's own ordering + `validate_order_key` contract, pinned directly
  as a drift guard (the wrapper does not re-export `validate_order_key`).
- `test_lifecycle.py` — the single lane authority: the `lane_of` overlay
  truth-table, the `is_item_ready` ⇔ `lane_of(...).name == "ready"`
  agreement, and `ready_sort_key`'s `(rank, id)` ordering. All
  dependency resolution is exercised OFFLINE (local + manifest-absent
  deps only — no `gh`).

Assertions are BEHAVIORAL — they exercise the real reduction
semantics, not smoke imports.
