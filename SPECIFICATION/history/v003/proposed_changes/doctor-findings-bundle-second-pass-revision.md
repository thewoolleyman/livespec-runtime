---
proposal: doctor-findings-bundle-second-pass.md
decision: accept
revised_at: 2026-05-25T21:50:43Z
author_human: thewoolleyman <thewoolleyman@gmail.com>
author_llm: claude-opus-4-7
---

## Decision and Rationale

User accepted all 10 ## Proposal: sections of the doctor-findings-bundle-second-pass in the prior /livespec:doctor dialogue. Combined effect: (P1) renames 'Exhaustive live walk' to 'Per-variant live walk' in spec.md + constraints.md and rewrites the definition to match the per-variant single-source dispatch in contracts.md §'Resolution semantics'; (P2) trims spec.md §'Public surface' to a pointer at contracts.md §'Module-level public surface' to eliminate the symbol-inventory duplication; (P3) collapses constraints.md's 'Inherited from livespec' bullet list to a one-paragraph pointer at non-functional-requirements.md as the canonical inherited inventory; (P4) names local_status_lookup as REQUIRED and sibling_status_lookup as OPTIONAL in spec.md's trimmed §'Public surface' prose; (P5) adds a Gherkin scenario for parse_cross_repo_manifest rejecting a target missing github_url; (P6) relocates contracts.md §'Versioning' into non-functional-requirements.md §'Versioning' (between Build-and-packaging and Release-flow) and replaces the contracts.md anchor with a pointer; (P7) drops the dangling 'templates/library/ is extracted' parenthetical in non-functional-requirements.md since no concrete upstream work-item is linked; (P8) documents the gh-api branch-existence 404-detection mechanism on contracts.md §branch_exists_on_remote with the harden-via-exit-code directive (impl change filed separately as work-item harden-branch-exists-404-detection); (P9) merges spec.md §'What this spec is not' into §'Scope boundary' as an 'Out of scope:' paragraph; (P10) names CrossRepoManifest's .targets dict attribute as a REQUIRED field in contracts.md §'livespec_runtime.cross_repo.types' so renaming is unambiguously a major-version bump.

## Resulting Changes

- spec.md
- contracts.md
- constraints.md
- scenarios.md
- non-functional-requirements.md
