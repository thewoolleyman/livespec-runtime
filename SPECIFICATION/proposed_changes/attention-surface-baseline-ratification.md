---
topic: attention-surface-baseline-ratification
author: claude-opus-5
created_at: 2026-08-25T11:38:24Z
---

## Proposal: Admit shared-runtime contracts that livespec core deliberately declines to name

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/contracts.md

### Summary

`contracts.md`'s preamble states that every contract it carries concretizes a slot in `livespec/SPECIFICATION/contracts.md`, and `spec.md` §"Scope boundary" frames this library as realizing only the runtime portion of livespec's cross-repo contract. Neither admits a contract that core has no slot for. The shipped attention surface is exactly such a contract: core's `contracts.md` names attention nowhere, and core's only attention prose is explicitly non-normative. This proposal widens both statements to admit a second, bounded category — shared-runtime surfaces consumed by two or more livespec-family producers that core has deliberately declined to name — so the attention baseline can be ratified without overriding upstream or silently violating this library's own preamble.

### Motivation

Homelab's plan `steady-state-loop-hardening` ruling R4 (`research/010-runtime-review-triage.md`) charges this repository with ratifying its shipped attention surface baseline-first. Executing that charge against the spec as written is currently impossible, and no prior review caught why: `contracts.md`'s preamble says "Every contract here concretizes a slot in `livespec/SPECIFICATION/contracts.md`; nothing here overrides upstream", but `grep -ic attention` over core's ratified tree returns 0 in `contracts.md`, and core's `non-functional-requirements.md` §"Control-Plane console guidance" states of its attention prose that core "neither names nor verifies any of it" and that the concrete realization "belongs to the reference console's own specification". There is therefore no upstream slot to concretize and, by core's own cut, there is not supposed to be one. Ratifying the attention surface into `contracts.md` without this widening would make the preamble false the moment the baseline lands — replacing one unratified surface with one self-contradicting document. The widening is deliberately bounded so it cannot become a licence for arbitrary local contracts: it admits only surfaces that at least two livespec-family Python producers already consume and that core has positively declined to name.

### Proposed Changes

In `SPECIFICATION/spec.md` §"Scope boundary", after the paragraph beginning "This spec describes ONLY the library's own contracts and discipline", the spec MUST add a paragraph establishing the second category:

> This library additionally carries SHARED-RUNTIME contracts: surfaces consumed by two or more livespec-family Python producers that `livespec` core has deliberately declined to name. Core's `non-functional-requirements.md` assigns such realizations to the realizing repositories rather than to core's contract; this library is the realizing repository for the shared piece. A shared-runtime contract MUST NOT restate or override any upstream contract, and MUST NOT be introduced where an upstream slot exists — where core names a slot, the concretize-a-slot rule continues to govern. A surface qualifies as shared-runtime ONLY when the same pure semantics and data shape are required by at least two producers and are expressible with consumer-neutral inputs; a surface needed by exactly one producer MUST stay in that producer.

In `SPECIFICATION/contracts.md`, the preamble sentence "Every contract here concretizes a slot in `livespec/SPECIFICATION/contracts.md`; nothing here overrides upstream" MUST be replaced by:

> Every contract here either concretizes a slot in `livespec/SPECIFICATION/contracts.md` or is a shared-runtime contract per `spec.md` §"Scope boundary". Nothing here overrides upstream. Each shared-runtime section MUST state, in its own text, that core names no slot for it and MUST name the producers that consume it.

The spec MUST NOT treat this category as open-ended: a proposal introducing a new shared-runtime contract SHOULD be rejected at revise unless it names the two or more consuming producers.

## Proposal: Ratify the shipped attention surface as public API

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/constraints.md

### Summary

Adds `### livespec_runtime.attention_item` and `### livespec_runtime.needs_attention` to `contracts.md` §"Module-level public surface", enumerating the symbols, the closed `AttentionKind` / `AttentionUrgency` / `HandoffKind` vocabularies, the dataclass fields, the stable-ID grammar, and the composer's injected input types and normalization semantics. This declares as ratified API what has in fact been shipped since v0.9.0 and consumed across repositories ever since.

### Motivation

