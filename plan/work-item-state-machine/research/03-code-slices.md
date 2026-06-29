# L0 code-slice breakdown (the `groom` input)

This is the **drafted code-slice breakdown** for the maintainer-owned
**`groom`** gate to cut into dispatchable `ready` children of epic
**`livespec-runtime-l4yojx`**. It maps 1:1 to the
`spec_commitments.impl_followups[]` in `02-propose-change-findings.json`
(so each filed child pairs back via `spec_commitment_hint = <id_hint>`).

**Sequencing constraint inside L0:** the code slices land AFTER the
spec propose-change is ratified (`revise`), because the code realizes
the ratified contract. Within the code, `rank` (S1) and `types` (S3)
are independent; `lifecycle` (S2) depends on `types` (S3) for the new
`WorkItem` shape and on `cross_repo` (already present). Tests (S4) pair
each module. The release (S5) is the exit gate and depends on S1–S4.

All product `.py` follows **this repo's red-green-replay TDD ritual**
(test-alone Red commit → impl Green amend; ONE commit carries both).
Every change via **worktree → PR → rebase-merge**; `mise exec -- git …`;
never `--no-verify`.

---

## S1 — `port-fractional-indexing` (rank primitive)

**Files:**
- `livespec_runtime/work_items/_fractional_indexing.py` — **PORTED
  VERBATIM** from `httpie/fractional-indexing-python` (the official
  Python port of `rocicorp/fractional-indexing`; stdlib-only: `math`,
  `typing`, `decimal`; CC0-1.0). Add an attribution header naming the
  upstream, the commit/tag ported, and the CC0-1.0 dedication. Public
  surface: `generate_key_between`, `generate_n_keys_between`,
  `validate_order_key`. **Do NOT refactor** — verbatim keeps it
  finished-math + drift-free (decision 38).
- `livespec_runtime/work_items/rank.py` — thin livespec-facing wrapper:
  `key_between(*, a, b)`, `n_keys_between(*, a, b, n)`, and the shared
  **`BOTTOM_SENTINEL`** constant (a char outside the base-62 alphabet,
  e.g. `"~"`). Keyword-only args per repo discipline.
- `NOTICES` (repo root, new) — the CC0-1.0 attribution line for the
  ported module (decision 38, G-1 consequence (c)).
- Tests: `tests/livespec_runtime/work_items/test_rank.py` (+ any
  `_fractional_indexing` round-trip/property tests) + a
  `tests/.../CLAUDE.md` if a new test dir is introduced.

**Notes:** `BOTTOM_SENTINEL` is consumed by the two backend store
adapters (L1a/L1b), imported from here — L0 only defines it. The wrapper
is the ONLY livespec-facing API; consumers never import
`_fractional_indexing` directly (the `_` prefix marks it private).

**Acceptance:** `key_between`/`n_keys_between` produce valid base-62
keys ordering strictly between neighbors; `BOTTOM_SENTINEL` sorts
strictly after every real key (`"~" > "z"`); `just check` green;
NOTICES present; attribution header present.

---

## S2 — `lifecycle-module` (the single lane authority)

**File:** `livespec_runtime/work_items/lifecycle.py` (net-new).

Contents (decisions 40/42):
- `Lane` (frozen/slotted/kw-only `{name: LaneName, reason:
  BlockedReason | None}`), `LaneName`, `BlockedReason` aliases.
- `lane_of(*, item, index, manifest) -> Lane` — net-new. Overlay logic
  per `01-spec-deltas.md` Delta 2.
- `is_item_ready(*, item, index, manifest) -> bool` =
  `lane_of(...).name == "ready"`. **Relocated** from the beads-fabro
  orchestrator's `commands/_cross_repo.py`, but as a **PURE predicate
  that takes INJECTED status-lookup callables** — the beads
  store-reading (`resolve_store_config`, the `read_work_items` free
  function, `StoreConfig`) MUST NOT move into the runtime (that would be
  a `runtime → beads` back-edge; decision 42). Reuse
  `livespec_runtime.cross_repo.resolve_ref` / `RefStatus` and the
  existing `local_status_lookup` / `sibling_status_lookup` injection
  seam.
- `ready_sort_key(item) -> tuple[...]` — relocated; lead key
  `priority → rank`, then `id` tie-break (decision 39). Drop the old
  `_GAP_TIED_RANK`/`_FREEFORM_RANK`/`captured_at` heuristic.
- The dependency predicate helpers (`parse_entry`, `_entry_blocks`, the
  local-lookup constructor) lifted from `_cross_repo.py`, parameterized
  on injected lookups.

