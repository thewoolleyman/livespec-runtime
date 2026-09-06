# Handoff — credential-reexec-loop-guard (livespec-runtime)

**Thread:** `plan/credential-reexec-loop-guard/` ·
**Ledger anchor:** `livespec-runtime-acf` (P1, `livespec-runtime` beads tenant) ·
**Design of record:** [`research/findings.md`](research/findings.md).

> Status is **derived from the ledger**, never stored in this file. Read it:
>
> ```bash
> cd /data/projects/livespec-runtime
> with-livespec-env.sh -- bd show livespec-runtime-acf --json
> ```
>
> Anything this handoff says about status is historical evidence with a
> timestamp. Re-measure before acting on it.

## The one-sentence version

A guard meant to stop an infinite credential re-exec loop is carried in an
environment variable that **every measured credential wrapper deletes** —
including the reference one — so the guard has never been able to fire, and any
repo whose wrapper cannot supply a required secret hangs silently and
unboundedly instead of failing with an error.

## Why this is P1 rather than an adopter footnote

Three properties compound:

1. **It is fleet-wide, not adopter-specific.** The reference wrapper drops the
   sentinel too. Fleet repos are safe only by luck: their secrets are present
   after one hop, so the guard is never consulted.
2. **It fails silently and open.** Every layer captures its child's output, so
   a hang emits zero bytes — for hours. It cost three sessions and roughly six
   hours of wall-clock before the cause was named.
3. **It fails in the direction that hides itself.** The symptom (a dispatch
   that "was killed with no output") looks like an infrastructure flake, so it
   invites retry rather than diagnosis.

Full measured evidence, with controls, is in `research/findings.md`.

## Recommended fix

Carry the "already re-execed" marker in **`argv`** rather than the environment,
because a wrapper's contract is to exec the argv it is handed while explicitly
rebuilding the environment. Fold in a bounded depth counter as belt-and-braces.
`decide_credentials` already receives `argv`, so the pure decision function
needs a new predicate, not a new input.

Rejected alternatives, with reasons, are in `research/findings.md` — in
particular **do not** fix this by allowlisting the variable in each wrapper.
That is the status quo, it exposes every third-party adopter, and it keeps a
guard that depends on the cooperation of the thing it guards against.

## Proposed slices (NOT yet filed as children — see "Next action")

| Slice | What it does | Depends on |
|---|---|---|
| S1 | Pure-brain change in `livespec_runtime/credentials.py`: detect the argv marker + depth, return `Fail` instead of `Reexec`. Paired tests prove termination when the ENV sentinel is absent. | — |
| S2 | Performer change in the `_bootstrap.py` entry points that build `reexec_argv`: append the marker, and strip it before handing argv to the real parser. | S1 |
| S3 | Diagnosability: give the dispatcher subprocess call a timeout and/or stream child output, so a future hang anywhere in the chain is visible. Independent of S1/S2 and separately valuable. | — |
| S4 | Release + fan-out: cut a `livespec-runtime` release and let the pin fan-out carry it, since consumers vendor this module. | S1, S2 |

S1 and S2 must land together in consumers' eyes: the guard is only correct when
the producer of the marker and its detector agree.

## Verification this thread owes

The fix is only "done" when it is exercised live, not merely merged and green.
The natural live exercise already exists and needs no special harness:

- Attempt a dispatch into a repo whose wrapper genuinely cannot supply a
  required secret (`resume` lacks `GITHUB_PRIVATE_KEY`; homelab lacks both
  GitHub App values). **Before:** silent unbounded hang. **After:** it must
  terminate promptly with the existing `Fail` message naming the missing
  variables and the wrapper.
- Keep a control in the same pass: a dispatch into a fleet repo must still
  `Proceed` normally, so the fix is shown not to break the working path.

Do not treat a passing unit test alone as discharge; the whole defect class
here is "the checked thing was not the thing that runs."

## Read-first chain

1. This handoff.
2. [`research/findings.md`](research/findings.md) — measured evidence, the
   options matrix, and what must not be done.
3. `livespec_runtime/credentials.py` — `decide_credentials`,
   `CREDENTIAL_REEXEC_SENTINEL`, and the comment stating the assumption that
   does not hold.
4. The `scripts/bin/_bootstrap.py` performer in a consuming repo (e.g. the
   `livespec-orchestrator-beads-fabro` plugin cache) — `_self_heal_credentials`
   is where the re-exec is actually built and run.

## Next action

**File the slices above as children of `livespec-runtime-acf`**, then drive S1
and S2. They are ordinary implementation work: no spec amendment is required,
because this fixes an implementation against its own stated contract rather
than changing the contract.

One judgement call is deliberately left open for whoever picks this up: whether
the argv marker should be a documented, supported flag or an internal token the
entry points strip before parsing. Both satisfy the guard; the first is
honest about the CLI surface, the second keeps the surface clean. Decide it
when filing S2, and record the reason.

## Discipline (non-negotiable)

- Every tracked-file change goes through a worktree under
  `$HOME/.worktrees/livespec-runtime/<branch>` → PR → rebase-merge → primary
  refresh → worktree removal. Never commit on the primary checkout.
- Run `just install-worktree-pack` then `git checkout -- .livespec.jsonc`
  immediately after creating any worktree.
- Product `.py` changes follow the Red-Green-Replay protocol. S1/S2/S3 all
  touch product Python, so they are in scope for it; this planning document is
  not.
- Use `mise exec -- git …` for git writes so the hooks run. **Never pass
  `--no-verify`**; if a hook fails, fix the cause or halt and report.
- Secrets are probe-only: `printenv NAME | wc -c`, never echo a value.

## Provenance

Found by the `plan/spec-side-autonomy` thread in the `livespec` repo while
completing leg 2 of `livespec-jvdvx4.2` (the twelve-repo `spec_governance`
backfill). The three adopter repos could not be factory-dispatched; diagnosing
why surfaced this. Leg 2 itself completed by hand-landing those three, so this
defect blocks no other work at the time of writing.