The attention surface — `AttentionItem`, `SourceRef`, `Handoff`, `AttentionKind`, `AttentionUrgency`, `HandoffKind`, `validate_attention_item_id`, and `compose_needs_attention` — is shipped, imported across the livespec family, and absent from this repository's ratified specification: `grep -ic attention` over all six files of `SPECIFICATION/` returns 0, while `constraints.md` §"Public-surface constraints" declares the `contracts.md` inventory to be "the entire v1 stable API". Every consumer therefore depends on a surface that this repository's own contract says is implementation detail, free to change in a patch release. The closure of `AttentionKind` — which downstream fan-out planning treats as a compatibility boundary — is today only a `typing.Literal` plus one exact-set unit test, which is a code convention, not a spec invariant. Homelab ruling R4 identified this as the reason the shared-runtime routing rule has no substrate: there is nothing ratified to amend. This finding supplies the substrate; extensions are deliberately out of scope and land only against the ratified baseline.

### Proposed Changes

`SPECIFICATION/contracts.md` §"Module-level public surface" MUST gain two subsections, each declaring itself a shared-runtime contract per `spec.md` §"Scope boundary" and naming its consuming producers.

`### livespec_runtime.attention_item` MUST enumerate:

- `AttentionKind` — a closed `Literal` whose members are exactly `human-valve`, `impl`, `spec`, `plan`, `hygiene`, `internal`, `host-only`. The set MUST be closed; adding a member is a minor-version bump per `non-functional-requirements.md` §"Versioning" for wire consumers, and MUST be treated as coordinated for consumers that exhaustively match on the type.
- `AttentionUrgency` — a closed `Literal` of exactly `high`, `medium`, `low`.
- `HandoffKind` — a closed `Literal` of exactly `drive`, `livespec-op`, `plan`, `shell`.
- `SourceRef` — frozen, slotted, kw-only; fields `repo: str`, `work_item: str | None = None`, `path: str | None = None`.
- `Handoff` — frozen, slotted, kw-only; fields `kind: HandoffKind`, `command: str`, `action_id: str | None = None`. A `Handoff` MUST carry an executable action, never a bare pointer.
- `AttentionItem` — frozen, slotted, kw-only; fields `id: str`, `kind: AttentionKind`, `urgency: AttentionUrgency`, `summary: str`, `source_ref: SourceRef`, `handoff: Handoff`.
- `validate_attention_item_id(*, id: str) -> bool` — the stable-ID grammar. An id MUST be colon-separated. Two-part ids `\u003cprefix\u003e:\u003csubject\u003e` MUST be accepted for prefixes `impl` and `plan`. Three-part ids `\u003cprefix\u003e:\u003cclass\u003e:\u003csubject\u003e` MUST be accepted for prefixes `host-only`, `valve`, `hygiene`, and `spec`. Every component after the prefix MUST be non-empty and MUST NOT be purely decimal, so that ids are stable natural keys rather than positional indices.

`### livespec_runtime.needs_attention` MUST enumerate the injected input dataclasses `SpecNextOutput`, `ImplNextOutput`, `WorkItemHumanValveLane`, `PlanThreadOutput`, and `HygieneScanFinding` with their fields and urgency defaults, and `compose_needs_attention(*, repo, spec_next=None, impl_next=None, human_valve_lanes=(), plan_threads=(), hygiene_scan=()) -> list[AttentionItem]`. The section MUST state that the composer is PURE: it MUST NOT read a ledger, journal, filesystem, or configuration, MUST NOT resolve an executable command, and MUST receive every fact as an already-derived injected input. It MUST state the id each input class composes (`valve:\u003cverb\u003e:\u003cwork_item\u003e`, `impl:\u003cwork_item\u003e`, `spec:\u003cop\u003e:\u003cspec_target\u003e`, `plan:\u003ctopic\u003e`, `hygiene:\u003ctype\u003e:\u003cresource\u003e`) and that ordering is deterministic. It MUST record that kinds `internal` and `host-only` are producer-constructed and have no composer input class.

`SPECIFICATION/constraints.md` §"Public-surface constraints" MUST be amended so that its "entire v1 stable API" sentence explicitly covers the shared-runtime sections as well as the slot-concretizing ones.

## Proposal: Correct the stale cross_repo-only public-surface sentence

### Target specification files

- SPECIFICATION/spec.md

### Summary

