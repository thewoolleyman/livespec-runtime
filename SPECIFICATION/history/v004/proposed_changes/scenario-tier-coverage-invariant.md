---
topic: scenario-tier-coverage-invariant
author: claude-opus-4-8
created_at: 2026-05-31T21:04:15Z
---

## Proposal: scenario-tier-coverage-invariant

### Target specification files

- non-functional-requirements.md

### Summary

Add a new bullet under non-functional-requirements.md §"Test discipline" restating the scenario-tier coverage invariant for livespec-runtime's own SPECIFICATION: every `## Scenario:` heading in `SPECIFICATION/scenarios.md` MUST have its own entry in `tests/heading-coverage.json` (granular, one entry per scenario, many-to-one mapping to tests expected), and each mapped test MUST sit at the integration tier or above. The invariant is restated independently here (livespec-runtime's spec does NOT inherit it by reference from another repo's SPECIFICATION) and is enforced mechanically by `livespec_dev_tooling.checks.heading_coverage` (livespec-dev-tooling v0.9.0+).

### Motivation

Epic li-scetier Wave 3. The scenario-tier coverage invariant is a pre-approved design (the user has approved it; this proposal does not re-litigate it). Because livespec-runtime's SPECIFICATION/ is an independent spec tree that does NOT inherit normative rules by reference from another repo's SPECIFICATION, the invariant MUST be restated in runtime's own non-functional-requirements.md so the rule is locally binding. It is added as a new bullet under the existing §"Test discipline" H2 (not a new `## ` H2) to avoid a `tests/heading-coverage.json` co-edit, and the prose is matched to runtime's project-name-prefixed version-reference convention (`livespec-dev-tooling v0.9.0+`).

### Proposed Changes

Under `non-functional-requirements.md` §"Test discipline", append a new bullet (a sibling of the existing four bullets, NOT a new `## ` H2) with the following content:

- **Scenario-tier coverage.** Every `## Scenario:` heading in `SPECIFICATION/scenarios.md` MUST have its own entry in `tests/heading-coverage.json`; scenarios are tracked granularly, one entry per scenario, and several scenarios MAY map to the same test (a many-to-one mapping is expected). Each mapped test MUST sit at the **integration tier or above** — a consumer-shaped test that imports `livespec_runtime` and drives a real workflow (cross-repo dependency resolution, manifest parsing, an error path) against `tmp_path`-scoped checkouts, asserting on consumer-visible return values and error types — never a unit-tier test, since a scenario describes consumer-observable behavior. A scenario entry is compliant when EITHER (a) its test node-id path component begins with one of the integration-tier prefixes declared in this repo's `pyproject.toml` `[tool.livespec_dev_tooling].scenario_tiers` allowlist (e.g. `tests.consumer`, `tests.e2e`), OR (b) the resolved test carries an explicit `pytest.mark.integration` (or stronger) marker. A `TODO` entry is permitted during transition provided its `reason` explicitly acknowledges this tier requirement. This invariant is enforced mechanically by `livespec_dev_tooling.checks.heading_coverage` (livespec-dev-tooling v0.9.0+).
