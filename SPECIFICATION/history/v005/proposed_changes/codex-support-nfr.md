---
topic: codex-support-nfr
author: codex-gpt-5
created_at: 2026-06-19T17:43:19Z
---

## Proposal: Codex contributor support and runtime neutrality

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

State the Codex support requirement for livespec-runtime contributors while preserving the library's agent-runtime-neutral public surface.

### Motivation

The family-wide Codex audit found that livespec-runtime has a governed specification but no active Codex-specific non-functional requirement. Runtime is a shared library rather than an agent Driver, so its Codex requirement should cover contributor workflow, manual verification, and avoiding agent-runtime coupling.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md`, add a paragraph under `## Task-runner discipline` or another existing contributor-tooling section without introducing a new H2. The text should require that Codex can contribute through `AGENTS.md` and repo hooks, state that runtime does not currently need project-local `.agents/skills/` adapters because it exposes importable library code rather than a user-facing livespec Driver surface, forbid runtime code from branching on Claude/Codex/Pi agent identity, and require any future Codex adapter or e2e proof involving runtime to be documented and manually verified before support is claimed.
