# livespec-runtime

Shared runtime library for livespec-governed projects.

Hosts runtime code consumed by canonical [`livespec`](https://github.com/thewoolleyman/livespec) skills, impl-plugin skills, doctor invariants, hooks, and CI workflows. Initial scope is `livespec_runtime.cross_repo` (cross-repo work-item dependency resolution per `livespec/SPECIFICATION/contracts.md` §"Cross-repo dependency awareness").

This library is NOT enforcement-suite code — those live in [`livespec-dev-tooling`](https://github.com/thewoolleyman/livespec-dev-tooling). The split is intentional: enforcement-suite is build-time tooling consumed via `[dependency-groups].dev`; runtime is invoked at sub-command execution time and consumed via `[project.dependencies]` or `[dependency-groups].dev` depending on the consumer.

## Status

**v0.1.0 — initial scaffold.** Empty `livespec_runtime.cross_repo` skeleton + scaffold. The cross_repo implementation (typed `DependsOnEntry` union, `providers.github`, `retry`, `resolve_ref`) lands as v0.2.0 per work-item `li-aclzfe` under parent epic `li-6d2wpj`.

## Consumption

Once `v0.2.0` cuts (the first useful release), consumers add this library via `uv` git source:

```toml
[dependency-groups]
dev = [
    "livespec-runtime",
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.2.0" }
```

Or as a runtime dependency:

```toml
[project]
dependencies = [
    "livespec-runtime>=0.2.0",
]

[tool.uv.sources]
livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.2.0" }
```

## Governance

- The `SPECIFICATION/` tree at the repo root is the live spec for this library, governed by livespec via its own seeded template (per epic `li-6d2wpj` Phase: seed). Until seeded, livespec sub-commands targeting this tree fail-fast with a precondition error directing the user to seed first.
- The `work-items.jsonl` / `memos.jsonl` at the repo root carry this library's own impl tracking via [`livespec-impl-plaintext`](https://github.com/thewoolleyman/livespec-impl-plaintext).
- The `compat` block on the `livespec-runtime` top-level key in `.livespec.jsonc` pins this library's compatibility with `livespec-core` per the pin-and-bump contract.
