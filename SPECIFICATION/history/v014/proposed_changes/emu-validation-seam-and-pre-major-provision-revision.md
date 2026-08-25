---
proposal: emu-validation-seam-and-pre-major-provision.md
decision: modify
revised_at: 2026-08-25T15:15:46Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Both findings accepted in substance, recorded as MODIFY because realizing them coherently required amending a file the proposal did not name as a target. Finding 1 fixes the two choices v013 deferred: validation is enforced at construction via InvalidAttentionItemIdError, so the composer refuses the call — form (i) of the three surfaced-failure forms constraints.md permits. The producer-emission-boundary alternative is rejected on the record because producers live in consumer repositories, making it a rule this library states and cannot verify — the exact mechanism that let the silent-drop gap survive. Finding 2 adds the pre-major provision so a Major-classified change below 1.0.0 releases as a minor bump, plus the Release-flow clause binding release-please-config.json to that rule, because a rule the automation contradicts is not a rule. Independent read-only Fable review returned BLOCKERS on the first pass and was right: the ratified scenario demanded a RESULT-borne failure that the mandated raise makes impossible — the third consecutive instance of jointly-unsatisfiable clauses in this repo, each at the seam between an edited file and an unedited one. Corrected, and the re-review returned NO BLOCKERS.

## Modifications

Beyond the proposal's named targets (contracts.md, constraints.md, non-functional-requirements.md), this ratification ALSO amends SPECIFICATION/scenarios.md. The scenario 'composition surfaces an invalid candidate rather than shortening the list' had a Then requiring that 'the result MUST surface the invalid candidate as an explicit failure or malformed marker, and MUST NOT be a one-element list' — phrased in the file's returned-value idiom and naming only the two result-borne surfaced-failure forms. Finding 1 mandates the third form, refusing the call, under which no result exists at all, so the scenario could not be satisfied as written and a conformance-test author following scenarios.md would contradict one following contracts.md. Its Then is rewritten into the file's raise idiom: InvalidAttentionItemIdError is raised; the error message names the rejected id; no list is returned at all, the valid candidate MUST NOT be returned alone. The scenario HEADING is unchanged, so its tests/heading-coverage.json mapping still keys correctly.

## Resulting Changes

- contracts.md
- constraints.md
- non-functional-requirements.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: fable
reviewer_identity: fable
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-25T15:14:00Z
verdict: NO BLOCKERS
proposal_stem: emu-validation-seam-and-pre-major-provision
content_digest: df7b7022866f674159b36498c70c606fbc06c5e2fe8f634e36b0b7d4870a6caa
