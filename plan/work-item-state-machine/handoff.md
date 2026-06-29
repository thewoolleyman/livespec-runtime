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
> `livespec-runtime-l4yojx` and its children. Until `groom` runs, the
> epic has **no children** — the code slices are a DRAFT in
> `research/03-code-slices.md`, not yet filed.

## Read-first chain (open these, in order)

1. `research/00-l0-overview.md` — the slice, the anchor, the reframe,
   and the cross-repo design-of-record paths.
2. `research/01-spec-deltas.md` — the exact `SPECIFICATION/contracts.md`
   deltas (the propose-change payload, human-readable) + the
   heading-coverage reasoning + the recommended `scenarios.md` additions.
3. `research/02-propose-change-findings.json` — the schema-valid
   `/livespec:propose-change` findings payload for (2).
4. `research/03-code-slices.md` — the code-slice breakdown (S1–S5), keyed
   to the `impl_followups[]` id_hints in (3).

## State as of this handoff

- ✅ Epic `livespec-runtime-l4yojx` anchored (prose-linked to
  `livespec-35s3zo`; no typed cross-tenant `depends_on`).
- ✅ Spec propose-change payload drafted (`01` + `02`), schema-validated.
- ✅ Code-slice breakdown drafted (`03`).
- ⏳ **Two maintainer-owned gates remain (the next action).**

## Next action (ONE path — the two maintainer-owned gates)

**The maintainer owns both; this track drafted them and must NOT
auto-pass either.**

1. **`revise` (spec ratification).** Author the proposed-change file
   from the drafted findings, then ratify:
   ```bash
   # author (drafting; produces SPECIFICATION/proposed_changes/<topic>.md):
   /livespec:propose-change work-item-lifecycle-l0 \
     --findings-json plan/work-item-state-machine/research/02-propose-change-findings.json
   # then ratify (maintainer gate):
   /livespec:revise
   ```
   (Or run `/livespec:propose-change` interactively, pasting the intent
   from `01-spec-deltas.md`.) Ratifying applies Deltas 1–4 to
   `SPECIFICATION/contracts.md`. Per `01`'s reasoning, **no
   `tests/heading-coverage.json` change is required** (the new `### `
   headings fall under the already-registered `## Module-level public
   surface` h2; the check skips `### `).

2. **`groom` (the slice cut).** Decompose epic `livespec-runtime-l4yojx`
   into dispatchable `ready` children using `research/03-code-slices.md`
   (S1–S5). Each filed child carries `spec_commitment_hint = <id_hint>`
   from `02`'s `impl_followups[]`. Then the code lands via the
   red-green-replay TDD ritual (worktree → PR → rebase-merge), and the
   **L0 exit gate is the `livespec-runtime` release** (S5) — the artifact
   L1a/L1b vendor.

After the release, the L1a (beads-fabro) and L1b (git-jsonl) tracks can
re-vendor and consume the new `livespec_runtime.work_items.{lifecycle,
rank}` + the new `types` shape.

## Discipline (non-negotiable)

- Every change via **worktree → PR → rebase-merge**; `mise exec -- git
  …`; **never `--no-verify`**; halt + report on any hook failure.
- Product `.py` follows this repo's **red-green-replay** ritual.
- Operate only in worktrees you create.
