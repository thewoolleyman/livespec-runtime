---
proposal: lockstep-declared-mapping-amendment.md
decision: accept
revised_at: 2026-08-25T14:20:03Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted. v012's lockstep constraint could not be conformed to: it required the kind-to-prefix correspondence to be by equal literal text and forbade naming a prefix differently from its kind, while its companion note required closing the gap to preserve every already-emitted id and offered admitting `human-valve` as a prefix as the remedy. compose_needs_attention emits `valve:` for kind="human-valve", so `valve` must stay accepted or emitted ids break, yet `valve` matches no kind by literal text, so the bijection fails; admitting `human-valve` adds an unmatched entry no producer emits. This replaces literal-text equality with a total, injective mapping declared as a ratified table in contracts.md, preserving both the kind vocabulary and every emitted id while keeping drift mechanically refusable. Ratified under the maintainer's standing directive that spec changes needed by the gap children route through propose-change, confirmed in-session. Independent read-only Fable review initially returned BLOCKERS on these bytes: the contracts.md grammar bullet still enumerated the three-part prefixes without `internal`, contradicting the new table and the amended constraints text — the same jointly-unsatisfiable-clause defect class recurring inside its own fix. That was corrected (the enumeration now includes `internal`), and the re-review of the corrected bytes returned NO BLOCKERS, confirming the enumeration, the table, constraints.md and the shipped _THREE_PART_PREFIXES all state the same accepted set, and that no third statement of that set exists anywhere in the tree.

## Resulting Changes

- constraints.md
- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-25T14:18:30Z
verdict: NO BLOCKERS
proposal_stem: lockstep-declared-mapping-amendment
content_digest: 234f9d7541e1536bfdf4b3a3782156585fb31e457d3314b3bf3eac6e779eaccf
