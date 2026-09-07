---
proposal: sentinel-readme-self-version-literals.md
decision: accept
revised_at: 2026-09-07T12:29:13Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed. The proposal widens a mechanism this repository already ratified and has demonstrably relied on: history/v002 established the x-release-please-version sentinels for contracts.md, and release eeeb8b4 (0.27.0) rewrote all three of that file's literals during this very revise pass, while README.md's three literals sat unchanged at v0.3.1 because README.md is not in release-please's extra-files. The independent reviewer verified every factual claim against the tree (three sentinelled literals current, README absent from extra-files, PR #45 and PR #14 as the two failed hand-refreshes) and returned NO BLOCKERS, noting only that 'twenty revisions' is 19 by exact count — rounding, not a misstatement. Placement in non-functional-requirements.md is right under the Boundary litmus: this governs the repo's own release automation and is invisible to a library consumer, so no scenario is owed. Implementation is already filed as livespec-runtime-2rg.

## Resulting Changes

- non-functional-requirements.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-09-07T12:05:57Z
verdict: NO BLOCKERS
proposal_stem: sentinel-readme-self-version-literals
content_digest: d32f35b2d27737af2da735ecbf1b723fc91317b3cf0a16acfe4346abcfb52549
