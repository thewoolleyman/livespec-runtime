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

| Slice | id | `spec_commitment_hint` | depends_on | dispatchable now? |
|---|---|---|---|---|
| S1 rank | `livespec-runtime-lel76i` | `port-fractional-indexing` | — | ✅ ready |
| S3 types | `livespec-runtime-lxgk3g` | `types-schema-edits` | — | ✅ ready |
| S2 lifecycle | `livespec-runtime-tscgce` | `lifecycle-module` | S3 | ⛔ (S3 open) |
| S4 tests | `livespec-runtime-rfwfie` | `lifecycle-rank-paired-tests` | S1, S2, S3 | ⛔ |
| S5 release | `livespec-runtime-ocekuv` | `cut-runtime-release` | S1, S2, S3, S4 | ⛔ |

`next` currently surfaces **S1 (`lel76i`) + S3 (`lxgk3g`)** as ready (the
no-open-dep layer-0 slices); S2/S4/S5 unblock as their deps close.

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
  are in the ledger, `ready`/factory, parent-linked + dep-linked, each
  carrying its `spec_commitment_hint`. **Do NOT re-file.**
- ⏳ **Code not yet written** — implement the slices next.

## Next action — implement the slices (red-green-replay)

Implement in dependency order; each via this repo's **red-green-replay**
TDD (worktree → PR → rebase-merge; `mise exec -- git`; never
`--no-verify`; halt + report on any hook failure):

1. **S1 (`livespec-runtime-lel76i`)** + **S3 (`livespec-runtime-lxgk3g`)**
   — independent (both ready now). Port `_fractional_indexing` + `rank.py`
   + `NOTICES` (S1); the `types.py` schema edits (S3). Use `feat:`
   subjects so release-please tracks them.
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
