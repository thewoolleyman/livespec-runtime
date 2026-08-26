---
topic: scenarios-parse-depends-on-entry-railway
author: claude-opus-5
created_at: 2026-08-26T10:43:42Z
---

## Proposal: Correct the two parse_depends_on_entry scenarios that still say the error is raised

### Target specification files

- SPECIFICATION/scenarios.md

### Summary

Two `## Scenario` blocks for `parse_depends_on_entry` assert `Then CrossRepoSchemaError is raised`, which contradicts the same tree's ratified `contracts.md` (v016) statement that the function returns a `Failure` carrying that error and `does NOT raise`, and contradicts the shipped code. Replace the raise-shaped Then-lines with Result-shaped ones, and leave the adjacent `parse_cross_repo_manifest` scenario alone because that boundary genuinely does still raise.

### Motivation

Measured on livespec-runtime master at be744d4 on 2026-08-26. `livespec_runtime/cross_repo/types.py` declares `parse_depends_on_entry(*, parsed: dict[str, Any]) -> Result[DependsOnEntry, CrossRepoSchemaError]` and returns `Failure(...)` for a missing kind, an unknown kind, and a missing per-kind required field; its docstring states that the per-kind `_parse_*` helpers still raise but that this boundary discharges them onto the failure track so no caller of the public surface has to catch. `contracts.md` agrees in two places after v016: the standalone paragraph stating the function returns a `Failure` and `It does NOT raise - a caller guarding it with try/except would never see the handler fire`, and the module-surface bullet contrasting it with `parse_cross_repo_manifest`, which `still RAISES`. Only `scenarios.md` disagrees, in exactly two blocks: `parse_depends_on_entry rejects unknown kind` and `parse_depends_on_entry rejects missing required field`, both of which read `Then CrossRepoSchemaError is raised`. The third nearby raise-shaped scenario, `parse_cross_repo_manifest rejects target missing github_url`, is CORRECT and must not be touched. This is a spec-internal contradiction rather than spec-to-implementation drift: the specification asserts two incompatible things about one function, so a reader cannot tell which artifact governs, and the scenarios are the ones that are false. The v016 pass did not introduce it - that revision changed `contracts.md` and did not touch `scenarios.md` at all - it made a latent falsehood visible by restating the contract as shipped. No mechanical gate catches it. Both scenarios carry `tests/heading-coverage.json` entries pointing at real tests, and those tests PASS while asserting the Result behaviour correctly (`assert not is_successful(result)` and `result.failure().detail`), because the heading-coverage check verifies that a scenario HAS a linked test, never that the scenario's Then-clause matches what that test asserts. A contributor implementing from the scenarios would write a `try`/`except CrossRepoSchemaError` that can never fire and would then treat a `Failure`-carrying `Result` as a typed entry, which is precisely the failure mode the ratified contracts.md paragraph warns about.

### Proposed Changes

In `SPECIFICATION/scenarios.md`, the two `parse_depends_on_entry` scenarios MUST state the Result-track outcome the shipped boundary produces, and MUST NOT describe the error as raised.

In `## Scenario: parse_depends_on_entry rejects unknown kind`, REPLACE the line:

    Then CrossRepoSchemaError is raised

WITH:

    Then a Failure carrying CrossRepoSchemaError is returned

In `## Scenario: parse_depends_on_entry rejects missing required field`, REPLACE the identical line:

    Then CrossRepoSchemaError is raised

WITH:

    Then a Failure carrying CrossRepoSchemaError is returned

The following `And` lines in both scenarios already speak of `the error detail` and remain accurate for the error carried on the failure track; they MUST be left unchanged.

The scenario `## Scenario: parse_cross_repo_manifest rejects target missing github_url` MUST NOT be changed: `parse_cross_repo_manifest` still raises, and `contracts.md` deliberately records that the two boundaries differ and that callers MUST NOT assume one idiom covers both.

Only Then-lines inside two existing `## Scenario` blocks change. No `## ` heading is added, changed, or removed, so `tests/heading-coverage.json` requires no co-edit and both existing entries stay valid.

The stale prose SHOULD also be corrected in the docstring of `tests/consumer/test_cross_repo_resolution.py::test_parse_depends_on_entry_rejects_missing_required_field`, which says the entry `raises CrossRepoSchemaError` while the test body asserts the Result behaviour; that is an implementation-side follow-up outside this spec change and is recorded here so it is not lost.
