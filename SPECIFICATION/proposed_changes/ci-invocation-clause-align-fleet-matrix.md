---
topic: ci-invocation-clause-align-fleet-matrix
author: claude-opus-4-8
created_at: 2026-07-10T03:50:04Z
---

## Proposal: Align the CI-invocation clause with the fleet per-target-matrix convention

### Target specification files

- non-functional-requirements.md

### Summary

Revise the `non-functional-requirements.md` §"Task-runner discipline"
clause that currently mandates *"Lefthook pre-push and CI MUST both
invoke `just check` (not the individual targets)."* Keep the pre-push
requirement (pre-push MUST invoke the full `just check` aggregate), but
replace the CI half: CI MAY run the aggregate as a per-target matrix of
individual `just check-<slug>` jobs, provided a completeness guard
(`check-aggregate-completeness`) prevents the wired set from silently
dropping a canonical slug. This matches the convention every other
Python repo in the livespec fleet — including livespec core itself —
actually follows.

### Motivation

The clause as written is contradicted by the entire fleet, making
`livespec-runtime` the sole outlier rather than a conformant member:

- A fleet audit (2026-07-10) of all nine livespec-governed repos found
  that **every** Python repo runs its CI as a per-target matrix of
  individual `just check-<slug>` jobs; **none** invokes `just check` as
  a single command. Only `dolt-server` invokes the aggregate directly,
  and only because it is a trivial shell repo (one `shellcheck` call).
- livespec core's own spec **prescribes** the matrix: `livespec`
  `SPECIFICATION/contracts.md` §"Pre-commit step ordering" (zero-`.py`
  subsetting) mandates the `setup` change-detection job, a Python-code
  matrix gated on `py_changed`, and an unconditional repo-metadata
  matrix — the exact per-target shape this clause forbids.
- Both Driver repos' NFRs **explicitly authorize** per-target `just
  <target>` delegation in CI.

The per-target matrix is a deliberate, load-bearing design, not drift:
it buys granular branch-protection status checks, job-level
parallelism, the second-checkout `check-doctor-static` job, and
zero-`.py` subsetting for fast docs-only feedback. Forcing runtime's CI
back to a single `just check` invocation to satisfy the current clause
would sacrifice all four and make runtime diverge from every sibling.

The clause's *intent* — CI must enforce the same gates as local, with
no silent drift — remains correct and is preserved: the completeness
guard keeps the CI matrix from dropping a canonical slug, and
broadening the matrix to the full canonical aggregate is tracked as
dedicated fleet work (the CI-aggregate-coverage epic), not left
implicit.

This revision resolves gap `gap-rsfmjjzl` (work-item
`livespec-runtime-woe5gi`) as spec-side drift correction rather than an
implementation change.

### Proposed Changes

In `non-functional-requirements.md` §"Task-runner discipline", replace
the clause:

> - The `just check` target is the load-bearing aggregate. It MUST run
>   lint, format-check, types, tests, and coverage in that order and
>   exit non-zero on any failure. Lefthook pre-push and CI MUST both
>   invoke `just check` (not the individual targets).

with:

> - The `just check` target is the load-bearing aggregate. It MUST run
>   lint, format-check, types, tests, and coverage in that order and
>   exit non-zero on any failure. Lefthook pre-push MUST invoke `just
>   check` (the full aggregate). CI MAY run the aggregate as a
>   per-target matrix of individual `just check-<slug>` jobs — for
>   granular branch-protection status checks, job-level parallelism, the
>   second-checkout `check-doctor-static` job, and zero-`.py` subsetting
>   per livespec `SPECIFICATION/contracts.md` §"Pre-commit step
>   ordering" — provided a completeness guard
>   (`check-aggregate-completeness`) prevents the wired set from silently
>   dropping a canonical slug. CI MUST NOT hand-pick a subset that omits
>   a canonical slug the aggregate runs without that guard flagging the
>   omission. Broadening the CI matrix to cover the full canonical
>   aggregate is tracked fleet-wide by the CI-aggregate-coverage epic.
