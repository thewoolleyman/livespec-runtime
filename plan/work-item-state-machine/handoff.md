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
| S5 release | `livespec-runtime-ocekuv` | `cut-runtime-release` | S1, S2, S3, S4 | 🧊 **HELD** — v0.5.0 blocked; WI-A ✅ merged (PR #96), **WI-B (CORE) pending**; #87 left OPEN |

**All four code slices (S1–S4) are DONE + merged + closed.** S5 (the
release exit gate) is **HELD by maintainer decision** — see
"L0 v0.5.0 release HELD" below. **WI-A (release-please App-token CI fix)
is DONE + merged (PR #96, `0914ec2`); WI-B (doctor out-of-band, home
livespec core) is still pending.** `ocekuv` and the epic
`livespec-runtime-l4yojx` stay **OPEN, blocked** until WI-B lands and the
release is cut.

### L0 v0.5.0 release HELD — release-please↔doctor interaction (blocker)

The maintainer is **holding the L0 v0.5.0 release** until the
release-please↔doctor interaction is fixed **systemically** (not worked
around per-release). Two findings surfaced while attempting S5; both are
now tracked as **new work-items linked to the fleet anchor
`livespec-35s3zo`** (the coordinator drives them — this thread does NOT
file or fix them):

- **WI-A — release-please PRs must run CI ungated** (`livespec-runtime-emz`;
  reference pattern home: **livespec-dev-tooling**) — ✅ **RESOLVED + MERGED**
  (PR #96, `0914ec2`). The release PR is authored by the release-please
  bot token, so its `pull_request` CI run was parked `action_required`
  (0 jobs) and the branch-protection required checks never reported →
  `mergeStateStatus: BLOCKED`. The fork-only
  `POST …/actions/runs/<id>/approve` endpoint does NOT apply (403 "not
  from a fork pull request"); manual unblock was close+reopen the PR as a
  human actor (re-fires `pull_request: reopened` ungated). **Fix landed
  in THIS repo's `.github/workflows/release-please.yml`:** a
  `actions/create-github-app-token@v1` step mints the livespec App
  installation token (`secrets.APP_ID` / `APP_PRIVATE_KEY`, already
  present) and passes `token:` to `googleapis/release-please-action@v4`
  — so the NEXT release PR release-please opens is App-authored and its
  CI runs ungated (it also restores the `release: published` fan-out
  event). The `emz` work-item is left for the coordinator to close as
  part of release gating. NB the CURRENTLY-OPEN #87 was opened under the
  OLD bot-token flow, so until release-please re-opens/updates it under
  the App identity (next master push) it may still need a one-time
  close+reopen to pick up ungated CI.
- **WI-B — doctor `out-of-band-edits` must not red master on
  release-please spec-file version bumps** (home: **livespec core**).
  release-please bumps the `x-release-please-version` anchors in
  `SPECIFICATION/contracts.md` (`compat.pinned` + the two
  `[tool.uv.sources]` example tags) `v0.4.0 → v0.5.0`. That drifts the
  active spec vs `history/v008`, so `doctor-out-of-band-edits` fails.
  `check-doctor-static` has no PR-only guard → it would run on the
  master-push CI after merge → master CI conclusion = failure →
  `check-master-ci-green` then blocks EVERY future pre-commit/pre-push
  (the repo's commit workflow freezes). The doctor's self-heal writes a
  `SPECIFICATION/history/vNNN/` backfill (verified: an untracked `v009/`
  snapshot of the spec at v0.5.0 + an `out-of-band-edit-<ts>` PC/revision
  pair; staging it → `doctor-static` green), but that is a
  maintainer-owned spec-history mutation and must land WITH the bump so
  master never reds. Fix: doctor (or the release flow) must not red
  master on `x-release-please-version`-only spec-file edits (exempt the
  annotated anchors, or auto-land the backfill atomically).

**State of the attempt (what was and was NOT done):**

- ✅ CI was made to run on #87 (close+reopen workaround) — the **5
  required checks pass** (`check-lint` / `check-format` / `check-coverage`
  / `check-aggregate-completeness` /
  `check-primary-checkout-commit-refuse-hook-installed`).
- ❌ Non-required `check-doctor-static` **fails** on #87
  (`doctor-out-of-band-edits` vs `history/v008`) — the WI-B blocker.
- 🚫 **#87 NOT merged** (merging would red master + freeze commits).
- 🚫 **No `v009` (or any spec-history) written** — the self-heal was only
  *probed* in a throwaway worktree (since removed); nothing committed.
- ✅ Tree clean on `master`; no orphaned worktrees; **#87 left OPEN**
  (`chore(master): release 0.5.0`, label `autorelease: pending`).

**Re-engagement (WI-A done; after WI-B lands):** the coordinator
re-engages this thread to cut the release. Then: ensure #87's CI is green
(WI-A — merged — makes that ungated once release-please re-opens #87
under the App identity, or via a one-time close+reopen; WI-B keeps
`doctor-static` green) →
rebase-merge #87 → confirm release-please cuts the **`v0.5.0`** tag (the
artifact L1a/L1b vendor) → close `ocekuv` via the store close-in-place
path (status `closed`, `resolution=completed`, merge-evidence
`AuditRecord` with the release merge sha + PR #87), closing the epic
`livespec-runtime-l4yojx`.

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
- 🧊 **S5 HELD** — release-please OPENED the release PR (**#87,
  `chore(master): release 0.5.0`**) and S5 was attempted, but the
  maintainer is **HOLDING the v0.5.0 release** pending a systemic fix of
  the release-please↔doctor interaction (**WI-A** + **WI-B**, both linked
  to fleet anchor `livespec-35s3zo`; the coordinator drives them). #87 is
  left OPEN; no `v009`/spec-history written; `ocekuv` + the epic stay
  OPEN, blocked. Full detail in "L0 v0.5.0 release HELD" above.

## Next action — BLOCKED: release HELD pending WI-A + WI-B (coordinator-driven)

**S1–S4 (all L0 code) are DONE + merged + closed.** The only remaining
step is S5 (cut the v0.5.0 release), which is **HELD**. This thread does
NOT drive the fix — the coordinator drives **WI-A** (release-please CI
ungated, home livespec-dev-tooling) and **WI-B** (doctor `out-of-band-edits`
must not red master on release-please version bumps, home livespec core),
both anchored to `livespec-35s3zo`. See "L0 v0.5.0 release HELD" above for
the full diagnosis and the verified (but unwritten) doctor self-heal.

**Do NOT, while held:** merge #87; write `history/v009` (or any
spec-history); work around the block per-release (close+reopen + manual
v009 was only the *manual* path — the maintainer chose the systemic fix).

**On re-engagement (after WI-A + WI-B land), to cut the release:**

1. Confirm #87 is current and its CI is green — WI-A makes the release
   PR's CI run ungated; WI-B keeps `check-doctor-static` green through the
   `x-release-please-version` bump. (If #87 went stale, release-please
   re-opens/updates it on the next master push.) The PR bumps every
   `x-release-please-version` anchor `v0.4.0 → v0.5.0`
   (`.release-please-manifest.json`, `pyproject.toml` `version`,
   `SPECIFICATION/contracts.md` `compat.pinned` + both `[tool.uv.sources]`
   example tags) + the `CHANGELOG.md` 0.5.0 section. Changelog = the three
   product features (S1 rank wrapper, S3 20-field schema, S2 lifecycle
   authority); S4 was `test:` so it carries no changelog entry, by design.
   - NB the schema change is breaking (`−priority`, the new 7-state
     `WorkItemStatus`) but was authored as plain `feat:` (no `!` /
     `BREAKING CHANGE:`); the maintainer APPROVED a 0.x **minor** bump
     (0.4.0 → 0.5.0) as the conventional pre-1.0 encoding (relayed
     2026-06-29) — cut v0.5.0 as-is.
2. Merge #87 (the repo's rebase-merge discipline). release-please then
   cuts the **`v0.5.0`** tag (the `release-dispatch.yml` flow). **This tag
   is what L1a/L1b vendor — the whole L1 layer gates on it.**
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
