---
proposal: scenarios-parse-depends-on-entry-railway.md
decision: accept
revised_at: 2026-08-26T12:32:39Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-5
---

## Decision and Rationale

Accepted as filed. The two corrected scenarios now describe what the shipped boundary does: `parse_depends_on_entry` returns `Result[DependsOnEntry, CrossRepoSchemaError]`, and for BOTH scenario inputs it returns rather than raises -- an unknown `kind` takes an early `return Failure(...)` before the try block is entered, and a missing per-kind required field raises inside `_require_field` only to be discharged by `except CrossRepoSchemaError as invalid: return Failure(invalid)`. The independent reviewer checked the escape paths adversarially and found no input matching either Given-clause that leaves as an exception. The replacement names the concrete `Failure` container the code constructs and is verbatim consistent with ratified contracts.md, which says the function returns a `Failure` and does NOT raise. The `And` lines about 'the error detail' needed no co-edit because that phrase names an attribute of the error object rather than how the error arrived. The adjacent `parse_cross_repo_manifest` scenario is deliberately left saying 'is raised', verified against code rather than merely left alone: that function returns a bare `CrossRepoManifest`, has no try, and lets `_require_field` propagate -- and contracts.md ratifies that the two boundaries differ and callers MUST NOT assume one idiom covers both. The mapped tests already asserted the Result behaviour and pass; the reviewer ran them (5 passed) and ran `heading_coverage` itself (exit 0), confirming no co-edit of the registry is required. WHY THIS DEFECT SURVIVED, recorded because it outlives the fix: `heading_coverage` verifies that a scenario HAS a linked test, never that the scenario's Then-clause matches what that test ASSERTS -- so a ratified scenario stated the opposite of its own PASSING test with every gate green. Filed as livespec-dev-tooling-0z11. Also recorded: v016 did NOT introduce this. That pass changed contracts.md and touched scenarios.md by zero lines; restating the contract as shipped merely EXPOSED a latent falsehood. INDEPENDENCE DISCLOSURE, recorded deliberately rather than left implicit: this proposal was AUTHORED BY THE SAME SESSION THAT IS DECIDING IT, earlier the same day, so this ratification lacked the fresh-eyes separation a proposal inherited from another session provides; and the reviewer's model family matches the deciding session's because `ratification_reviewer_model` was pinned fleet-wide to `opus` today for availability, not chosen for this proposal. Both reductions were disclosed to the reviewer in its brief so it would read harder as the only independent check, and are recorded here so a maintainer can weigh or reverse them on sight. The independent-review floor was met in full: a separate, read-only, independently spawned reviewer returned the literal verdict NO BLOCKERS for these exact bytes, having re-computed the digest itself.

## Resulting Changes

- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-08-26T12:10:37Z
verdict: NO BLOCKERS
proposal_stem: scenarios-parse-depends-on-entry-railway
content_digest: f9c169569c4a054b6c6cf54c1fc7b41a5e588fe18df428b85794d7e6b559bda9
