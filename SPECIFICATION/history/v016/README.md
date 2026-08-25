# livespec-runtime — specification

This tree is the natural-language specification for `livespec-runtime`,
the shared cross-repo dependency-resolution runtime library consumed by
`livespec`, by every `livespec-impl-*` plugin, and by
`livespec-dev-tooling`. The library dogfoods `livespec` — every change
to this `SPECIFICATION/` flows through `/livespec:propose-change`,
`/livespec:critique`, `/livespec:revise`, `/livespec:doctor`, and
`/livespec:prune-history`.

## File map

- `spec.md` — purpose, scope boundary, terminology, public surface, and
  lifecycle. The orienting document; read this first.
- `contracts.md` — module-level public surface, resolution semantics,
  retry policy, `.livespec.jsonc` `compat` block shape, consumption
  shape, system dependencies, versioning rules.
- `constraints.md` — architecture-level constraints: public-surface
  rules, resolution-substrate rules, provider rules, process boundaries,
  dependency rules, forbidden patterns.
- `non-functional-requirements.md` — contributor-facing invariants:
  task-runner discipline, repo layout, build/release, test discipline,
  spec-evolution rules.
- `scenarios.md` — Gherkin scenarios per public-surface path.

## Read order for a new contributor

1. `spec.md` — what the library is and where its boundary sits.
2. `contracts.md` — the importable surface and resolution semantics.
3. `constraints.md` — architectural rules the implementation honors.
4. `non-functional-requirements.md` — how the repo is built, tested,
   and released.
5. `scenarios.md` — the worked examples for each contract path.

## Lifecycle

Every change here lands through livespec's standard loop. Direct edits
outside a `revise` snapshot are out-of-process; doctor's static phase
will flag drift.

## Upstream pointers

When any rule in this tree appears to conflict with `livespec`'s
`SPECIFICATION/`, the upstream rule wins. The `compat.pinned` value in
the repo-root `.livespec.jsonc`'s `livespec-runtime` section records
which `livespec` release this spec is currently consistent with.