`spec.md` §"Public surface" tells consumers they import from sub-modules under `livespec_runtime.cross_repo`, naming only that package, although the ratified inventory has covered `work_items` and `github_auth` for many releases and will cover the attention modules once this proposal lands. The sentence MUST be generalized to point at the inventory rather than at one package.

### Motivation

The sentence is simply false as shipped and has been false since `work_items` and `github_auth` were ratified; the attention baseline widens the gap further. A reader following §"Public surface" literally would conclude that `livespec_runtime.work_items.lifecycle` — which the pending `contracts-sibling-block-rule` proposal is actively correcting — is implementation detail. Leaving it unfixed while adding two more families to the inventory would make the entry point to the public surface actively misleading.

### Proposed Changes

In `SPECIFICATION/spec.md` §"Public surface", the opening sentence "Consumers import directly from the sub-modules under `livespec_runtime.cross_repo`, not from the package namespace" MUST be replaced with:

> Consumers import directly from the sub-modules enumerated in `contracts.md` §"Module-level public surface", not from the package namespace. That inventory spans every ratified family — slot-concretizing families such as `livespec_runtime.cross_repo`, `livespec_runtime.work_items`, and `livespec_runtime.github_auth`, and shared-runtime families per §"Scope boundary".

The remainder of the section, including the `resolve_ref` lookup paragraph, MUST be left intact; it is accurate and specific to the cross-repo family. The section MUST NOT enumerate symbols inline — `contracts.md` remains the single source of truth.

## Proposal: Ratify kind-to-prefix lockstep and declare the two shipped breaks non-conformant

### Target specification files

- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

Establishes as a ratified invariant that every `AttentionKind` member has exactly one corresponding stable-ID prefix and vice versa, and records that the shipped implementation violates it in two places: kind `internal` has no prefix at all, and kind `human-valve` composes the non-matching prefix `valve`. The invariant is ratified now and the implementation is declared non-conformant, which converts a silent inconsistency into a tracked spec-to-implementation gap.

### Motivation

The seven ratified kinds are `human-valve`, `impl`, `spec`, `plan`, `hygiene`, `internal`, `host-only`; the six grammar prefixes are `impl` and `plan` (two-part) and `host-only`, `valve`, `hygiene`, `spec` (three-part). Two mismatches follow. `internal` is a first-class kind that `validate_attention_item_id` rejects outright — the open bug `livespec-runtime/livespec-runtime-dnu`. Separately, and recorded nowhere before this thread, kind `human-valve` maps to prefix `valve`: `compose_needs_attention` emits `valve:\u003cverb\u003e:\u003cwork_item\u003e` for `kind="human-valve"`, so the composer itself bakes in the mismatch and no test catches it. A baseline that declared only the shipped behavior would ratify both breaks as correct, which is precisely the failure this baseline exists to prevent. Ratifying the invariant instead, and naming the implementation non-conformant, is what the livespec loop is for: the gap becomes visible to gap detection and is closed in the implementation rather than blessed in the contract.

### Proposed Changes

`SPECIFICATION/constraints.md` MUST gain, under §"Public-surface constraints", the lockstep invariant:

> Every `AttentionKind` member MUST correspond to exactly one stable-ID prefix accepted by `validate_attention_item_id`, and every accepted prefix MUST correspond to exactly one `AttentionKind` member. The correspondence MUST be by equal literal text. Adding a kind without its prefix, adding a prefix without its kind, or naming a prefix differently from its kind is FORBIDDEN. A mechanical check MUST assert the bijection so the two vocabularies cannot drift.

The same section MUST record the known non-conformance explicitly:

> As of the revision that ratifies this constraint, the implementation is NON-CONFORMANT in two places: `internal` is a ratified kind with no accepted prefix, and the ratified kind `human-valve` is composed with the prefix `valve`. Both are spec-to-implementation gaps to be closed in the implementation; neither is a licence to weaken this constraint. Closing them MUST preserve every id already emitted, so the correction either admits `internal` and `human-valve` as accepted prefixes or migrates emitted ids under an explicit compatibility decision recorded at revise.

`SPECIFICATION/scenarios.md` MUST gain scenarios covering the invariant and the shipped behavior:

