# non-functional-requirements.md — livespec-runtime

Dev-environment, repository-tooling, build/test, and contributor-workflow
invariants that are NOT visible at the consumer-facing import surface.
Every rule here is a binary, mechanically-checkable invariant; lint /
type-check / test failures are the enforcement mechanism.

## Boundary

This file covers contributor-facing invariants: how the repo is built,
tested, linted, version-controlled, and released. It does NOT cover:

- The library's import-surface API — see `contracts.md` §"Module-level
  public surface".
- The library's architectural / runtime constraints — see
  `constraints.md`.
- The cross-repo resolution semantics consumers depend on — see
  `contracts.md` §"Resolution semantics".
- Worked-example flows — see `scenarios.md`.

When a contributor-facing rule conflicts with an inherited rule from
`livespec/SPECIFICATION/non-functional-requirements.md`, the upstream
rule wins.

## Inherited from livespec

The library follows livespec-core's `non-functional-requirements.md` in
full. Notable inherited rules (NOT re-stated, listed for orientation):

- Toolchain pins managed by mise (`uv`, `just`, `lefthook`) and uv
  (Python interpreter + every Python package). Drift between
  `.mise.toml` here and `livespec`'s `.mise.toml` is a follow-up to
  detect via tooling.
- Ruff lint + format with the upstream rule set.
- Pyright strict mode with the strict-plus diagnostics.
- 100% line + branch coverage on `livespec_runtime/`.
- Pytest discipline; hypothesis property-based tests on pure modules.
- Conventional Commits subjects; rebase-merge-only master.
- Lefthook pre-commit / commit-msg / pre-push step ordering.
- Keyword-only arguments; frozen kw-only dataclasses.
- Domain errors vs bugs split.

## Task-runner discipline

- `just` is the single canonical entry point for every dev-tooling
  invocation in this repo (per the upstream livespec convention).
  Direct invocations of `ruff`, `pyright`, `pytest`,
  `coverage`, or `gh` in lefthook hooks or CI YAML are FORBIDDEN; all
  such invocations MUST go through a `just <target>` indirection.
- The `just check` target is the load-bearing aggregate. It MUST run
  lint, format-check, types, tests, and coverage in that order and
  exit non-zero on any failure. Lefthook pre-push MUST invoke `just
  check` (the full aggregate). CI MAY run the aggregate as a
  per-target matrix of individual `just check-<slug>` jobs — for
  job-level parallelism, per-job status visibility, the
  second-checkout `check-doctor-static` job, and zero-`.py` subsetting
  per livespec `SPECIFICATION/contracts.md` §"Pre-commit step
  ordering" — provided the `check-ci-matrix-completeness` guard proves
  the CI job set is a superset of the aggregate (excluding the
  pre-push-only world-gate checks), so no canonical slug the aggregate
  runs is silently dropped from CI. Merges are gated on
  the whole matrix by a single all-green gate job (`ci-green`) that
  `needs:` every gating job, per livespec
  `SPECIFICATION/non-functional-requirements.md` §"CI as a merge gate
  (branch protection)"; CI MUST NOT hand-pick a subset that omits a
  canonical slug the aggregate runs without the guard flagging the
  omission. Broadening the CI matrix to cover the full canonical
  aggregate is tracked fleet-wide by the CI-aggregate-coverage epic.

Codex support for this repository is REQUIRED at the contributor-workflow layer. `AGENTS.md` is the Codex-facing source of truth for repository mutation discipline, and repo hooks plus `just check` remain the mechanical enforcement surface. This repo does not currently need project-local `.agents/skills/` livespec adapters because it exposes importable runtime library code rather than a user-facing livespec Driver surface. Runtime code MUST remain agent-runtime-neutral: it MUST NOT branch on Claude Code, Codex, Pi, or any other harness identity. Any future Codex adapter or high-level e2e proof involving this repo MUST document the adapter/proof boundary and include manual Codex verification before support is claimed.

## Repo layout

- `livespec_runtime/` — the importable package. Sub-packages
  (`cross_repo/`, future namespaces) live one level deeper.
- `tests/` — pytest suite. Layout mirrors `livespec_runtime/`
  one-to-one (every module under `livespec_runtime/cross_repo/` has a
  paired `tests/livespec_runtime/cross_repo/test_<module>.py`).
- `SPECIFICATION/` — this spec, governed by livespec.
- This library's own impl tracking lives in its per-repo beads Dolt
  tenant via `livespec-impl-beads` (the legacy repo-root JSONL stores
  are frozen under `archive/`).
- `pyproject.toml`, `uv.lock`, `.mise.toml`, `.livespec.jsonc`,
  `justfile`, `lefthook.yml`, `release-please-config.json`,
  `.release-please-manifest.json` — toolchain configuration; each
  is hand-authored, not templated.

## Prose conventions

