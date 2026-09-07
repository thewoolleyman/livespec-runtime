# 005 — Public-surface reconciliation for `livespec-runtime-mqsxsu.4`

Prepared 2026-09-06 by the factory implement stage for
`livespec-runtime-mqsxsu.4` (absorbs `livespec-runtime-vbofkr`, gap
`gap-vjxowbbp`), under the batch-1 ruling in research/003 §5: the mechanical
half — an `__all__`-versus-inventory check plus the group-3 narrowing — is
dispatchable; **the documentation half is a propose-change → revise pass that
the dispatch prompt must authorize explicitly**. This dispatch prompt did not,
and AGENTS.md forbids materializing `SPECIFICATION/proposed_changes/` on the
maintainer's behalf, so the documentation half is PREPARED here (§5) rather
than landed.

## 1. Re-measurement, and the method that must be used

Measured against `HEAD` of this branch, over the first-party structural
universe (`livespec_runtime/**/*.py`, minus the `# @generated` verbatim port):

| quantity | count |
|---|---|
| modules declaring a non-empty `__all__` | 34 |
| `###` module sections in contracts.md "Module-level public surface" | 18 |
| exporting modules with NO section | 16 |
| exported (module, name) pairs | 173 |
| distinct exported names | 148 |
| names not appearing in the inventory | 86 pairs / 69 distinct |
| …of those, inside a RATIFIED module | **0** (was 3 before this changeset) |

The method is a WORD-BOUNDARY match over the inventory section. Searching for
the backticked bare name is wrong and manufactures roughly 44 phantom findings,
because the inventory backticks full signatures (`lane_of(*, item, ...)`), so a
bare `` `lane_of` `` never matches. The item's own caveat says this; it is
restated in the check's docstring so the next re-measurement cannot repeat it.

The 69/86 that remain are ALL inside the 16 unratified modules — i.e. the
inventory is now exactly self-consistent for every module it claims to cover.

## 2. Group 1 — modules with no ratified section: the v012 question, answered

