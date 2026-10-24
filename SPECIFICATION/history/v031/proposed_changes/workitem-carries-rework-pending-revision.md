---
proposal: workitem-carries-rework-pending.md
decision: accept
revised_at: 2026-10-24T16:08:42Z
author_human: Chad Woolley <thewoolleyman@gmail.com>
author_llm: claude-opus-5-5
---

## Decision and Rationale

Accepted as written. It extends the existing awaits_scope_override sentence pattern in ### livespec_runtime.work_items.types to rework_pending, which livespec-orchestrator-beads-fabro has carried as a local vendored patch since its commit 74a97bf9 (2026-08-28). Ratifying it releases the governance hold on livespec-runtime-gfhy2a, which implements the field upstream and is the fleet coordinator's last missing carrier for its runtime dispatch assertion. Independent ratification review: opus, read-only, NO BLOCKERS on the exact bytes (it counted 15 required plus 11 optional-on-read fields, 26 in all, and searched the live spec for other field enumerations, finding none). Advisories carried to gfhy2a: confirm the rework:pending label spelling against the orchestrator, and keep work_item_record_identity stable for legacy records.

## Resulting Changes

- contracts.md
- scenarios.md

## Ratification Review

ratification_review: auto-spawn
reviewer_model: opus
reviewer_identity: opus
separate_reviewer: True
read_only: True
reviewed_at: 2026-10-24T16:07:20Z
verdict: NO BLOCKERS
proposal_stem: workitem-carries-rework-pending
content_digest: 132c569c3d25a8e9d72ed5760059e6d150a109a3e74df7e398bcd9324b4af101
