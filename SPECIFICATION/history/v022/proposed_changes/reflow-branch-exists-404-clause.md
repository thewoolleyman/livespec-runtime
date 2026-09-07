---
topic: reflow-branch-exists-404-clause
author: claude-opus-5
created_at: 2026-09-07T11:57:21Z
---

## Proposal: reflow-branch-exists-404-clause

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Re-wrap the continuation lines of the `branch_exists_on_remote` bullet in §"Module-level public surface" → `livespec_runtime.cross_repo.providers.github` (currently lines 100–107) to the paragraph's own column width. One line, pasted during the v020 ratification, is 123 characters wide in a ~74-column paragraph. Cosmetic; the wording is unchanged.

### Motivation

Both independent ratification reviewers on 2026-09-06 noted the over-long pasted line as a non-blocker, and plan runtime-backlog-drain parked it rather than widen its frozen scope; plan runtime-backlog-drain-2 filed it as livespec-runtime-3r5 and this proposal is its payload. Reflowing keeps the file readable in the 80-column terminals and diff views the rest of the section is written for, and a byte-identical-modulo-whitespace edit carries no ratification risk.

### Proposed Changes

In `SPECIFICATION/contracts.md`, within the `branch_exists_on_remote` bullet of the `livespec_runtime.cross_repo.providers.github` section, the continuation lines that currently read (lines 100–107) from "`gh api repos/<owner>/<name>/branches/<branch>` and treats a 404" through "lands on the failure track as `GithubFailure`; it is NOT raised." MUST be re-wrapped so that no line exceeds 80 columns, keeping the bullet's two-space continuation indent. The text MUST be byte-identical to the current text after collapsing every run of line-break-plus-indent whitespace to a single space; no word, backtick span, or BCP14 keyword (the clause's existing SHOULD, MUST NOT and MAY) is added, removed, or reordered. The revise pass applies this as a whitespace-only edit and MUST verify it with `awk 'length > 80' SPECIFICATION/contracts.md` reporting nothing inside that bullet.
