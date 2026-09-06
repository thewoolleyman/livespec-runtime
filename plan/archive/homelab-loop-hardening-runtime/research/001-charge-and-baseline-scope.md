# 001 — Charge, verified baseline, and the ownership cut

Seed note for plan thread `homelab-loop-hardening-runtime`, created
2026-08-25 by the runtime-side session.

## Where this charge came from

`mi-homelab/homelab` ran a four-repository adversarial review programme
against its plan `steady-state-loop-hardening` (epic `homelab/hl-nkuzaz`).
This repository supplied the fourth and final pair (PR #1033), and homelab
triaged it as `research/010-runtime-review-triage.md` (PR #1034), whose
ruling **R4** made this thread MANDATORY and **baseline-first**.

Read-first chain, in order:

1. `mi-homelab/homelab` `plan/steady-state-loop-hardening/research/010-runtime-review-triage.md`
   — the triage that charges this thread (§"The runtime charge").
2. The same plan's `research/reviews/livespec-runtime-review-fable.md` and
   `research/reviews/livespec-runtime-review-sol.md` — this repository's own
   reviews; their closing sections are the ratifiability lists the charge unions.
3. `research/008-core-review-triage-and-shared-runtime-rule.md` — the
   shared-runtime routing rule this thread executes.
4. `research/009-console-review-triage.md` §R2 — propagation by consumer
   shape, refined again by 010.

Homelab initiates; this repository files. Nothing in that chain authorizes
bypassing this repo's own valves: every spec change here runs
`propose-change` → independent review → `revise`, never a direct spec edit.

## What is verified true in this repository, today

Re-verified in this session against primary sources, not accepted from the
reviews:

- **The attention surface is ratified nowhere.** `grep -ic attention` over
  all six files of `SPECIFICATION/` returns **0** — `spec.md`,
  `contracts.md`, `constraints.md`, `non-functional-requirements.md`,
  `scenarios.md`, `README.md`. The shipped surface — `AttentionItem`,
  `SourceRef`, `Handoff`, `AttentionKind`, `AttentionUrgency`,
  `HandoffKind`, `validate_attention_item_id` in
  `livespec_runtime/attention_item.py`, and `compose_needs_attention` in
  `livespec_runtime/needs_attention.py` — has been cross-repo consumed
  since `v0.9.0` with no ratified contract behind it.
- **`spec.md` §"Public surface" is stale.** It says consumers "import
  directly from the sub-modules under `livespec_runtime.cross_repo`",
  naming only that package, and defers the inventory to `contracts.md`
  §"Module-level public surface" — which enumerates `cross_repo`,
  `work_items`, and `github_auth` and nothing else.
- **`AttentionKind` closure is a code convention.** It is a
  `typing.Literal` plus an exact-set unit test — not a spec invariant.
  There is therefore no ratified text to amend, which is precisely why the
  baseline must land before any extension.
- **Kind↔prefix lockstep is broken in TWO places, not one.** The kinds are
  `human-valve, impl, spec, plan, hygiene, internal, host-only` (7); the
  id-grammar prefixes are `impl, plan` (two-part) and
  `host-only, valve, hygiene, spec` (three-part) (6). So:
  - `internal` is a first-class kind with **no** prefix at all — the open
    bug `livespec-runtime/livespec-runtime-dnu`; and
  - kind `human-valve` corresponds to prefix `valve` — a **name mismatch**
    that no mechanical check currently catches and that `-dnu` does not
    mention.
  Any lockstep constraint this thread ratifies must cover both.
- **Shipped-but-unratified is broader than attention.** `hygiene_scan*`
  (six modules), `credentials`, `github_budget*`, and `spec_governance`
  are equally absent from the ratified inventory. The baseline
  propose-change must state explicitly, per charge point 1, whether they
  ride the baseline or are recorded as debt — silence would repeat the
  defect being repaired.

## The charge (ten points, in order)

From `research/010` §"The runtime charge", with the reviews' detail folded in.

1. **Baseline ratification propose-change FIRST.** Declare the current
   shipped attention surface: schema, kinds, stable-ID grammar, composer
   inputs/semantics, validation posture. Correct `spec.md` §"Public
   surface". Scenarios and heading coverage co-edited. State explicitly
   whether `hygiene_scan` and the other shipped-but-unratified modules ride
   the baseline or are recorded debt. **Only then** any extension.
2. **Row-by-row ownership table under the rt-sol-2 routing test.** Code
   moves here only when the SAME pure semantics and data shape are needed by
   **at least two Python producers** and are expressible with
   **consumer-neutral inputs**. This repository MAY own envelope types, the
   ID grammar, the validator, and a pure normalizer over injected facts. It
   MUST NEVER own the five fact derivations, persistence, thresholds, CLI
   envelopes, console events, overseer state, or the probe. Consumer
   vocabulary — beads/Dolt, dispatcher, journal, foreman, homelab — is
   banned from this repository's contracts. Duplicated thin adapters are
   acceptable; **DRY never justifies reversing dependency direction**.
3. **Minimal generic-API decision.** Prefer broad existing kinds plus the
   smallest additive stable-ID form (e.g. `impl:<fact-class>:<subject>`)
   over new kinds. Fix `-dnu` — and the `human-valve`/`valve` mismatch — in
   the same ratified pass. Make kind↔prefix lockstep a ratified constraint
   with a mechanical check. Decide the `HandoffKind` for detector-staleness
   handoffs explicitly. Tests required for simultaneous-facts-per-subject,
   deterministic ids, and cross-class distinctness.
4. **Validation posture: retire silent drop.** `compose_needs_attention`
   currently DROPS items failing id validation (test-pinned), and direct
   dataclass construction bypasses validation entirely — a producer-side
   false-green channel one layer below homelab's research/009 R3. Ratify
   refuse-loudly / Result-typed / malformed-marker — never omit. Negative
   control: one invalid + one valid candidate must yield a **visible
   failure**, not a shorter list.
5. **Composer-vs-schema-only decision**, default **schema-only** (this
   repository owns vocabulary, grammar, shape, validation; producers
   construct). Name the id-formatting authority either way.
6. **Dependency-direction refusal, provable.** No consumer imports, no
   ledger/journal/config reads, no executable-command resolution. Facts
   arrive as already-derived pure inputs.
7. **Repo-native evidence.** Red-Green-Replay pairs for every product `.py`
   delta, Result-railway public API, property-based tests on pure modules,
   heading-coverage co-edits, `cross_repo_public_api` reconciliation with
   named consumption sites, release only via a release-please tag.
8. **Release + ORDERED per-consumer fan-out matrix** built from ACTUAL
   shapes and pins, to be re-verified at filing time rather than copied
   from the reviews: vendoring consumers (core, beads-fabro, git-jsonl —
   whose vendored/dev skew is reconciled here), installed-package consumer
   (overseer — its real leg stated, not an invented vendor bump), and wire
   consumer (console — graded by a producer-payload wire test, no pin
   invented). Decide the semver class of additive `Literal` members against
   BOTH this repository's rules and core's, and state the
   additive-for-wire / coordinated-for-typed stability guarantee.
9. **Ordered activation/rollback contract.** Consumers validate before
   producers emit. Version skew must yield absence-of-new-facts or an
   explicit unavailable state — **never false resolution** of existing
   attention.
10. **Prior art cited**: `livespec-runtime/livespec-runtime-bvtkzm`,
    `-xtri75`, `-o96`, `-76j`, `-dnu`, `-ego` (an attention item must carry
    an actionable handoff, not a pointer), plus the v008/v011
    pure-extraction precedents. Consumer evidence names tags from
    authoritative sources only — the git tag and the release manifest,
    never `README.md` (stale at `v0.3.1`) and never a committed lockfile
    (`uv.lock` says `0.21.2`; the authoritative tag is `v0.21.3`).

## Sequencing and constraints

- **The baseline propose-change is the critical path.** The parallel
  `homelab-loop-hardening-orchestrator` filing's needs-attention
  deliverables wait on it.
- **Generic, not local.** Everything ratified here must be consumable by any
  adopter, not shaped to homelab.
- **Merging is not deploying.** A consumer counts as consuming only after
  its own pin/vendor/wire evidence exists.
- **Nothing pre-exists.** This repository's tenant was swept 2026-08-25:
  63 records, zero hits for any plan slug. Positive controls in the same
  sweep: `attention` 58, `needs-attention` 25.

## Next action

Author the baseline ratification propose-change (charge point 1) and run it
through `propose-change` → independent review → `revise`. It is recorded as
the single next action on this thread's plan epic.
