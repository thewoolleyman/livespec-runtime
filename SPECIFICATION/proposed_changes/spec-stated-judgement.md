---
topic: spec-stated-judgement
author: claude-fable-5-1:spec-implementation-lockstep
created_at: 2026-10-20T01:08:54Z
---

## Proposal: livespec_runtime.spec_stated: the shared judgement of whether a behaviour is stated by the ratified spec, with an injected model runner

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/scenarios.md

### Summary

A new shared-runtime family, livespec_runtime.spec_stated, defines once for every orchestrator the judgement 'is this behaviour stated by the ratified specification, and by which heading', and the classification of a work-item as a feature, a bug, a chore or non-functional. The module owns the prompt text, the inputs, the verdict schema, its parser and the persisted spec-change-tier fields both orchestrators store; it invokes no model itself and takes the model runner as a caller-supplied callable, so the library stays model-agnostic and credential-free. It is added to the Module-level public surface as a minor-version addition.

### Motivation

Plan spec-implementation-lockstep in livespec-orchestrator-beads-fabro (epic bd-ib-ax3rds), Definition of Done assertion 6: both orchestrators, livespec-orchestrator-beads-fabro and livespec-orchestrator-git-jsonl, run the same is-this-stated-by-the-spec judgement from livespec-runtime. The maintainer's 2026-08-25 rule routes behaviour common to the orchestrators to this library ('a plugin-local implementation of a shared shape forks the schema; a core-side definition reverses the established source-of-truth direction. Both are refusals'), and the 2026-10-19 ruling asks for one implementation of the drift concept that everything else delegates to. The consuming work-item in this repository is livespec-runtime-krpzzb; the beads-fabro consumers are bd-ib-ouk27x (vendored pin), bd-ib-57ss2n, bd-ib-dzk5jd, bd-ib-yvjxo4 and bd-ib-m76p2n, and git-jsonl's consumer is bd-ib-jik5ko.

### Proposed Changes

In SPECIFICATION/contracts.md, section "Module-level public surface", add a new subsection immediately after "### `livespec_runtime.spec_governance`" and before "## Resolution semantics":

### `livespec_runtime.spec_stated`

SHARED-RUNTIME contract per `spec.md` §"Scope boundary": the one judgement every orchestrator runs to decide whether a behaviour is stated by a ratified livespec specification. The consuming producers are `livespec-orchestrator-beads-fabro` (its Definition-of-Done judgement, its Definition-of-Ready spec-change tier, its ledger-intent scan and its drift run) and `livespec-orchestrator-git-jsonl` (its ledger-intent scan, its impl-drift front-end and its filing). The module MUST define the judgement once — its prompt, its inputs, its verdict schema and its parser — and MUST NOT invoke a model, a subprocess or the network itself: the model is reached only through the `run_model` callable the caller supplies, so the library carries no credential and no provider binding.

- `StatedKind` — the `TypeAlias` for `Literal["stated", "partial", "unstated"]`.
- `ItemClass` — the `TypeAlias` for `Literal["feature", "bug", "chore", "non_functional"]`.
- `SpecStatedVerdict` — frozen, slotted, kw-only dataclass. Fields: `kind: StatedKind` (REQUIRED); `stated_by: tuple[str, ...]` (REQUIRED; each entry the verbatim text of a governing H2 heading, empty for `unstated`); `generalization_target: str | None` (REQUIRED; the verbatim H2 heading whose generalization would state the behaviour, or `None`); `rationale: str` (REQUIRED).
- `SpecChangeTier` — frozen, slotted, kw-only dataclass: the persisted fields both orchestrators store on a work-item. Fields: `tier: Literal["spec-change", "none"]` (REQUIRED), `linked_proposal_topic: str | None` (REQUIRED), `verdict: SpecStatedVerdict | None` (REQUIRED), `judged_at: str` (REQUIRED, ISO-8601 UTC).
- `ModelRunner` — the `TypeAlias` for `Callable[[str], str]`: given the rendered prompt, return the model's raw text. The library MUST call it at most once per `judge` or `classify` call.
- `SpecStatedParseError` — raised by nothing; returned as the `Failure` payload of `parse_verdict`. It MUST subclass `Exception` directly per `constraints.md` §"Public-surface constraints" and MUST carry `field: str | None` (the offending field, or `None` when the response is not JSON) and `detail: str`.
- `JUDGE_PROMPT: str` and `CLASSIFY_PROMPT: str` — the prompt templates, importable so a consumer renders exactly the shared text.
- `judge(*, spec_tree: Mapping[str, str], statement: str, run_model: ModelRunner) -> Result[SpecStatedVerdict, SpecStatedParseError]` — `spec_tree` maps each spec-tree-relative file path to its text. The verdict's `stated_by` entries MUST each equal an H2 heading present in `spec_tree`; a model response naming a heading not present MUST be returned as a `Failure` naming the field.
- `classify(*, title: str, description: str, item_type: str, run_model: ModelRunner) -> Result[ItemClass, SpecStatedParseError]` — `item_type` is the stored type and MUST be passed to the model as evidence, never returned as the answer unexamined.
- `parse_verdict(*, text: str, headings: Collection[str]) -> Result[SpecStatedVerdict, SpecStatedParseError]` — parse one raw model response. A well-formed response yields the verdict; a response with a missing or ill-typed field yields a `Failure` whose error names that field; a response that is not JSON yields a `Failure` whose error has `field` `None` and a `detail` naming the parse error.

In SPECIFICATION/scenarios.md, add at the end of the file, in this repository's `## Scenario: <text>` heading style (tests/heading-coverage.json MUST gain an entry for each in the same revise):

## Scenario: the spec-stated judgement names the governing heading, the generalization target, or neither

- **Given** a spec tree whose `contracts.md` carries the H2 heading `## Widgets` stating that a widget MUST be blue, and a `run_model` stub returning a well-formed response
- **When** `judge` is called with the statement "a widget is blue"
- **Then** the result MUST be a `Success` whose verdict has `kind` `stated` and `stated_by` equal to `("## Widgets",)`
- **And** calling `judge` with "a widget is blue and square" against a stub reporting partial coverage MUST yield `kind` `partial` with `generalization_target` `"## Widgets"`
- **And** the stub MUST have been called exactly once per `judge` call, and the module MUST have opened no subprocess and no socket

## Scenario: classify treats the stored type as evidence, not as the answer

- **Given** an item typed `task` whose description asks for new observable behaviour, and a `run_model` stub that returns `feature`
- **When** `classify` is called
- **Then** the result MUST be a `Success` carrying `feature`

## Scenario: parse_verdict names the offending field or the parse error

- **Given** a response missing `kind`
- **When** `parse_verdict` is called
- **Then** the result MUST be a `Failure` whose `SpecStatedParseError` has `field` `"kind"`
- **And** for a response that is not JSON the `Failure`'s error MUST have `field` `None` and a non-empty `detail`
- **And** for a response whose `stated_by` names a heading absent from the supplied headings the `Failure`'s error MUST have `field` `"stated_by"`
