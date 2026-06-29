# Handoff — work-item-state-machine (L0, livespec-runtime)

**Thread:** `plan/work-item-state-machine/` · **Ledger anchor:** epic
`livespec-runtime-l4yojx` (`livespec-runtime` beads tenant) · **Fleet
anchor (prose ref):** `livespec-35s3zo` (livespec core tenant).

> Status is **derived from the ledger**, never stored here. To read it:
> ```bash
> with-livespec-env.sh python3 \
>   /home/ubuntu/.claude/plugins/cache/livespec-orchestrator-beads-fabro/livespec-orchestrator-beads-fabro/*/scripts/bin/list_work_items.py --json
> ```
> (`with-livespec-env.sh` injects the tenant password; the glob resolves
> the active orchestrator plugin root.) See the children with
> `with-livespec-env.sh bd children livespec-runtime-l4yojx --json`. The
> cut is **APPROVED (Option A) + FILED** — the 5 children below are in the
> ledger under the CURRENT schema (`open`/`priority`/no-`rank`; the
> 7-state shape lands at the L2 migration).

## The filed children (epic `livespec-runtime-l4yojx`)

All `ready` + `origin:freeform`, `parent=livespec-runtime-l4yojx`, each
carrying `spec_commitment_hint = <id_hint>`. Deps are beads `blocks`
edges (round-trip to `depends_on` on read):

| Slice | id | `spec_commitment_hint` | depends_on | status |
|---|---|---|---|---|
| S1 rank | `livespec-runtime-lel76i` | `port-fractional-indexing` | — | ✅ **DONE** (PR #86 `976cf86`; closed) |
| S3 types | `livespec-runtime-lxgk3g` | `types-schema-edits` | — | ⏳ ready (NEXT) |
| S2 lifecycle | `livespec-runtime-tscgce` | `lifecycle-module` | S3 | ⛔ (S3 open) |
| S4 tests | `livespec-runtime-rfwfie` | `lifecycle-rank-paired-tests` | S1, S2, S3 | ⛔ |
| S5 release | `livespec-runtime-ocekuv` | `cut-runtime-release` | S1, S2, S3, S4 | ⛔ |

`next` currently surfaces **S3 (`lxgk3g`)** as the ready layer-0 slice;
S2/S4/S5 unblock as their deps close.

### Verbatim-port pattern (ESTABLISHED by S1 — reuse for any future port)

A verbatim third-party file lands in the first-party tree at its
ratified path and is excluded from the lint/type/coverage gates exactly
like `_vendor/` code (it can't take `# pragma`/reformatting without
ceasing to be verbatim). For `_fractional_indexing.py` the three
exclusions are already in `pyproject.toml`: ruff `extend-exclude`,
pyright `exclude`, coverage `omit` (`*/work_items/_fractional_indexing.py`).
The custom AST checks (keyword-only, no-inheritance, no-raise/except)
**no-op** in this repo (`[tool.livespec_dev_tooling].source_trees` is
empty for this flat-layout library), so they need no exclusion. The
first-party WRAPPER (`rank.py`) carries the gate-compliant, 100%-covered
surface.

## Read-first chain (open these, in order)

1. `research/00-l0-overview.md` — the slice, the anchor, the reframe,
   and the cross-repo design-of-record paths.
2. `research/01-spec-deltas.md` — the spec deltas (now RATIFIED; kept for
   the rationale + heading-coverage reasoning + recommended scenarios).
3. `research/02-propose-change-findings.json` — the findings payload
   `revise` consumed; the `impl_followups[]` `id_hint`s are the
   `spec_commitment_hint` values each child carries.
4. `research/03-code-slices.md` — the code-slice breakdown (S1–S5).
5. `research/04-groom-cut.md` — the `groom` cut (APPROVED, Option A,
   now FILED; see the table above for the minted ids).

## State as of this handoff

- ✅ Epic `livespec-runtime-l4yojx` anchored (prose-linked to
  `livespec-35s3zo`; no typed cross-tenant `depends_on`).
- ✅ Thread + drafts committed to `master` (PR #81 `e89fe9b`; #82
  `cd50149`; #84 `fa82022`).
- ✅ **`revise` gate DONE** (coordinator/core session): commit
  **`42d3d5e`**, history **`v008`**, `SPECIFICATION/contracts.md`
  ratified. **Do NOT re-run `propose-change` / `revise`.**
- ✅ **`groom` cut APPROVED (Option A) + FILED** — the 5 children above
  are in the ledger, parent-linked + dep-linked, each carrying its
  `spec_commitment_hint`. **Do NOT re-file.**
- ✅ **S1 DONE** — `rank.py` + verbatim `_fractional_indexing.py` +
  `NOTICES` + the three gate-exclusions landed on `master` (PR #86,
  `976cf86`); child `lel76i` closed (`completed`, merge-evidence audit).
- ⏳ **S3 next** (ready); then S2, S4, S5.

## Next action — implement the remaining slices (red-green-replay)

In dependency order; each via this repo's **red-green-replay** TDD
(worktree → PR → rebase-merge; `mise exec -- git`; never `--no-verify`;
halt + report on any hook failure). Use `feat:` subjects (release-please
tracking). Close each child on merge via the store close-in-place path
(status `closed`, `resolution=completed`, merge-evidence `AuditRecord`),
as done for S1.

1. **S3 (`livespec-runtime-lxgk3g`)** — `types.py` schema edits (build to
   the ratified `### …work_items.types`): 7-state `WorkItemStatus`;
   `+ rank: str` (required, where `priority` was); `− priority: int`;
   `AdmissionPolicy`/`AcceptancePolicy`/`StoredBlockedReason` aliases +
   the three `… | None = None` policy fields; keep `assignee` (document
   `active ⟹ assignee`); `__all__`; fix the module-docstring drift.
   Update `test_types.py`; confirm `reduce.py` identity reducer stays
   deterministic over the new shape. **NB:** `priority` is referenced by
   the orchestrator's `ready_sort_key` (in beads-fabro, an L1a concern)
   and by capture/groom filing under the CURRENT schema — but THIS repo's
   `livespec_runtime` has no internal `priority` reader beyond `types`/
   serialization, so the edit is contained here; just keep
   `reduce._work_item_to_dict` (asdict-based) working.
2. **S2 (`livespec-runtime-tscgce`)** — net-new `lifecycle.py` (after S3).
3. **S4 (`livespec-runtime-rfwfie`)** — paired tests + coverage
   completion (after S1+S2+S3).
4. **S5 (`livespec-runtime-ocekuv`)** — let **release-please open** the
   `livespec-runtime` release PR, then **STOP before merging it** and
   surface for the coordinator (the L0 release unblocks the whole L1
   layer; maintainer approval is relayed first).

Close each child via the `implement` freeform path as its PR merges (or
per the coordinator's dispatch). The ratified contract surface to build
to: `SPECIFICATION/contracts.md` §§`work_items.types` / `.lifecycle` /
`.rank`; per-slice scope + acceptance in `research/04-groom-cut.md`.

## Discipline (non-negotiable)

- Every change via **worktree → PR → rebase-merge**; `mise exec -- git
  …`; **never `--no-verify`**; halt + report on any hook failure.
- Product `.py` follows this repo's **red-green-replay** ritual.
- Operate only in worktrees you create.
