# 003 — Triage batch 1: the whole snapshot, the stray worktrees, the un-anchored plan

Proposed 2026-09-06 for the maintainer's ruling. Every disposition below is a
PROPOSAL until the ruling is recorded as a scope event on
`livespec-runtime-c7toen`; nothing in the ledger or the worktree root changes
before that. Measured against master `9ae4ed2`, the forge (two bulk PR
listings, zero open PRs), and a ledger dump taken at 06:27Z. Where the brief
that produced these numbers was read rather than re-measured, the load-bearing
claims were re-verified by hand before this note was written (the workflow
file, the retired CI job, the v017–v019 history, the v010 revision, the
registry's TODO ownership, the release commits' lockfile stats, and `git
cherry` on five worktrees).

With 18 items the whole snapshot fits one batch. Dispositions use the charter
§5 sorting rule. Confidence is stated per class; only one class carries a
genuine question.

## 1. Close — landed or falsified (6)

Each of these was resolved weeks ago and never closed. Evidence is primary.

| id | P | was | why it is done |
|---|---|---|---|
| `2xs` | 1 | backlog | `.github/workflows/auto-enable-merge.yml` landed as PR #437 on 2026-08-03; six release-please PRs have merged through it since; no PR is parked. |
| `5ud` | 2 | backlog | Commit `450ed40` (2026-09-04) deleted the `detect-py-changes` job and every `py_changed` condition, and armed `ci_gate_parity`. The only remaining mention is the header comment describing the retired job. |
| `mkn` | 2 | backlog | The registry has 23 TODO entries and 0 unowned; the armed TODO-ownership tier exits 0 on master. The item's exit criterion is exactly that command passing. |
| `0h8` | 2 | blocked | v017 (2026-08-26, PR #633) ratified the per-kind blocking rule for `sibling_work_item`; v018 and v019 closed the two follow-ups the closing comment named; `proposed_changes/` is empty. |
| `woe5gi` | 2 | blocked | Its own metadata chose "revise the clause" on 2026-07-10; v010 (`ci-invocation-clause-align-fleet-matrix`, 2026-07-11) did exactly that. Blocked for eight weeks after being satisfied. |
| `xct` | 2 | open | Commit `9ae4ed2` (today) prescribes `just worktree-create` in AGENTS.md AND makes a raw worktree commit-capable through the hooks. The premise is false by design. Its one surviving sentence (a hook-rejected commit leaves changes staged) is parked. |

Confidence: high on all six. Closed with reason `landed (c7toen batch 1)`.

## 2. Close — wrong tenant (1)

- `f5zhs5` (P3, backlog): the code is livespec core's
  `no_spec_section_citation_in_code.py`, which prunes a hard-coded directory
  set and does not honor gitignore. Nothing in this repository can change
  that; it has been a non-dispatchable cross-repo pointer for nine weeks. Under
  the never-work-around rule the item is re-filed in the `livespec` tenant with
  its acceptance text carried over, and the path recorded here. Confidence:
  medium-high.

## 3. Consolidate (2 into 2 survivors)

| closes | into | why |
|---|---|---|
| `6m4` (P3) | `ciq` (P2) | Same module (`hygiene_scan_worktrees.py`), same fixtures, and `ciq`'s fix alone yields nothing in a rebase-merge fleet: today 9 of the 14 stray worktrees have MERGED PRs yet read "unmerged" by ancestry, and 2 more are hidden by untracked dirt, so the detector is blind to 11 of 14. The survivor's acceptance gains "merged-ness by patch equivalence (`git cherry`), not ancestry". |
| `vbofkr` (P2) | `mqsxsu.4` (P1) | Scenarios for `github_auth` (0 today) and `work_items` (2) are decided per module family by the public-surface reconciliation, and this repo's revise discipline co-edits scenarios and heading coverage in one propose-change. The gap id `gap-vjxowbbp` and the "or consciously exempted" wording carry across. |

Confidence: high on `6m4`, medium-high on `vbofkr`.

## 4. Re-scope (2)

- `cq8` (P1, ready): the Result-railway adoption. Partial adoption landed
  (`parse_depends_on_entry`, `load_github_app_config`, the hygiene spawn,
  v016's `retry_with_backoff`/`resolve_ref`), but `check-public-api-result-typed`
  still exits 0 vacuously behind the role-absence gate, so "done" is
  unmeasured. New scope: re-derive the flagged set with the un-gated checker,
  record the per-function (a)/(b)/(c) disposition on the item, add
  `hygiene_scan_cli.py` to `supervisor_entry_files`, convert the genuine (a)
  cases, report (c) false positives upstream on `livespec-dev-tooling-idlx`.
  Dispatchable. Its `non_local_depends_on` sibling `idlx` may make the readiness
  gate disagree with the `ready` status; that is read at dispatch time, not
  assumed.
- `5s4ax2` (P2, blocked, gap `gap-nyckdcxc`): the 404 discriminator. The
  SHOULD wanted to avoid bare-substring collisions; the shipped discriminator is
  already `gh`'s structured `(HTTP 404)` stderr line consumed through a typed
  `http_404` field, and `gh` exits 1 for every API error so an exit code can
  never discriminate. Proposed as decided: accept-as-satisfied and file a
  one-clause propose-change relaxing the SHOULD to name the structured line or
  an explicit status header; on ratification the gap and the item close. The
  spec lane is the maintainer's; the proposal payload is prepared by the drive
  session and handed to `livespec:propose-change`, per AGENTS.md.

## 5. Keep (7), with the two status repairs

| id | P | tier | note |
|---|---|---|---|
| `mqsxsu.4` | 1 | 3 | **Status repair first:** carries `open`, outside `WorkItemStatus`; the 2026-07-06 record on `f5zhs5` shows one such record blocked ALL factory dispatch in this tenant. Normalize to `backlog`. Absorbs `vbofkr`. Mechanical half (an `__all__` ⊆ contracts.md check plus the group-3 narrowing) is dispatchable; the documentation half is a propose-change → revise pass that the dispatch prompt must authorize explicitly. |
| `acf` | 1 | 1 | Still true: `decide_credentials` checks only the env sentinel, no argv marker, no depth bound. Slice S1 (pure brain: marker + depth → `Fail`, termination proven with the env sentinel absent) is dispatchable here. S2 (append/strip the marker in the orchestrator's `_bootstrap.py`) and S3 (dispatcher subprocess timeout) are orchestrator-tenant work: filed there, path recorded on `acf`, S1 and S2 released together. Tier 1 because the defect is in the dispatcher's credential path. |
| `ciq` | 2 | 2 | Absorbs `6m4`. Dispatchable. Demonstrated live on two stray worktrees today. |
| `8zu` | 2 | 4, **canary** | Unchecked cast in `mapping_option`; sibling `int_option` has the same pattern. Small, `ready`, product `.py` with a `fix:` subject: it exercises the whole Red-Green-Replay factory path, which is what the charter §6 tier-0 canary is for. |
| `wpt` | 2 | 4 | `GithubBudgetedClient` still has zero production callers; the four call sites match the item's inventory. Description trimmed toward the dispatcher's sizing guidance before dispatch. |
| `jis` | 3 | 4 | 0 of the last 8 release commits touch `uv.lock`; `release-please-config.json` lacks the `generic` extra-file that livespec-overseer's config carries for exactly this. Config-only, `chore(release):`, no TDD ritual. Acceptance observable at the next release. |
| `mqsxsu` | 2 | 3 | The plan anchor for `homelab-loop-hardening-runtime`; 7 of 8 children closed. Stays until `.4` disposes, then the archive gates run. Not dispatchable (epic). |

Exemption labels proposed: **none**. Every keep is dispatchable. If the tier-0
canary fails on the factory path, the failure is filed as a discovered-during
`factory-path-defect` under charter §4 and that item, not any of these, gets
the label.

## 6. Hygiene — the 14 stray worktrees

Fifteen worktrees exist under `~/.worktrees/livespec-runtime/`; one is this
session's. `git cherry master HEAD` was run for every stray; "cherry" is the
count of unmerged patches.

| worktree | PR | cherry | dirty | disposition |
|---|---|---|---|---|
| add-ratification-reviewer-model | #545 merged | 0 | clean | remove as merged |
| cap-test-parallelism | landed as `5dffbd1` | 0 | clean | remove as merged |
| fix-spec-pr-merge-governance-key | #521 merged | 0 | clean | remove as merged |
| fix/auto-enable-release-merge | #437 merged | 0 | clean | remove as merged (`2xs`) |
| fix/ci-telemetry-argmax | #566 merged | 0 | `M uv.lock` (the `jis` artifact) | remove as merged, discarding the lock diff |
| foreman-consensus-valve | #596 merged | 0 | clean | remove as merged |
| impl/awaits-scope-override-field | #533 merged | 0 | clean | remove as merged |
| lever-propose-change-batch | #525 merged | 0 | clean | remove as merged |
| spec/awaits-scope-override-field | #531 merged | 0 | clean | remove as merged |
| spec/ratify-awaits-scope-override | #532 merged | 0 | clean | remove as merged |
| wire-tombstone-check | landed as `f0ba5ee` | 0 | clean | remove as merged |
| chore/hp-default-dispatch-factory | none (0 own commits) | 0 | stray `.livespec.jsonc.tmp.*` | remove as abandoned |
| janitor-livespec-runtime-6bnjkd | detached, in master | 0 | `M .livespec.jsonc`, untracked `.livespec-core/` | remove as abandoned (the `ciq` specimen) |
| ci-concurrency-group | none | **1** | clean | remove as abandoned: a 4-line `concurrency:` block in `ci.yml`, a workflow edit forbidden on the factory path and predating the `450ed40` rewrite. Recorded here; if wanted, it is a fresh item, not a rebase. |
| **runtime-backlog-drain** | #650 | — | staged plan files | **keep** (this session) |

Fourteen removals; thirteen local branches deleted afterwards, every one
patch-equivalent to master except `ci-concurrency-group`, whose four lines are
recorded above. `branch -D` on those is the codified cleanup of the mutation
protocol, not an ad-hoc destructive act.

## 7. The un-anchored plan

`plan/credential-reexec-loop-guard/` (2026-08-10) has no anchor epic, a
pre-Planning-Lane `handoff.md`, and none of its four slices filed. Its content
is the research behind `acf`. Proposed as decided: move the directory to
`plan/archive/credential-reexec-loop-guard/`, record on `acf` that the archived
research is its design record, and let `acf` carry the work. The alternative
(filing an anchor epic) would create a new item for a plan whose only live
content is one snapshot item. Confidence: medium-high; `plan_epic_parity` is
armed-only and will report at the next armed run if an archived directory with
no epic is a finding, in which case the fallback is to fold the research into
`acf`'s comments and delete the directory.

## 8. Ordering after the ruling

0. Canary: `drive --action impl:livespec-runtime-8zu`, run to a journal
   `outcome` event, before any other dispatch.
1. Tier 1: status repairs (`mqsxsu.4` → backlog, `xct` closed) — done at ruling
   time; `acf` S1 dispatched, S2/S3 filed in the orchestrator tenant.
2. Tier 2: `cq8` (re-scoped), `ciq` (+`6m4`).
3. Tier 3: `mqsxsu.4` (+`vbofkr`), then `mqsxsu` archive gates.
4. Tier 4: `wpt`, `jis`, `5s4ax2` after its propose-change ratifies.

## 9. What the ruling authorizes, mechanically

On "ratify as proposed":

- `bd close` × 7 (`2xs 5ud mkn 0h8 woe5gi xct f5zhs5`), each reason naming
  `c7toen batch 1` and the class; the `f5zhs5` re-file path recorded on it
  once filed in the `livespec` tenant.
- `bd close` × 2 as consolidated (`6m4` → `ciq`, `vbofkr` → `mqsxsu.4`), with
  an absorbing comment on each survivor.
- `bd update --status backlog` on `mqsxsu.4`; re-scope comments on `cq8` and
  `5s4ax2`.
- Worktree removals × 14 and branch deletions × 13, then `git worktree prune`.
- The plan-directory move in §7, committed on this branch.
- A scope event on `livespec-runtime-c7toen` recording every disposition by
  id, then the canary dispatch and the loop.

Net effect against the snapshot: 9 of 18 closed, 9 remain, all dispatchable.