- Every version reference in this spec's prose MUST be prefixed
  with the owning project name. Library-local references use
  `livespec-runtime vX.Y.Z`; upstream meta-tool references use
  `livespec vNNN`; sibling impl-plugin references use the
  plugin name (`livespec-impl-git-jsonl v0.x`, etc.). External
  dependency versions follow the same shape (`uv 0.5.x`,
  `gh 2.x`, `Python 3.10+`).
- Inline JSON or TOML example snippets are exempt when the
  version is the value of a typed field whose key already encodes
  the project name (e.g. `livespec-runtime.compat.pinned`,
  `[tool.uv.sources].livespec-runtime`). The structural key
  carries the disambiguation; the value stays unprefixed and
  is automated via the release-please wiring below.

## Build and packaging

- Build backend: `hatchling`.
- Package: a single wheel built from `livespec_runtime/` per
  `[tool.hatch.build.targets.wheel].packages`.
- The package is consumed by every livespec-governed repo via `uv`
  git source; PyPI publication is OUT-OF-SCOPE for v1 (consumers
  install by tag, not by PyPI version).

## Versioning

- Major (`X.0.0`) — removing or renaming a public symbol; changing a
  resolution semantic; tightening a parse contract such that previously
  valid inputs now raise.
- Minor (`0.X.0`) — adding a public symbol; adding a new
  `DependsOnEntry` variant; loosening a parse contract; adding a new
  provider module.
- Patch (`0.0.X`) — internal refactors with no public-surface change;
  bugfixes that align behavior with this contract.

The pin-and-bump mechanism means consumers MAY pin to a major-version
range (`>=0.2.0,<1.0.0`) but MUST also carry an explicit `pinned` tag
in their `.livespec.jsonc` `compat` block. The pinned tag is the
actually-used version; the semver range communicates compatibility.

## Release flow

- Releases are cut via `release-please` (the manifest-mode config at
  `release-please-config.json`). Conventional-Commits subjects on
  master drive the version bump.
- The release-please PR opens automatically when commits with `feat:`
  / `fix:` subjects land on master. Merging the release-please PR
  tags the release.
- The consumer-facing example version literals in
  `SPECIFICATION/contracts.md` carry inline
  `x-release-please-version` sentinel comments. The release-please
  config (`release-please-config.json`) lists
  `SPECIFICATION/contracts.md` under `extra-files` with the `generic`
  updater so each release rewrites the example tags in place. The
  authoritative location for what the consumer copy-paste should
  pin to is therefore always the freshest commit on `master`.
- Every consumer's `.livespec.jsonc` `livespec-runtime.compat.pinned`
  value MUST update via a separate bump-pin PR in the consumer repo.
  This library's release does NOT auto-open bump-pin PRs (v1 deferral;
  manual bump-pin is acceptable).

## Test discipline

- Every public symbol enumerated in `contracts.md` §"Module-level
  public surface" MUST have direct test coverage.
- The `providers/github` module's gh-CLI invocations MUST be tested
  against fixtures (recorded `gh` output), NOT against the live
  GitHub API. Consumers' CI environments cannot be assumed to have
  outbound network or `gh auth`.
- The retry layer's backoff sequence MUST be tested by
  monkeypatching `time.sleep` to a no-op or spy. Tests MUST NOT burn
  real wall-clock seconds on backoff.
- The resolve walker's match-dispatch MUST be tested per variant,
  including the `UNKNOWN` degradation paths.
- **Scenario-tier coverage.** Every `## Scenario:` heading in
  `SPECIFICATION/scenarios.md` MUST have its own entry in
  `tests/heading-coverage.json`; scenarios are tracked granularly,
  one entry per scenario, and several scenarios MAY map to the same
  test (a many-to-one mapping is expected). Each mapped test MUST sit
  at the **integration tier or above** — a consumer-shaped test that
  imports `livespec_runtime` and drives a real workflow (cross-repo
  dependency resolution, manifest parsing, an error path) against
  `tmp_path`-scoped checkouts, asserting on consumer-visible return
  values and error types — never a unit-tier test, since a scenario
  describes consumer-observable behavior. A scenario entry is
  compliant when EITHER (a) its test node-id path component begins
  with one of the integration-tier prefixes declared in this repo's
  `pyproject.toml` `[tool.livespec_dev_tooling].scenario_tiers`
  allowlist (e.g. `tests.consumer`, `tests.e2e`), OR (b) the resolved
  test carries an explicit `pytest.mark.integration` (or stronger)
  marker. A `TODO` entry is permitted during transition provided its
  `reason` explicitly acknowledges this tier requirement. This
  invariant is enforced mechanically by
  `livespec_dev_tooling.checks.heading_coverage` (livespec-dev-tooling
  v0.9.0+).

## Spec evolution

This library's spec evolves through the same livespec lifecycle the
library itself implements support for. The `compat.pinned` value on
this library's `.livespec.jsonc` `livespec-runtime` section is what
doctor's `contract-version-compatibility` invariant consults when
livespec-core checks this library's compatibility with the installed
`livespec` version.
