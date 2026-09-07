---
topic: sentinel-readme-self-version-literals
author: claude-opus-5
created_at: 2026-09-07T11:57:20Z
spec_commitments:
  impl_followups:
    - id_hint: sentinel-readme-self-version-literals
      description: |
        Already filed as livespec-runtime-2rg (backlog): add README.md to release-please-config.json extra-files with the generic updater; add x-release-please-version sentinels to README.md:11, :24 and :36; drop the version anchor from livespec_runtime/cross_repo/providers/__init__.py:7 ('At v0.3.0 the only provider is' -> 'The only provider is'); verify the updater rewrites exactly the sentinelled README lines by running release-please's GenericUpdater against the real file, since its failure mode is silence.
---

## Proposal: sentinel-readme-self-version-literals

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Widen the ratified x-release-please-version sentinel mechanism from SPECIFICATION/contracts.md alone to every consumer-facing self-version literal this library carries — README.md's Status line and its two consumption examples included — by naming README.md beside contracts.md in the §"Release flow" bullet and in release-please's extra-files, and state that module docstrings carry no self-version literal at all. The three contracts.md literals the bullet already governs have stayed current across twenty spec revisions; the four literals outside it (README.md:11, :24, :36 and livespec_runtime/cross_repo/providers/__init__.py:7) rotted to v0.3.x against 0.26.0.

### Motivation

livespec-runtime is the fleet's shared runtime LIBRARY, consumed by git tag (livespec at v0.22.1, livespec-orchestrator-beads-fabro at v0.21.1, livespec-orchestrator-git-jsonl at v0.20.0), so consumers copy-paste version literals from this repository. history/v002's doctor-findings-bundle ratified the sentinel convention for contracts.md and it demonstrably works: release commit 1c211eb (0.26.0) rewrote exactly pyproject.toml and contracts.md. README.md duplicates the same consumption snippet WITHOUT sentinels and is NOT in extra-files, and the repository has already tried hand-refreshing twice — livespec-runtime-pcy (PR #45) moved README from v0.1.0 to v0.3.1 and it rotted 23 minor versions; PR #14 moved a docstring from v0.2.0 to v0.3.0 and it rotted again. A rule that governs only one of the two files consumers read is half a rule. The docstring case is different in kind: a present-tense claim about package shape anchored to a version says nothing a directory listing does not, so the clause forbids the anchor rather than sentinelling it. Implementation is already filed as livespec-runtime-2rg; this proposal gives it its ratified basis. Measured across the fleet 2026-09-07: no other livespec repository carries a consumer-facing self-version literal, so this convention is this library's own and the widening is internal to it.

### Proposed Changes

In `SPECIFICATION/non-functional-requirements.md` §"Release flow", REPLACE the bullet that begins "The consumer-facing example version literals in `SPECIFICATION/contracts.md` carry inline `x-release-please-version` sentinel comments." with the following bullet, verbatim:

- Every consumer-facing self-version literal — the example version tags in `SPECIFICATION/contracts.md` and the Status line and consumption examples in `README.md` — MUST carry an inline `x-release-please-version` sentinel comment, and the release-please config (`release-please-config.json`) MUST list both `SPECIFICATION/contracts.md` and `README.md` under `extra-files` with the `generic` updater so each release rewrites every such literal in place. A self-version literal outside that mechanism is a defect, not a chore: hand-refreshed literals in this repository rotted twice (README.md v0.1.0→v0.3.1 by PR #45, then 23 minor versions behind; a docstring v0.2.0→v0.3.0 by PR #14, likewise) while every sentinelled literal stayed current across twenty revisions. Module docstrings MUST NOT carry a self-version literal at all: a present-tense statement about the package's shape is written without a version anchor, because the anchor adds nothing the tree does not already state and is guaranteed to rot. The authoritative location for what the consumer copy-paste should pin to is therefore always the freshest commit on `master`.

No other section changes. The existing sentence pair is subsumed, not duplicated.
