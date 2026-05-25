---
proposal: doctor-findings-bundle.md
decision: accept
revised_at: 2026-05-25T17:15:29Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

User authorized accept-all on the seven-proposal bundle. Combined effect: (a) strips five narrative v0.2.0 pins that described v0-line-stable behavior, (b) adopts the project-name-prefix convention for version references in spec prose, (c) wires release-please extra-files for the consumer-example tags, (d) corrects spec.md and contracts.md from 1s/2s/4s to 1s/2s backoff phrasing, (e) aligns the exhaustive-live-walk definition with what v1 actually walks (no local-clone view), (f) enumerates per-variant required fields under contracts.md, and (g) replaces the RefStatus JSON-roundtrip rule with explicit value-lookup-SHOULD / name-lookup-MUST-NOT phrasing.

## Resulting Changes

- spec.md
- contracts.md
- constraints.md
- non-functional-requirements.md