> `## Scenario: every attention kind has a matching stable-ID prefix` — Given the ratified `AttentionKind` members, When the accepted prefix set of `validate_attention_item_id` is compared against them, Then the two sets MUST be equal by literal text.

> `## Scenario: validate_attention_item_id rejects an id whose component is purely decimal` — Given the id `impl:42`, When it is validated, Then the result MUST be false, because a positional index is not a stable natural key.

> `## Scenario: validate_attention_item_id accepts a well-formed three-part hygiene id` — Given the id `hygiene:stale-worktree:my-repo`, When it is validated, Then the result MUST be true.

Each new scenario MUST be linked from `tests/heading-coverage.json` in the same revise landing, per `non-functional-requirements.md` §"Test discipline" ("Scenario-tier coverage"), whose mapped test MUST sit at the integration tier or above; a scenario added without its coverage entry is malformed.

## Proposal: Ratify composition completeness so absence can never be manufactured by validation failure

### Target specification files

- SPECIFICATION/constraints.md
- SPECIFICATION/scenarios.md

### Summary

Establishes that `compose_needs_attention` MUST NOT silently omit a candidate whose id fails validation, and that constructing an `AttentionItem` with an invalid id MUST NOT be a supported path. The shipped composer does silently drop such candidates and direct construction bypasses validation entirely; both are declared non-conformant rather than ratified.

### Motivation

`compose_needs_attention` routes every candidate through a private `_append_if_valid` helper that appends only when `validate_attention_item_id` returns true and otherwise discards the item with no error, no marker, and no log — behavior currently pinned by unit tests. Because the kind-to-prefix lockstep is already broken, this is not hypothetical: a candidate carrying a would-be `internal:` id is dropped on the floor today. The consequence is a producer-side false-green channel. A caller that renders the composed list sees a SHORTER list, indistinguishable from a genuinely quiet repository, so a validation defect presents as "nothing needs attention". That is the same failure class that homelab's research/009 R3 repaired one layer up on the detector side, and it is strictly worse here because it is silent at the point of production. Ratifying the current behavior would ratify the ability to manufacture absence.

### Proposed Changes

`SPECIFICATION/constraints.md` MUST gain, under §"Public-surface constraints":

> `compose_needs_attention` MUST NOT silently omit a candidate. When a candidate's id fails `validate_attention_item_id`, the composer MUST surface the failure — by refusing the call, by returning a typed failure, or by emitting an explicit malformed marker in the returned sequence. Returning a shorter list with no other signal is FORBIDDEN, because an omission is indistinguishable from an absence of attention and therefore manufactures a false all-clear. Absence MUST always mean nothing needed attention, never that composition failed.

> Constructing an `AttentionItem` whose id fails `validate_attention_item_id` MUST NOT be a supported path. Validation MUST be enforced at construction or at every producer emission boundary; which of the two, and the exact surfaced-failure form above, MUST be fixed by the proposal that implements this constraint.

The section MUST record that the implementation is NON-CONFORMANT as of the ratifying revision: the shipped composer drops invalid candidates silently and direct construction is unvalidated. Both are spec-to-implementation gaps.

`SPECIFICATION/scenarios.md` MUST gain the negative control:

> `## Scenario: composition surfaces an invalid candidate rather than shortening the list` — Given one candidate whose id is well-formed and one whose id is not, When `compose_needs_attention` is called with both, Then the result MUST surface the invalid candidate as an explicit failure or malformed marker, and MUST NOT be a one-element list carrying only the valid candidate.

That scenario MUST be linked from `tests/heading-coverage.json` in the same revise landing, per `non-functional-requirements.md` §"Test discipline" ("Scenario-tier coverage"), and its mapped test MUST sit at the integration tier or above.

## Proposal: Record the remaining shipped-but-unratified modules as explicit debt

### Target specification files

- SPECIFICATION/spec.md

### Summary

States which shipped modules remain outside the ratified inventory after this baseline — `hygiene_scan` and its five companions, `credentials`, the `github_budget` family, and `spec_governance` — and records that their absence is acknowledged debt rather than a claim that they are implementation detail.

### Motivation

