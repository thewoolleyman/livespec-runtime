---
topic: seed
author: livespec-seed
---

## Proposal: seed

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md
- SPECIFICATION/non-functional-requirements.md
- SPECIFICATION/scenarios.md
- SPECIFICATION/README.md

### Summary

Initial seed of the specification from user-provided intent.

### Motivation

Shared runtime library for livespec-governed projects. Hosts cross-repo work-item dependency resolution code — the typed DependsOnEntry union (local / sibling_work_item / pull_request / branch), the GitHub gh-CLI provider, the 3-attempt 1s/2s/4s retry policy, and the resolve_ref exhaustive-walk entry point — consumed by canonical livespec skills, impl-plugin skills, doctor invariants, hooks, and CI workflows. Sibling to livespec, livespec-impl-* plugins, and livespec-dev-tooling (which owns enforcement-suite code; this library owns runtime code consumed at sub-command execution time). Cross-repo coordination via pin-and-bump on the `livespec-runtime` compat block in each consumer's .livespec.jsonc, mirroring the impl-plugin and dev-tooling shape.

### Proposed Changes

Shared runtime library for livespec-governed projects. Hosts cross-repo work-item dependency resolution code — the typed DependsOnEntry union (local / sibling_work_item / pull_request / branch), the GitHub gh-CLI provider, the 3-attempt 1s/2s/4s retry policy, and the resolve_ref exhaustive-walk entry point — consumed by canonical livespec skills, impl-plugin skills, doctor invariants, hooks, and CI workflows. Sibling to livespec, livespec-impl-* plugins, and livespec-dev-tooling (which owns enforcement-suite code; this library owns runtime code consumed at sub-command execution time). Cross-repo coordination via pin-and-bump on the `livespec-runtime` compat block in each consumer's .livespec.jsonc, mirroring the impl-plugin and dev-tooling shape.
