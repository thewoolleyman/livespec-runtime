---
proposal: scenario-tier-coverage-invariant.md
decision: accept
revised_at: 2026-05-31T21:05:24Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-4-8
---

## Decision and Rationale

Epic li-scetier Wave 3. Pre-approved design (user-approved; not re-litigated). The scenario-tier coverage invariant is restated independently in livespec-runtime's own non-functional-requirements.md §"Test discipline" because runtime's SPECIFICATION does NOT inherit normative rules by reference from another repo's SPECIFICATION. Added as a new bullet under the existing §"Test discipline" H2 (no new `## ` heading), so no tests/heading-coverage.json co-edit is required. Every normative MUST/MAY clause from the canonical restatement is preserved; version references use runtime's project-name-prefixed convention (livespec-dev-tooling v0.9.0+).

## Resulting Changes

- non-functional-requirements.md
