# livespec-runtime

Shared runtime library for livespec-governed projects.

Hosts runtime code consumed by canonical [`livespec`](https://github.com/thewoolleyman/livespec) skills, impl-plugin skills, doctor invariants, hooks, and CI workflows. Initial scope is `livespec_runtime.cross_repo` (cross-repo work-item dependency resolution per `livespec/SPECIFICATION/contracts.md` §"Cross-repo dependency awareness").

This library is NOT enforcement-suite code — those live in [`livespec-dev-tooling`](https://github.com/thewoolleyman/livespec-dev-tooling). The split is intentional: enforcement-suite is build-time tooling consumed via `[dependency-groups].dev`; runtime is invoked at sub-command execution time and consumed via `[project.dependencies]` or `[dependency-groups].dev` depending on the consumer.

## Status

**v0.3.1 — cross_repo resolution surface shipped.** `livespec_runtime.cross_repo` is fully implemented: typed `DependsOnEntry` union, `providers.github`, `retry`, and `resolve_ref` all landed in v0.2.0 (2026-05-24). v0.3.x carries follow-on fixes and polish. The module is present and in active use by livespec consumers.

## Consumption

Consumers add this library via `uv` git source:

```toml
[dependency-groups]
dev = [
    "livespec-runtime",
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.3.1" }
```

Or as a runtime dependency:

```toml
[project]
dependencies = [
    "livespec-runtime>=0.3.1",
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.3.1" }
```

## Governance

- The `SPECIFICATION/` tree at the repo root is the live spec for this library, governed by livespec via its own seeded template (per epic `li-6d2wpj` Phase: seed). Until seeded, livespec sub-commands targeting this tree fail-fast with a precondition error directing the user to seed first.
- This library's own impl tracking lives in a per-repo beads/Dolt **tenant database** on the shared dolt-server (tenant `livespec-runtime`), via [`livespec-impl-beads`](https://github.com/thewoolleyman/livespec-impl-beads); the beads client config is committed at `.beads/config.yaml`. The pre-cutover plaintext `work-items.jsonl` / `memos.jsonl` snapshot is frozen read-only under [`archive/`](archive/README.md).
- The `compat` block on the `livespec-runtime` top-level key in `.livespec.jsonc` pins this library's compatibility with `livespec-core` per the pin-and-bump contract.

## Observability

The livespec family dogfoods its own telemetry. CI runs, Red→Green commit-gate cycles, the beads+fabro dispatcher, sandbox runs, and harness sub-agents are published to a shared Honeycomb environment:

- **[livespec family — all activity](https://ui.honeycomb.io/thewoolleyweb/environments/livespec/board/krThv8DvcwS)** — the cross-repo activity board (Honeycomb, `livespec` environment).
