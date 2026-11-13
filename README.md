# livespec-runtime

Shared runtime library for livespec-governed projects.

Hosts runtime code consumed by canonical [`livespec`](https://github.com/thewoolleyman/livespec) skills, impl-plugin skills, doctor invariants, hooks, and CI workflows. Initial scope is `livespec_runtime.cross_repo` (cross-repo work-item dependency resolution per `livespec/SPECIFICATION/contracts.md` §"Cross-repo dependency awareness").

This library is NOT enforcement-suite code — those live in [`livespec-dev-tooling`](https://github.com/thewoolleyman/livespec-dev-tooling). The split is intentional: enforcement-suite is build-time tooling consumed via `[dependency-groups].dev`; runtime is invoked at sub-command execution time and consumed via `[project.dependencies]` or `[dependency-groups].dev` depending on the consumer.

## Status

**v0.30.4 — cross_repo resolution surface shipped.** <!-- x-release-please-version --> `livespec_runtime.cross_repo` is fully implemented: typed `DependsOnEntry` union, `providers.github`, `retry`, and `resolve_ref` have all landed. The module is present and in active use by livespec consumers. See [`CHANGELOG.md`](CHANGELOG.md) for the per-release history.

## Consumption

Consumers add this library via `uv` git source:

```toml
[dependency-groups]
dev = [
    "livespec-runtime",
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.30.4" } # x-release-please-version
```

Or as a runtime dependency:

```toml
[project]
dependencies = [
    "livespec-runtime>=0.30.4", # x-release-please-version
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.30.4" } # x-release-please-version
```

## Mutation kill matrix

`just mutation-kill-matrix` runs the shared Rule-26 engine on demand over
`livespec_runtime/`, excluding the vendored CC0 fractional-indexing port. It
collects the repository's tests and writes `reports/mutation-kill-matrix.json`,
including each mutant's killers, survivors, baseline failures, unapplied
coverage and redundancy candidates. The first-party wrapper around that port
is included.

Engine flags pass through, for example `just mutation-kill-matrix --help`.
The result cache is `reports/mutation-kill-matrix-cache.json`; passing
`--previous-report <path>` also writes
`reports/mutation-kill-matrix-changes.json`. Reports and worker outputs are
generated artifacts; retain a report and its checksum with the plan evidence.

On fleet hosts, execute the real run through an approved persistent cluster
Job, with the released engine and target revision recorded. Configuration
alone is not a completed run. This recipe is advisory and runs only on demand;
it is absent from the check aggregate, commit and push hooks, and required PR
CI. A redundancy candidate still needs intent review and the plan's pruning
safeguards before removal.

## Governance

- The `SPECIFICATION/` tree at the repo root is the live spec for this library, governed by livespec via its own seeded template (per epic `li-6d2wpj` Phase: seed). Until seeded, livespec sub-commands targeting this tree fail-fast with a precondition error directing the user to seed first.
- This library's own impl tracking lives in a per-repo beads/Dolt **tenant database** on the shared dolt-server (tenant `livespec-runtime`), via [`livespec-orchestrator-beads-fabro`](https://github.com/thewoolleyman/livespec-orchestrator-beads-fabro); the beads client config is committed at `.beads/config.yaml`. The pre-cutover plaintext `work-items.jsonl` / `memos.jsonl` snapshot is frozen read-only under [`archive/`](archive/README.md).
- The `compat` block on the `livespec-runtime` top-level key in `.livespec.jsonc` pins this library's compatibility with `livespec-core` per the pin-and-bump contract.

## Observability

The livespec family dogfoods its own telemetry. CI runs, Red→Green commit-gate cycles, the beads+fabro dispatcher, sandbox runs, and harness sub-agents are published to a shared Honeycomb environment:

- **[livespec family — all activity](https://ui.honeycomb.io/thewoolleyweb/environments/livespec/board/krThv8DvcwS)** — the cross-repo activity board (Honeycomb, `livespec` environment).
