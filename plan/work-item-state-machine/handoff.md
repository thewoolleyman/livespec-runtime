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
| S3 types | `livespec-runtime-lxgk3g` | `types-schema-edits` | — | ✅ **DONE** (PR #89 `84173e6`; closed) |
| S2 lifecycle | `livespec-runtime-tscgce` | `lifecycle-module` | S3 | ✅ **DONE** (PR #91 `4cda557`; closed) |
| S4 tests | `livespec-runtime-rfwfie` | `lifecycle-rank-paired-tests` | S1, S2, S3 | ✅ **DONE** (PR #93 `4dbb2fc`; closed) |
| S5 release | `livespec-runtime-ocekuv` | `cut-runtime-release` | S1, S2, S3, S4 | 🛑 **AWAITING MAINTAINER** — release PR #87 (0.5.0) OPEN; STOP before merge |

**All four code slices (S1–S4) are DONE + merged + closed.** S5 is the
release exit gate: release-please has OPENED the release PR (**#87,
`chore(master): release 0.5.0`**, branch
`release-please--branches--master--components--livespec-runtime`, label
`autorelease: pending`). Per the coordinator relay the agent **STOPS
before merging** — the L0 release unblocks the whole L1 layer, so
**maintainer approval is relayed first**. `ocekuv` stays OPEN until the
maintainer merges #87 and the tag is cut.

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
- ✅ **S3 DONE** — `types.py` rebuilt to the ratified 20-field shape
  (7-state `WorkItemStatus`; `+rank: str` required; `−priority: int`;
  `AdmissionPolicy`/`AcceptancePolicy`/`StoredBlockedReason` aliases +
  the three `… | None = None` policy fields; module-docstring drift
  fixed) + collateral `test_reduce.py`/`test_store.py` construction
  updates; landed on `master` (PR #89, `84173e6`); `reduce.py` identity
  reducer green over the new shape (100% per-file coverage); child
  `lxgk3g` closed (`completed`, merge-evidence audit).
- ✅ **S2 DONE** — net-new `lifecycle.py` (the `lane_of` single lane
  authority; `is_item_ready` = `lane_of(...).name=="ready"`;
  `ready_sort_key` on `(rank, id)`; the dep-blocking predicate relocated
  from the orchestrator's `_cross_repo.py` as PURE functions injecting
  only the in-memory `index` — no `runtime → beads` back-edge, sibling
  deps resolve `UNKNOWN`) + `test_lifecycle.py` (lane scenarios + 100%
  per-file coverage, offline); landed on `master` (PR #91, `4cda557`);
  child `tscgce` closed (`completed`, merge-evidence audit). **No
  orchestrator-repo edits** (the `_cross_repo.py` shrink is L1a).
- ✅ **S4 DONE** — cross-module + completeness tests (the
  `is_item_ready` ⇔ `lane_of(...).name=="ready"` agreement matrix in
  `test_lifecycle.py`; the verbatim `_fractional_indexing` round-trip /
  `validate_order_key` drift guard in `test__fractional_indexing.py`;
  the work_items tests `CLAUDE.md` refresh) landed on `master` (PR #93,
  `4dbb2fc`); per-file 100% coverage green (164 tests); behavior-
  preserving so it took the **green-verified leg** (`TDD-Suite-Green-*`),
  not the Red→Green ritual; child `rfwfie` closed (`completed`,
  merge-evidence audit).
- 🛑 **S5 AWAITING MAINTAINER** — release-please has OPENED the release
  PR (**#87, `chore(master): release 0.5.0`**). The agent STOPS before
  merging; `ocekuv` stays OPEN.

## Next action — MAINTAINER: approve + merge the release PR (S5)

S1–S4 are complete. The only remaining step is the maintainer-owned
release exit gate. **The agent must NOT merge the release PR** — the L0
release unblocks the whole L1 layer, so approval is relayed first.

1. **Review release PR #87** (`chore(master): release 0.5.0`, branch
   `release-please--branches--master--components--livespec-runtime`).
   Changelog = the three product features (S1 rank wrapper, S3 20-field
   schema, S2 lifecycle authority); S4 was `test:` so it carries no
   changelog entry, by design. The PR bumps every `x-release-please-version`
   anchor `v0.4.0 → v0.5.0` (`.release-please-manifest.json`,
   `pyproject.toml` `version`, `SPECIFICATION/contracts.md`
   `compat.pinned` + both `[tool.uv.sources]` example tags) + the
   `CHANGELOG.md` 0.5.0 section.
   - NB the schema change is breaking (`−priority`, the new 7-state
     `WorkItemStatus`) but was authored as plain `feat:` (no `!` /
     `BREAKING CHANGE:`), so release-please proposes a 0.x **minor** bump
     (0.4.0 → 0.5.0). For a pre-1.0 library that is the conventional
     encoding; if the maintainer wants a louder signal, re-tag is a
     maintainer call.
2. **On maintainer approval:** merge #87 (the repo's rebase-merge
   discipline). release-please then cuts the **`v0.5.0`** tag (the
   `release-dispatch.yml` flow). **This tag is what L1a/L1b vendor — the
   whole L1 layer gates on it.**
3. **After the tag is cut:** close `ocekuv` via the store close-in-place
   path (status `closed`, `resolution=completed`, merge-evidence
   `AuditRecord` with the release merge sha + PR #87), matching S1–S4.
   That closes the L0 epic `livespec-runtime-l4yojx`.

Close each child via the `implement` freeform path as its PR merges (or
per the coordinator's dispatch). The ratified contract surface to build
to: `SPECIFICATION/contracts.md` §§`work_items.types` / `.lifecycle` /
`.rank`; per-slice scope + acceptance in `research/04-groom-cut.md`.

## Discipline (non-negotiable)

- Every change via **worktree → PR → rebase-merge**; `mise exec -- git
  …`; **never `--no-verify`**; halt + report on any hook failure.
- Product `.py` follows this repo's **red-green-replay** ritual.
- Operate only in worktrees you create.
