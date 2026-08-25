---
topic: lockstep-declared-mapping-amendment
author: claude-opus-5
created_at: 2026-08-25T13:55:22Z
---

## Proposal: Assert kind-to-prefix lockstep over a declared mapping rather than literal text equality

### Target specification files

- SPECIFICATION/constraints.md
- SPECIFICATION/contracts.md

### Summary

The v012 lockstep constraint requires the AttentionKind-to-prefix correspondence to be "by equal literal text" and forbids "naming a prefix differently from its kind", while its companion non-conformance note requires that closing the gap "MUST preserve every id already emitted" and offers admitting `human-valve` as an accepted prefix as a remedy. For the `human-valve` case those requirements are not jointly satisfiable, so v012 as ratified cannot be conformed to. This replaces literal-text equality with an explicitly declared, ratified kind-to-prefix MAPPING over which the bijection is asserted, preserving the kind vocabulary, preserving every emitted id, and still forbidding drift.

### Motivation

Surfaced while implementing the v012 gap on `livespec-runtime/livespec-runtime-wfl`, before any code changed. `compose_needs_attention` emits `valve:<verb>:<work_item>` for `kind="human-valve"`, so the prefix `valve` MUST remain accepted or every already-emitted human-valve id stops validating — which the same constraint forbids. But a retained `valve` prefix has no `AttentionKind` member equal to it by literal text, so the prefix-to-kind direction of the ratified bijection fails. Admitting `human-valve` alongside `valve` does not repair this: it adds a second entry with no counterpart, leaving the bijection broken in both directions. Only three exits exist. Renaming the kind `human-valve` to `valve` would change a ratified closed vocabulary and break every consumer that matches on the kind literal. Migrating emitted ids to a `human-valve:` prefix would break existing natural keys, which v012 explicitly forbids. Asserting the bijection over a declared mapping preserves the kind vocabulary AND every emitted id, and loses nothing that matters: the anti-drift property v012 wanted comes from the correspondence being total, injective, and mechanically checked, not from the two strings being spelled the same. The `internal` half of the gap was closed under v012 as written and is unaffected. This is the implementation revealing a specification defect — the Drift direction of the loop — filed under the maintainer's standing revise directive rather than worked around in code.

### Proposed Changes

In `SPECIFICATION/constraints.md` §"Public-surface constraints", the ratified lockstep bullet MUST be REPLACED. Its current text requires that "The correspondence MUST be by equal literal text" and that "naming a prefix differently from its kind is FORBIDDEN". The replacement MUST read:

> Every `AttentionKind` member MUST correspond to exactly one stable-ID prefix accepted by `validate_attention_item_id`, and every accepted prefix MUST correspond to exactly one `AttentionKind` member. The correspondence MUST be a total, injective mapping DECLARED in `contracts.md` §"Module-level public surface", not inferred from spelling; a kind and its prefix MAY differ in literal text where the declared mapping says so. Adding a kind without its prefix, adding a prefix without its kind, or introducing either without a corresponding entry in the declared mapping is FORBIDDEN. A mechanical check MUST assert the mapping is total and injective in both directions, so the two vocabularies cannot drift.

The companion non-conformance bullet MUST be amended to record what is now true: the `internal` half is CLOSED (the accepted-prefix set admits `internal`), and the remaining non-conformance is that no declared mapping artifact exists yet and no mechanical check asserts it. The sentence offering "admits `internal` and `human-valve` as accepted prefixes" as a remedy MUST be REMOVED, because admitting `human-valve` as a prefix is exactly the repair that does not work: it would leave `valve` unmatched while adding an unused prefix, and it would NOT be emitted by any producer.

In `SPECIFICATION/contracts.md` §"`livespec_runtime.attention_item`", the declared mapping MUST be stated as ratified content, so the mechanical check has a single source of truth:

| `AttentionKind` | stable-ID prefix | arity |
|---|---|---|
| `human-valve` | `valve` | three-part |
| `impl` | `impl` | two-part |
| `spec` | `spec` | three-part |
| `plan` | `plan` | two-part |
| `hygiene` | `hygiene` | three-part |
| `internal` | `internal` | three-part |
| `host-only` | `host-only` | three-part |

The section MUST state that `human-valve` is the ONE entry whose prefix differs in literal text from its kind, that the difference is retained deliberately to preserve every already-emitted `valve:` natural key, and that changing any prefix in this table is a MAJOR-version change because it invalidates ids already in circulation.

`SPECIFICATION/scenarios.md`'s scenario "every attention kind has a matching stable-ID prefix" MUST be updated so its Then clause asserts the declared mapping is total and injective, rather than asserting set equality by literal text, which the amended constraint no longer requires.
