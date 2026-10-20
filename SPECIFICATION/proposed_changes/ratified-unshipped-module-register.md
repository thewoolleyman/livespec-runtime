---
topic: ratified-unshipped-module-register
author: claude-fable-5-1:spec-implementation-lockstep
created_at: 2026-10-20T02:31:59Z
---

## Proposal: A ratified public-surface section may precede its module while a live owner is registered

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/scenarios.md

### Summary

The public-surface inventory rule is one-directional in spec.md (every shipped module is ratified or declared internal), while tests/livespec_runtime/test_public_surface_inventory.py also refuses a ratified contracts.md section whose module does not ship, a reverse leg added by livespec-runtime-6tt to catch phantom names. Together they make it impossible to ratify a new family before its implementation lands, while the implementing work-item cannot be dispatched until its governing section is ratified. This change lets a ratified section precede its module only while a live owning work-item is named for it in a shrink-only ratified_unshipped_modules register in tests/public-surface-debt.json. Phantom detection is unchanged for every other section, and a stale row fails the suite.

### Motivation

Plan spec-implementation-lockstep in livespec-orchestrator-beads-fabro (epic bd-ib-ax3rds). The maintainer's 2026-10-20 ruling, recorded on bd-ib-7sjdzv, holds a feature until its linked proposed change is ratified, so the spec must be able to lead the implementation. Measured 2026-10-20: the revise of this repository's proposal spec-stated-judgement into v026 (opus ratification review NO BLOCKERS) was refused by the pre-push suite. test_every_ratified_module_section_resolves_to_a_shipped_module and test_every_documented_name_is_exported_by_a_module_its_section_names both failed on livespec_runtime.spec_stated, which its implementing work-item livespec-runtime-krpzzb cannot build before that ratification. The fleet coordinator ruled this route for the maintainer on 2026-10-20 (recorded on bd-ib-ax3rds).

### Proposed Changes

In SPECIFICATION/spec.md, section "Public surface", in the paragraph that begins "Every shipped module that declares a public surface is inside the ratified inventory", insert after the sentence ending "and `tests/livespec_runtime/test_public_surface_inventory.py` fails on it; the `# @generated` third-party port that test's register excludes is outside this rule by construction." the following sentences:

> The converse also holds: every module a ratified `contracts.md` section documents MUST ship, and every name such a section documents MUST be exported, so a phantom inventory entry fails the same test. The one exception is a section ratified AHEAD of its implementation. Such a section MAY name a module that does not ship yet only while a row of the `ratified_unshipped_modules` register in `tests/public-surface-debt.json` names that module and a live owning work-item. While the row stands, the test MUST NOT fail that section's module or names for not shipping, and MUST still apply every other check to it. The register is shrink-only: the change that ships the module MUST delete its row, a row whose module now ships MUST fail the suite as stale, and the owning work-item MUST NOT close while its row stands.

In SPECIFICATION/scenarios.md, add at the end of the file, in this repository's `## Scenario: <text>` heading style (tests/heading-coverage.json MUST gain an entry for it in the same revise):

## Scenario: a ratified section may precede its module only while a live owner is registered

- **Given** a ratified `contracts.md` section documenting a module that does not ship, and a `ratified_unshipped_modules` row naming that module and a live owning work-item
- **When** the public-surface inventory test runs
- **Then** it MUST NOT fail that section for the missing module or its unexported names
- **And** the same section without the row MUST fail as a phantom
- **And** a row whose module now ships MUST fail as stale
- **And** a documented name missing from any other ratified section's module MUST still fail