Handoff 1 of `homelab-loop-hardening-runtime` (research/001 §"Shipped-but-
unratified is broader than attention") left open whether `hygiene_scan*`,
`credentials`, `github_budget*`, and `spec_governance` ride the baseline or are
recorded as debt. **It is already answered in the ratified spec**, and that is
the finding: `SPECIFICATION/spec.md`, section "Public surface", says

> Some shipped modules remain outside the ratified inventory:
> `livespec_runtime.hygiene_scan` and its companion modules,
> `livespec_runtime.credentials`, the `livespec_runtime.github_budget` family,
> and `livespec_runtime.spec_governance`. Their absence is ACKNOWLEDGED DEBT,
> not a claim that they are implementation detail. […] Each MUST be ratified or
> explicitly declared internal in a subsequent proposal.

So the disposition is **record-as-debt**, ratified, not a fresh decision for
this dispatch to make. What was missing was any mechanical hold on it: prose
said "acknowledged debt" and nothing enumerated WHICH modules or noticed a new
one joining them. `tests/public-surface-debt.json` now enumerates all 16, each
row citing that clause, and the check refuses a 17th. The register is
shrink-only: a row whose module gets ratified, gets declared internal, or stops
exporting fails as stale until it is deleted.

One module in the register is NOT covered by that ratified paragraph and is
therefore a genuine gap rather than recorded debt —
`livespec_runtime.cross_repo.providers.github_process`, a size-decomposition
split-out of the ratified `cross_repo.providers.github` section. It is
registered with `disposition: gap-not-yet-recorded-as-debt` and carried into §5.

## 3. Group 2 — omissions from a section that exists: closed

The item's named examples, `GithubFailure` and `GithubQueryFailed`, were fixed
before this dispatch (they are documented under
`### livespec_runtime.cross_repo.providers.github`). Re-measurement found the
remaining three: `http_get_json`, `http_post_json`, and
`resolve_installation_id`, exported by `livespec_runtime.github_auth.mint`,
which HAS a ratified section. They were disposed of as group 3 — see §4 — and
group 2 is now empty. That is why the check does not carry a per-name debt
list: a name in a ratified module must be documented or dropped, never
registered.

## 4. Group 3 — names that should not be public

Three sub-cases, three different dispositions. None was auto-documented, per
the item's explicit warning.

**(a) `mint`'s two HTTP seams and the resolution step — NARROWED.** Dropped
from `livespec_runtime/github_auth/mint.py`'s `__all__`. The ratified section
documents this module as the mint entry point plus the injectable seam bundle;
the urllib pair is reached through `DEFAULT_MINT_SEAMS` and installation
resolution is a documented STEP of `mint_installation_token`. Nothing outside
`mint.py` and its own tests imports the three names. This is the group-3
narrowing the ruling made dispatchable.

*Versioning classification, per `non-functional-requirements.md` section
"Versioning":* **Major** — removing a public symbol — which the pre-major
provision releases as a MINOR `0.X.0` bump, not `1.0.0`. The commit declares it
with a `!` marker and a `BREAKING CHANGE:` footer, which is also what
`release_bump_classification` requires: that check reads `__all__` under
`source_trees` and refuses a bump weaker than the surface delta. Runtime blast
radius is nil — `__all__` governs the declared surface and `import *`, not
direct imports — but the conservative classification is the one the item calls
for and the cheaper error.

**(b) `FIError` / `BASE_62_DIGITS` — NOT narrowed, out of scope by an existing
rule.** `work_items/_fractional_indexing.py` is a verbatim third-party port
marked `# @generated` (commit 0ad3f8c) precisely so `is_generated()` drops it
from every structural check's first-party universe. Its `__all__` is
livespec-added conformance metadata over upstream bytes, not a declaration of
this library's surface, and the ratified surface for the algorithm is the
keyword-only wrapper in `work_items/rank.py`. Editing the port to drop two
names would deviate it from upstream to restate what the universe rule already
says. No narrowing, therefore no Versioning classification is triggered. The
exclusion is not silent: the register enumerates the port WITH the five names
it takes out of scope, and a re-vendoring that changes that `__all__` fails
until the register is restated.

**(c) The `main` / `run` CLI entry points — DEFERRED to the family, on
purpose.** They live in `hygiene_scan.py` and `hygiene_scan_cli.py`, both
group-1 debt. Narrowing them now would pre-empt the very proposal that must
decide whether the family is ratified or declared internal, and it would be the
same mistake in the other direction as auto-documenting them. They are
registered with that reasoning on the row.

*Aside worth recording:* a whole-file word-boundary match CREDITS `main` and
`run` from prose elsewhere in the inventory (`credential_helper`'s ratified
`main(...)` signature), so a name-only check would have let these two launchers
through. That is why the check's first obligation is at MODULE level — a module
with no ratified section owes a register row regardless of how its names
happen to spell.

## 5. Prepared propose-change payload (the documentation half — NOT landed)

Two items, both for the maintainer's spec lane. Neither is a blocker for the
mechanical half; both are what would let register rows be deleted.

### 5a. `github_process` is unratified and unrecorded

`SPECIFICATION/spec.md`, section "Public surface", enumerates the debt
families, and `livespec_runtime.cross_repo.providers.github_process` is in none
of them — the paragraph's "and its companion modules" attaches to
`hygiene_scan` only. The module exports `GithubFailure` and `GithubQueryFailed`
(both documented under the provider's own section) plus `completed_gh` (not
documented anywhere). It exists because `providers/github.py` was decomposed
for size, so the split moved surface out from under a ratified heading without
anyone deciding what the new module is.

Proposed delta — one of two, maintainer's call:

1. *Preferred.* Document `completed_gh` under
   `### livespec_runtime.cross_repo.providers.github_process`, a new section
   naming it a support module of the provider, and state that its re-exports
   are the provider section's names. Then delete the register row.
2. *Alternative.* Extend spec.md's debt paragraph to name it, keeping the
   register row with `disposition: acknowledged-debt`.

Option 1 is the recommendation: the module is inside a ratified family, and
recording a fresh module as debt the same day it is noticed is how the original
70 accumulated.

### 5b. The 16 unratified modules, and the scenario half of `gap-vjxowbbp`

The absorbed `livespec-runtime-vbofkr` asks that scenarios for the `github_auth`
and `work_items` public symbols be "decided per module family in this
reconciliation, co-edited with heading coverage in the same propose-change, or
consciously exempted with the reason recorded". Decided, per family:

- `github_auth` — its five modules are all RATIFIED and now export exactly
  what the inventory documents (§4a closed the last gap). Its scenario coverage
  is a scenarios.md question, not a public-surface question; it rides the same
  propose-change that ratifies a family, not this reconciliation. Recorded as
  consciously deferred, with that reason.
- `work_items` — same posture: ratified sections, no undocumented exports.
- The 16 debt modules — no scenarios are owed until the ratify-or-declare-
  internal proposal decides which of them have consumer-visible behavior at
  all. Writing scenarios first would presume the answer.

Handoff, once the maintainer takes the documentation half:

```
/livespec:propose-change public-surface-inventory-completes-shipped-modules
```

with a body that, per family, either ratifies the module (a `###` section with
per-symbol bullets, plus its `tests/heading-coverage.json` entry co-edited in
the same proposal per this repo's revise discipline) or declares it internal
(and then the family's `__all__` narrows, which is a Major classification
released as a minor bump under the pre-major provision). Then
`/livespec:revise --only-topic public-surface-inventory-completes-shipped-modules`.
Each family ratified or declared internal deletes its rows from
`tests/public-surface-debt.json`; when the register empties, the file and its
two register-shaped tests go with it.

## 6. What landed here

- `livespec_runtime/github_auth/mint.py` — `__all__` narrowed to the ratified
  five (§4a), with the paired assertion in `tests/.../test_mint.py`.
- `tests/livespec_runtime/test_public_surface_inventory.py` — the mechanical
  check: four assertions, both directions, proven to fail on an undocumented
  name in a ratified module, on an unregistered exporting module, and on a
  stale register row.
- `tests/public-surface-debt.json` — the enumerated, shrink-only register.
- `tests/heading-coverage.json` — `contracts.md` "Module-level public surface"
  now maps to the new test. Its prior `TODO` reason said "Whatever closes
  livespec-runtime-mqsxsu.4 is the right mapping for this heading"; this is it.
