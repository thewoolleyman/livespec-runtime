---
topic: emu-validation-seam-and-pre-major-provision
author: claude-opus-5
created_at: 2026-08-25T15:02:46Z
---

## Proposal: Fix the composition-validation seam at construction, refusing the call on an invalid id

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

v013 ratified that `compose_needs_attention` MUST NOT silently omit a candidate and that constructing an `AttentionItem` with an invalid id MUST NOT be a supported path, while explicitly deferring two choices to the proposal that implements them: which surfaced-failure form, and whether validation is enforced at construction or at every producer emission boundary. This fixes both: validation is enforced AT CONSTRUCTION, via a new `InvalidAttentionItemIdError` raised from `AttentionItem`, which makes the composer refuse the call — one of the three forms v013 permits.

### Motivation

The emission-boundary alternative is not enforceable by this library. Producers live in the consumer repositories — the orchestrator, the overseer, and console-facing components — so a rule requiring validation at every producer emission boundary would be a rule this library states and cannot check, which is how the silent-drop gap survived unnoticed in the first place. Construction is the single seam this library actually controls, and enforcing there closes BOTH ratified gaps at once: an invalid id can no longer be constructed directly, and the composer, which constructs every item it returns, therefore refuses the call rather than returning a shorter list. That is strictly stronger than a malformed marker, which would satisfy the composer bullet while leaving direct construction unvalidated. Raising also preserves the return type `list[AttentionItem]`, so no consumer's success path changes shape; only the previously-silent failure path becomes visible. The error subclasses `ValueError` so a consumer already guarding construction with a `ValueError` handler keeps working.

### Proposed Changes

`SPECIFICATION/contracts.md` §"`livespec_runtime.attention_item`" MUST gain the error to its enumerated surface:

> - `InvalidAttentionItemIdError` — raised when an `AttentionItem` is constructed with an `id` that fails `validate_attention_item_id`. It MUST subclass `ValueError`. Its message MUST name the rejected id.

The `AttentionItem` entry MUST state the construction contract:

> Constructing an `AttentionItem` whose `id` fails `validate_attention_item_id` MUST raise `InvalidAttentionItemIdError`. Validation happens at construction, so no `AttentionItem` value can exist with an invalid id.

`SPECIFICATION/contracts.md` §"`livespec_runtime.needs_attention`" MUST state the composer's resulting behavior:

> Because every returned item is constructed, `compose_needs_attention` MUST propagate `InvalidAttentionItemIdError` when any injected input composes an invalid id. It MUST NOT omit the offending candidate, and MUST NOT return a partial list alongside a suppressed failure. Refusing the call is the ratified surfaced-failure form for this library.

`SPECIFICATION/constraints.md` §"Public-surface constraints" MUST have its v013 non-conformance bullet for composition completeness REPLACED, because the implementation conforms once this lands:

> The composition-completeness constraints above are enforced at construction: `AttentionItem` validates its own `id` and raises `InvalidAttentionItemIdError`, so neither the composer nor a direct constructor can produce or suppress an invalid item. Enforcement MUST NOT be relocated to the producer emission boundary, because producers live in consumer repositories and this library cannot verify a rule it does not own.

This change tightens a parse contract such that previously valid inputs now raise, so it is a breaking change under `non-functional-requirements.md` §"Versioning" and MUST be released per the pre-major provision proposed alongside it.

## Proposal: Add a pre-major provision so a breaking change below 1.0.0 does not force 1.0.0

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

§"Versioning" classifies a breaking change as Major (`X.0.0`) with no provision for a library still below 1.0.0, so the first breaking change would mechanically force `1.0.0`. This adds an explicit pre-major provision: while the major version is 0, a Major-classified change is released as a minor bump, and the `1.0.0` boundary is reserved for a deliberate stability declaration. §"Release flow" gains the matching automation requirement so the released number cannot disagree with the rule.

### Motivation

The `-emu` seam change is the first Major-classified change this library has had to release, and it exposed that the ratified rule has no pre-major case. Read literally it mandates `1.0.0`, which would announce API stability as an incidental side effect of one bug fix, on a library four repositories vendor while the fleet's ordered release matrix is still deferred. Reaching `1.0.0` should be a deliberate declaration that the surface is stable and supported, not something the first breaking fix triggers. Semantic versioning already treats `0.y.z` as the initial-development phase where anything MAY change; the ratified text simply never said so. Without this provision the maintainer's direction to stay below 1.0.0 could only be honored by violating the ratified rule, which is not an acceptable way to resolve the conflict. The automation clause matters as much as the prose: this repository's release-please configuration carries no pre-major setting today, so a breaking subject would cut `1.0.0` regardless of what the spec says, and a rule the automation contradicts is not a rule.

### Proposed Changes

`SPECIFICATION/non-functional-requirements.md` §"Versioning" MUST gain, immediately after the Major/Minor/Patch classification list:

> **Pre-major provision.** While this library's major version is `0`, a change classified Major above MUST be released as a MINOR bump (`0.X.0`), NOT as `1.0.0`. The `1.0.0` boundary is reserved for a deliberate declaration that the public surface is stable and supported; it MUST NOT be reached incidentally by the first breaking change. Consumers MUST therefore treat every `0.X.0` bump as potentially breaking, which the pin-and-bump mechanism below already requires by making the `pinned` tag the authoritative version. The Major/Minor/Patch classification above continues to describe the CHANGE; this provision governs the NUMBER it is released under while the major version is `0`.

`SPECIFICATION/non-functional-requirements.md` §"Release flow" MUST gain:

> The release automation MUST be configured so it cannot contradict the pre-major provision: while the major version is `0`, `release-please-config.json` MUST carry `bump-minor-pre-major`, so a breaking-change subject cuts a minor bump rather than `1.0.0`. A release number the automation produces in disagreement with §"Versioning" is a defect in the configuration, not a re-interpretation of the rule.
