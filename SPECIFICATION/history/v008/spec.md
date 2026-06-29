# spec.md — livespec-runtime

This is the natural-language specification for `livespec-runtime`, the
shared runtime library that ships the cross-repo dependency-resolution
surface consumed by `livespec`, by every `livespec-impl-*` plugin, and by
`livespec-dev-tooling`. The library dogfoods `livespec` — this
`SPECIFICATION/` tree evolves through `/livespec:seed` /
`propose-change` / `revise` / `doctor` / `prune-history` / `critique`,
exactly the same lifecycle every consumer project uses.

## Purpose

`livespec-runtime` provides one piece: runtime library code consumed at
sub-command execution time by other livespec-governed repos. It is NOT a
Claude Code plugin; it ships no slash commands, no SKILL.md files, no
hooks. It is a plain Python package installed via `uv` git source and
imported from consumer code.

The library exists as a separate repo (rather than living inside
`livespec` or a consumer plugin) so the cross-repo coordination surface
has a single canonical owner with its own release cadence. Each consumer
pins this library by tag in its `pyproject.toml` and bumps the pin via
the same pin-and-bump mechanism `livespec` defines for impl-plugin
coordination.

## Scope boundary

This spec describes ONLY the library's own contracts and discipline. The
decisions this library implements — the four-variant `DependsOnEntry`
shape, the `cross_repo_targets` manifest schema, the resolve-ref
semantics, retry policy, the pin-and-bump mechanism, doctor invariants
that consume `resolve_ref` — are all FIXED upstream in `livespec`'s
`SPECIFICATION/` (its `contracts.md` and `non-functional-requirements.md`).
This `SPECIFICATION/`
MUST NOT re-state `livespec`'s contract; it MUST concretize how this
library realizes the runtime portion of that contract and point upstream
for anything else.

When `livespec`'s contract changes, this library's `compat` block in its
own `.livespec.jsonc` moves forward in a discrete bump-pin PR, at which
point this `SPECIFICATION/` may require companion revisions to honor the
new surface.

Out of scope: re-statement of `livespec`'s cross-repo contract; Python
implementation manual content; the upstream doctor-invariant catalog
that consumes `resolve_ref` (`no-orphan-dependency`,
`no-stalled-epic`'s cross-repo extension) — those live in
`livespec/SPECIFICATION/contracts.md`.

## Terminology

This spec adopts every term defined in `livespec/SPECIFICATION/spec.md`
verbatim. The terms below are library-local additions or
refinements; they extend the upstream glossary, never contradict it.

**Runtime code (this library) vs enforcement-suite code
(livespec-dev-tooling)** — Runtime code runs as part of a sub-command's
working flow: typed dataclass construction, schema parsing,
resolve-ref's per-variant live walk, gh-CLI subprocess dispatch, retry
backoff. Enforcement-suite code runs during build / lint / test gates:
invariant checks, coverage assertion, pyright/ruff configuration. The
split exists because runtime code is consumed by every
livespec-governed repo's actual operation, while enforcement-suite code
is consumed only by the repo's own pre-commit and CI surface. Mixing
them inflates the runtime repo's contract surface and forces every
consumer to pull every enforcement-suite dependency at runtime.

**Cross-repo dependency** — A `depends_on` entry on a work-item that
points OUTSIDE the consumer repo: another livespec-governed sibling
repo's work-item, a GitHub pull request, or a GitHub branch. Cross-repo
dependencies are the contract surface this library exists to resolve.
Same-repo dependencies (`kind: local`) flow through this library's
typing boundary but their resolution is a no-op pass-through to the
caller-supplied `local_status_lookup`.

**Per-variant live walk** — The resolution policy this library
implements: no cache; for each entry, dispatch on the entry's `kind`
and consult the single view defined for that variant (LocalDep →
caller's `local_status_lookup`; SiblingWI → caller's
`sibling_status_lookup` when configured; PR / Branch → GitHub via
`gh`). Degrade to `UNKNOWN` rather than raising. Local clones are NOT
read by the library directly at v1; consumers that want a local-clone
view wire it through `sibling_status_lookup`. The walk is per-call
(always fresh, no memoization), not pre-computed; consumers that need
batching MUST batch at the call site.

**Canonical github_url** — The string form
`https://github.com/<owner>/<name>` with an optional trailing `.git`
and/or trailing `/`. The library accepts ONLY this form for the
`github_url` field in `cross_repo_targets`; ssh / git-protocol / bare
owner-name / non-github hosts raise `NonCanonicalGithubUrlError` at the
provider boundary.

## Public surface

Consumers import directly from the sub-modules under
`livespec_runtime.cross_repo`, not from the package namespace. The
importable-symbol inventory is canonicalized in `contracts.md`
§"Module-level public surface"; that section is the single source of
truth for what is in v1's stable API and which fields each variant
carries. All other names in the package tree are implementation
detail. Versioning rules for surface changes live in
`non-functional-requirements.md` §"Versioning".

The `resolve_ref` callable takes a REQUIRED `local_status_lookup`
(used for `LocalDependency` resolution) and an OPTIONAL
`sibling_status_lookup` (used for `SiblingWorkItemDependency`
resolution; absent ⇒ those resolutions return `RefStatus.UNKNOWN`).
The exhaustive signature lives in `contracts.md` §"Module-level
public surface".

## Lifecycle and evolution

This `SPECIFICATION/` is governed by `livespec`. Changes land through
the standard livespec lifecycle:

- Propose: `/livespec:propose-change --spec-target SPECIFICATION/`
  drops a file under `proposed_changes/`.
- Critique: `/livespec:critique --spec-target SPECIFICATION/`
  surfaces issues before they ratify.
- Revise: `/livespec:revise --spec-target SPECIFICATION/`
  accepts, modifies, or rejects each pending proposal and snapshots a
  new `history/vNNN/`.
- Doctor: `/livespec:doctor --spec-target SPECIFICATION/` runs static
  + LLM-driven invariants.
- Prune: `/livespec:prune-history --spec-target SPECIFICATION/`
  collapses old history entries.

Every spec change MUST flow through this loop. Direct edits to the
top-level files outside a `revise` snapshot are out-of-process.
