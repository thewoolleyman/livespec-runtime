---
topic: spec-stated-clause-evidence
author: claude-opus-5-5 (spec-implementation-lockstep)
created_at: 2026-11-09T03:22:09Z
---

## Proposal: A spec-stated verdict carries the clause evidence its parser reads

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

Add a `ClauseEvidence` export to `livespec_runtime.spec_stated` and an `evidence` field to `SpecStatedVerdict`, a tuple of `ClauseEvidence` that defaults to empty. State the rule by which `parse_verdict` reads an optional `evidence` list from a model response. Add one scenario that pins the rule. Today the ratified section lists the verdict's fields as a closed set of four and names no `ClauseEvidence`, so the public-surface inventory check rightly refuses exporting it.

### Motivation

livespec-runtime-bxbyko must upstream the surface that livespec-orchestrator-beads-fabro's vendored copy of `livespec_runtime.spec_stated` already ships and reads: `verdict.evidence` in its Definition-of-Done governing-record and governing-heading judgement code. Its factory run 01M6Z4E59TG1 implemented the field and the parser (commit f150de8, which passes the full suite). It stopped because the item's Definition of Done also requires `ClauseEvidence` in `__all__`, and the public-surface inventory test fails any export that the ratified `### livespec_runtime.spec_stated` section does not name. Master already carries the bare `ClauseEvidence` class (822f0b3), unexported and unspecified. Until the contract states this surface, a re-vendor from runtime master breaks the orchestrator with an AttributeError, and the one shared judgement is not the same in both consumers. livespec-orchestrator-git-jsonl's vendored copy carries none of this surface and reads no `.evidence`, so the defaulted field is additive for it.

### Proposed Changes

In `SPECIFICATION/contracts.md` §"Module-level public surface" → `### livespec_runtime.spec_stated`:

1. Insert a new bullet immediately BEFORE the `SpecStatedVerdict` bullet:

   - `ClauseEvidence` — frozen, slotted, kw-only dataclass: one verbatim quotation offered in support of a judgement. Fields: `heading: str` (REQUIRED; the text of the heading the quotation is drawn from); `quote: str` (REQUIRED; non-blank, the quoted clause text).

2. In the `SpecStatedVerdict` bullet, append a fifth field after `rationale: str` (REQUIRED):

   `evidence: tuple[ClauseEvidence, ...]` (OPTIONAL; defaults to the empty tuple; the quotations the model's response offered, in response order). Constructing a verdict without `evidence` MUST yield an empty tuple, so every caller that builds a verdict from the four required fields keeps working unchanged.

3. In the `parse_verdict` bullet, append:

   The response MAY carry an `evidence` key. When the key is absent or `null`, the verdict's `evidence` MUST be the empty tuple. When it is a list whose every entry is an object carrying a string `heading` and a non-blank string `quote`, the verdict's `evidence` MUST be those entries as `ClauseEvidence` values, in list order. A non-list `evidence` value, a non-object entry, or an entry whose `heading` is not a string or whose `quote` is not a non-blank string MUST yield a `Failure` whose error has `field` `"evidence"`. An entry's `heading` is carried as given: unlike `stated_by`, it is NOT checked against `headings`, so a quotation's provenance is the consumer's to grade.

In `SPECIFICATION/scenarios.md`, insert immediately AFTER `## Scenario: parse_verdict names the offending field or the parse error`:

```markdown
## Scenario: parse_verdict reads optional clause evidence in order

- **Given** a well-formed response whose `evidence` is a list of two objects, each carrying a string `heading` and a non-blank string `quote`
- **When** `parse_verdict` is called
- **Then** the result MUST be a `Success` whose verdict's `evidence` equals the two entries as `ClauseEvidence` values, in response order
- **And** the same response without an `evidence` key, or with `evidence` `null`, MUST yield a verdict whose `evidence` is the empty tuple
- **And** a response whose `evidence` is not a list, carries a non-object entry, or carries an entry whose `quote` is blank MUST yield a `Failure` whose `SpecStatedParseError` has `field` `"evidence"`
```

The revise that accepts this proposal MUST add a `tests/heading-coverage.json` row for the new scenario heading in the same change, with `test` `"TODO"`, `work_item` `livespec-runtime-bxbyko`, and a non-empty `reason` naming bxbyko as the item whose relaunch binds the test.
