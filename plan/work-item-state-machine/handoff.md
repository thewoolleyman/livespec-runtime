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
> the active orchestrator plugin root.) Filter for
> `livespec-runtime-l4yojx` and its children. Until the cut is approved
> and filed, the epic has **no children** — the slices are a DRAFT in
> `research/04-groom-cut.md`, not yet filed.

## Read-first chain (open these, in order)

1. `research/00-l0-overview.md` — the slice, the anchor, the reframe,
   and the cross-repo design-of-record paths.
2. `research/01-spec-deltas.md` — the spec deltas (now RATIFIED; kept for
   the rationale + heading-coverage reasoning + recommended scenarios).
3. `research/02-propose-change-findings.json` — the findings payload
   `revise` consumed; the `impl_followups[]` `id_hint`s are the
   `spec_commitment_hint` values each child carries.
4. `research/03-code-slices.md` — the code-slice breakdown (S1–S5).
5. `research/04-groom-cut.md` — **the drafted `groom` cut** (the current
   next action): the 5 dependency-layered children + the filing-mechanism
   decision. Awaiting the coordinator's approval relay.

## State as of this handoff

- ✅ Epic `livespec-runtime-l4yojx` anchored (prose-linked to
  `livespec-35s3zo`; no typed cross-tenant `depends_on`).
- ✅ Thread + drafts committed to `master` (PR #81 `e89fe9b`; handoff
  refresh #82 `cd50149`).
- ✅ **`revise` gate DONE** (driven by the coordinator/core session):
  commit **`42d3d5e`** on `origin/master`, history **`v008`**,
  `SPECIFICATION/contracts.md` ratified (the `### …work_items.types`
  rewrite + the new `### …work_items.lifecycle` / `### …work_items.rank`
  headings). **Do NOT re-run `propose-change` / `revise`.**
- ✅ **`groom` cut DRAFTED** — `research/04-groom-cut.md` (5
  dependency-layered children, each keyed to its `spec_commitment_hint`).
- 🚫 **Nothing filed to the ledger yet** — the epic has no children. The
  cut is maintainer-owned; file nothing until the coordinator relays
  approval.
- 🚫 **No code written yet** — the runtime `.py` lands only after the
  cut is approved + filed.

## Next action (ONE path — the `groom` cut, maintainer-owned)

`revise` is DONE. The single remaining gate is **`groom`** — and the cut
is already drafted in `research/04-groom-cut.md`. The maintainer/
coordinator OWNS it; **draft is surfaced, awaiting approval. File
nothing until approval is relayed.**

On approval:

1. **File the 5 children** of `livespec-runtime-l4yojx` per the approved
   cut in `04` — each `ready`, dep-linked by the layering (S3,S1 →
   S2 → S4 → S5), carrying `spec_commitment_hint = <id_hint>`. **Filing
   mechanism is a decision in `04`** (the native `groom`
   `file_approved_slices` hardcodes `spec_commitment_hint=None`, so use
   the `append_work_item`/`capture-work-item` path with the hint set, or
   `groom`-then-update — see `04` §"Filing mechanism").
2. **Implement S1–S4** via this repo's **red-green-replay** TDD
   (worktree → PR → rebase-merge).
3. **Cut the S5 `livespec-runtime` release** — the L0 exit gate; the
   artifact L1a (beads-fabro) + L1b (git-jsonl) vendor.

## Discipline (non-negotiable)

- Every change via **worktree → PR → rebase-merge**; `mise exec -- git
  …`; **never `--no-verify`**; halt + report on any hook failure.
- Product `.py` follows this repo's **red-green-replay** ritual.
- Operate only in worktrees you create.
