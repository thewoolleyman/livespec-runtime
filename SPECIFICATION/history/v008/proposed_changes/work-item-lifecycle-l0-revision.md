---
proposal: work-item-lifecycle-l0.md
decision: accept
revised_at: 2026-06-29T08:08:07Z
author_human: thewoolleyman <chad@thewoolleyman.com>
author_llm: wism-l0-runtime
---

## Decision and Rationale

Ratify the L0 work-item-lifecycle contract (decisions 24/26/28/32/35/36/38/39/40/42/44): 7-state status enum; required non-null rank as the sole ordering authority; drop priority; admission/acceptance/blocked policy fields (optional-on-read); assignee reused as owner with active==>assignee; new work_items.lifecycle (lane_of/Lane + relocated is_item_ready/ready_sort_key with injected status-lookups, no runtime->beads back-edge) and work_items.rank (key_between/n_keys_between, ported CC0 module, BOTTOM_SENTINEL) surfaces; fix the :131 upstream-schema drift. The 6 load-bearing lane_of/rank Gherkin scenarios are deferred to a groomed implement child paired with their unit tests (maintainer call); no heading-coverage.json change (no ## heading added/changed; ### headings are not tracked).

## Resulting Changes

- contracts.md