Homelab's charge asks explicitly whether `hygiene_scan` rides the baseline or is recorded as debt. Verifying the question against the package shows it is broader than `hygiene_scan`: `credentials`, `github_budget` and its four companion modules, and `spec_governance` are equally shipped and equally unratified. Answering only for `hygiene_scan` would leave the identical defect standing under four other names. They are deliberately NOT ratified here: the attention surface is on the critical path because other repositories consume it across the boundary and a parallel filing waits on it, whereas ratifying five more families in the same pass would enlarge an already load-bearing proposal and invite exactly the unexamined blessing this baseline exists to avoid. What is not acceptable is silence, because silence is what let the attention surface ship unratified for eleven minor versions.

### Proposed Changes

`SPECIFICATION/spec.md` §"Public surface" MUST gain a closing paragraph:

> Some shipped modules remain outside the ratified inventory: `livespec_runtime.hygiene_scan` and its companion modules, `livespec_runtime.credentials`, the `livespec_runtime.github_budget` family, and `livespec_runtime.spec_governance`. Their absence is ACKNOWLEDGED DEBT, not a claim that they are implementation detail. Until each is ratified, consumers MUST NOT treat it as stable API, and this repository MUST NOT rely on the absence as licence to change it freely where a consumer is known to import it. Each MUST be ratified or explicitly declared internal in a subsequent proposal.

The paragraph MUST NOT ratify these modules by implication, and a later proposal ratifying any of them MUST enumerate its symbols in `contracts.md` under the same discipline this baseline applies to the attention family.

## Proposal: Define producer and scope the Literal-discriminator rule so the attention vocabularies do not contradict it

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/constraints.md

### Summary

Adds a `Producer` definition to `spec.md` §"Terminology", because the shared-runtime category and the attention sections both lean on it, and narrows the existing `constraints.md` bullet governing `Literal[...]` discriminator values so that it names the `DependsOnEntry` union explicitly rather than "the union variants". Without the narrowing, ratifying the kebab-case attention vocabularies would contradict a ratified constraint the moment the baseline lands.

### Motivation

Two defects surfaced by running this proposal through the doctor objective checks before filing, both caused by this baseline introducing a second family into a document written when only one existed. First, `constraints.md` §"Public-surface constraints" states that `Literal[...]`-typed discriminator fields "on the union variants" MUST take literal values equal to "the snake_case variant name", exemplified by `local`, `sibling_work_item`, `pull_request`, and `branch`. `AttentionItem.kind` is a `Literal`-typed discriminator field, and its ratified members `human-valve` and `host-only` are kebab-case, not snake_case. The bullet's definite reference to "the union variants" is unambiguous only while `DependsOnEntry` is the sole union; once the attention family is ratified the sentence reads as a rule the new surface breaks. Second, "producer" carries real weight in the shared-runtime admission test and in the attention sections, yet it appears nowhere in the ratified tree, and §"Terminology" exists precisely to hold library-local additions. An undefined load-bearing term in an admission test is how an admission test stops constraining anything.

### Proposed Changes

`SPECIFICATION/spec.md` §"Terminology" MUST gain a library-local definition:

> **Producer** — A livespec-family Python component that CONSTRUCTS values of a shared-runtime type and emits them across a process or repository boundary; for the attention family, an orchestrator, overseer, or console-facing component that composes or constructs `AttentionItem` values. A producer is distinguished from a mere importer: importing a type for annotation does not make a component a producer. The shared-runtime admission test in §"Scope boundary" counts producers, not importers.

`SPECIFICATION/constraints.md` §"Public-surface constraints" MUST narrow the existing `Literal[...]` bullet so it names its subject. Its opening MUST be changed from "`Literal[...]`-typed discriminator fields on the union variants" to "`Literal[...]`-typed discriminator fields on the `DependsOnEntry` union variants", leaving the snake_case requirement and its four examples otherwise intact.

The same section MUST then state the rule for the other family, so neither vocabulary is left ungoverned:

> Closed `Literal` VOCABULARIES that are not union discriminators — `AttentionKind`, `AttentionUrgency`, and `HandoffKind` — are governed separately. Their members MUST be lowercase and MAY contain internal hyphens; they are wire-visible strings rather than variant names, so the snake_case rule above MUST NOT be applied to them. Their exact membership is fixed by `contracts.md`, and widening any of them is a public-surface change per §"Public-surface constraints".

This finding MUST land in the same revision as the attention sections; ratifying those sections without it would introduce the contradiction it exists to prevent.