**Coordination with L1a (beads-fabro):** the orchestrator's
`_cross_repo.py` shrinks to orchestrator-only bits
(`load_manifest`, the beads store-reading that BUILDS the injected
lookups); its `next`/Dispatcher/`list-work-items` IMPORT these from the
runtime. That shrink is an **L1a** change (it gates on the L0 release) —
**not** part of L0. L0 only ADDS `lifecycle.py`; it does not edit the
orchestrator repo. Name-collision caveat (decision 42): runtime's
`read_work_items` is a Protocol *method*, not the beads free function.

**Acceptance:** the lane truth-table holds (the 6 recommended scenarios
in `01-spec-deltas.md`); `is_item_ready` agrees with
`lane_of(...).name=="ready"` by construction; no import of any
beads/orchestrator symbol from `lifecycle.py`; `just check` green.

---

## S3 — `types-schema-edits`

**File:** `livespec_runtime/work_items/types.py`.

- `WorkItemStatus` → the 7-state `Literal`.
- `+ rank: str` (required, non-null, no default) in the required-field
  block (where `priority` was); `− priority: int`.
- New aliases `AdmissionPolicy`, `AcceptancePolicy`,
  `StoredBlockedReason`; add `admission_policy` / `acceptance_policy` /
  `blocked_reason` as defaulted `… | None = None` fields among the
  optional-on-read block (alongside `spec_commitment_hint`/`supersedes`).
- Keep `assignee: str | None` in place (the reused owner field); add the
  `active ⟹ assignee` requirement to the docstring (the dataclass
  itself can't enforce it — doctor does, at L1).
- Update `__all__` for the new aliases.
- Fix the module-docstring drift ("codified by
  `livespec/SPECIFICATION/contracts.md`") to point at this repo's own
  `### livespec_runtime.work_items.types` (decision 44).

**Blast-radius check inside the runtime:** `reduce.py`'s
`_work_item_to_dict` uses `asdict` + an explicit `audit` re-pack; the new
scalar/optional fields auto-serialize via `asdict` (no `reduce.py`
change needed), but **confirm** `work_item_record_identity`'s canonical
serialization includes the new keys deterministically (it will — `asdict`
emits every field; sorted-keys canonicalization handles the rest). The
removal of `priority` changes the canonical identity of any record
re-serialized post-migration — this is expected (the migration is L2 and
re-keys via `rebalance-ranks`); L0 only changes the *type*, it does not
rewrite stored lines.

**Acceptance:** `WorkItem` constructs with the new shape; `test_types.py`
updated; `mypy`/`pyright` + `just check` green; identity reducer still
deterministic over the new shape.

---

## S4 — `lifecycle-rank-paired-tests`

Paired tests mirroring the source tree (per `tests/CLAUDE.md`
1:1-pairing discipline):
- `tests/livespec_runtime/work_items/test_rank.py`
- `tests/livespec_runtime/work_items/test_lifecycle.py`
- updated `tests/livespec_runtime/work_items/test_types.py`
- any `_fractional_indexing` test (round-trip / `validate_order_key`).

Cover the 6 recommended scenarios in `01-spec-deltas.md` (lane overlay
cases, `ready_sort_key` rank ordering, `key_between` betweenness, the
sentinel sort property). NB: these are folded into the red-green-replay
commits for S1–S3 (the Red test rides with its impl); S4 is the
*coverage-completion* slice for anything not naturally paired in S1–S3
(e.g. cross-module lane↔readiness agreement).

**Acceptance:** per-file 100% coverage gate
(`just check-per-file-coverage`) green; heading/claude-md coverage green.

---

## S5 — `cut-runtime-release` (the L0 exit gate)

Once S1–S4 are merged to `master`, a `feat:`-subject change triggers
release-please to cut the next `livespec-runtime` tag. **This tag is the
artifact L1a/L1b vendor** — the whole L1 layer gates on it. Bump any
in-repo self-references (`.livespec.jsonc` `compat.pinned`,
`contracts.md` `[tool.uv.sources]` example tag) as release-please's
flow dictates.

**Acceptance:** release-please PR merged; new tag visible; the
`livespec_runtime.work_items.{lifecycle,rank}` + the new `types` shape
importable from the released artifact.

---

## What L0 does NOT touch (boundary)

- **No orchestrator-repo edits** — the `_cross_repo.py` shrink, the
  Dispatcher valves/WIP, `list-work-items` lane emission, custom-status
  registration, the 2-step `append_work_item`, `rebalance-ranks`, and the
  doctor invariants are **L1a** (beads-fabro), gating on the L0 release.
- **No git-jsonl edits** — store required-keys + sentinel adapter +
  `next` `priority→rank` are **L1b**, gating on the L0 release.
- **No tenant data migration** — the `rank` backfill + custom-status
  registration across all 9 tenants is **L2**, gating on the L1 releases.
- **No CORE spec edits** — the reframe (decision 44) keeps the contract
  out of CORE.
