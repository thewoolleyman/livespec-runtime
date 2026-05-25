---
topic: doctor-findings-bundle-second-pass
author: claude-opus-4-7
created_at: 2026-05-25T19:45:00Z
---

## Proposal: rename-exhaustive-live-walk-to-per-variant-live-walk

### Target specification files

- SPECIFICATION/spec.md

### Summary

Rename the terminology entry "Exhaustive live walk" (and its in-prose
reference) to "Per-variant live walk", and rewrite the definition so it
no longer suggests a multi-source overlay. The current entry reads "for
each entry, walk every extant view the library can directly access… and
return the first definitive `RefStatus`", which implies a fallback chain
across multiple views. The actual contract in `contracts.md` §"Resolution
semantics" and the impl in `livespec_runtime/cross_repo/resolve.py`
dispatch each variant to exactly ONE view: LocalDep → `local_status_lookup`;
SiblingWI → `sibling_status_lookup`; PR → `gh pr view`; Branch →
`branch_exists_on_remote` (then conditionally `branch_merged_into_default`).
"Exhaustive" connotes "try them all" — but the v1 surface has no such
walk.

### Motivation

/livespec:doctor surfaced this as `doctor-llm-objective-conceptual-fidelity`
[severity: medium]: the terminology and the operational semantics fight
each other. Readers who internalize "exhaustive walk" will look in the
code for a fallback chain that doesn't exist. The fix is the terminology,
not the semantics — "Per-variant live walk" preserves the
no-cache / always-fresh / degrade-to-UNKNOWN properties without claiming
multi-source overlay.

### Proposed Changes

1. Edit `SPECIFICATION/spec.md` lines 52-53 (the §"Terminology"
   intro bullet's prose mention):

```diff
-resolve-ref's exhaustive walk, gh-CLI subprocess dispatch, retry backoff.
+resolve-ref's per-variant live walk, gh-CLI subprocess dispatch, retry backoff.
```

2. Edit `SPECIFICATION/spec.md` lines 70-77 (the terminology entry):

```diff
-**Exhaustive live walk** — The resolution policy this library
-implements: no cache; for each entry, walk every extant view the
-library can directly access (GitHub via `gh`, caller-supplied lookups)
-and return the first definitive `RefStatus`; degrade to `UNKNOWN`
-rather than raising. Local clones are NOT walked by the library
-directly at v1; consumers that want a local-clone view wire it through
-`sibling_status_lookup`. The walk is per-call, not pre-computed;
-consumers that need batching MUST batch at the call site.
+**Per-variant live walk** — The resolution policy this library
+implements: no cache; for each entry, dispatch on the entry's
+`kind` and consult the single view defined for that variant
+(LocalDep → caller's `local_status_lookup`; SiblingWI → caller's
+`sibling_status_lookup` when configured; PR / Branch → GitHub via
+`gh`). Degrade to `UNKNOWN` rather than raising. Local clones are
+NOT read by the library directly at v1; consumers that want a
+local-clone view wire it through `sibling_status_lookup`. The walk
+is per-call (always fresh, no memoization), not pre-computed;
+consumers that need batching MUST batch at the call site.
```

3. Edit `SPECIFICATION/constraints.md` line 108 (the "exhaustive-walk
   policy" reference under §"Forbidden patterns"):

```diff
-  exhaustive-walk policy.
+  per-variant-walk policy.
```

The impl module docstrings in `livespec_runtime/cross_repo/resolve.py`
that also use the "exhaustive live-walk" phrase are addressed by the
impl-side `refresh-impl-docstring-version-pins` work-item below; the
two cleanups travel together.


## Proposal: trim-spec-md-public-surface-to-pointer

### Target specification files

- SPECIFICATION/spec.md

### Summary

Reduce `spec.md` §"Public surface" (lines 86-115) from a re-enumeration
of importable symbols to a 2-3 line summary that points at
`contracts.md` §"Module-level public surface". The current text
duplicates the symbol catalog already canonicalized in `contracts.md`,
which violates the livespec-template content-shape rule: `spec.md`
carries intent and architecture; `contracts.md` carries the importable
surface inventory.

### Motivation

/livespec:doctor surfaced this as
`doctor-llm-subjective-template-compliance` [severity: medium]:
spec.md:86-115 re-states what contracts.md:9-115 already specifies.
Future revisions risk drift between the two enumerations. Reducing
spec.md to a pointer makes `contracts.md` the single source of truth
and eliminates the drift class.

### Proposed Changes

Edit `SPECIFICATION/spec.md` lines 86-115 (the entire §"Public surface"
section):

```diff
-## Public surface
-
-Consumers import directly from the sub-modules, not the package
-namespace. The public surface:
-
-- `livespec_runtime.cross_repo.types` — typed `DependsOnEntry` union
-  (`LocalDependency`, `SiblingWorkItemDependency`,
-  `PullRequestDependency`, `BranchDependency`); the `CrossRepoManifest`
-  / `CrossRepoTarget` view of the `cross_repo_targets` block; the
-  `RefStatus` enum (`OPEN`, `CLOSED`, `UNKNOWN`); and the
-  `parse_depends_on_entry` / `parse_cross_repo_manifest` dict-to-typed
-  boundary helpers.
-- `livespec_runtime.cross_repo.errors` — `CrossRepoSchemaError`, the
-  single domain error raised by the parser helpers.
-- `livespec_runtime.cross_repo.providers.github` — the gh CLI
-  subprocess dispatch surface (`query_pull_request_state`,
-  `branch_exists_on_remote`, `branch_merged_into_default`,
-  `NonCanonicalGithubUrlError`).
-- `livespec_runtime.cross_repo.retry` — `retry_with_backoff`
-  implementing the 3-attempt 1s/2s backoff policy (see
-  `contracts.md` §"Retry policy" for the full description,
-  including the reserved-but-unused 4.0s constant).
-- `livespec_runtime.cross_repo.resolve` — `resolve_ref`, the entry
-  point that takes a typed `DependsOnEntry` + `CrossRepoManifest` +
-  two caller-supplied lookups and returns a `RefStatus`.
-
-All other names in the package tree are implementation detail. Removing
-or renaming any of the above is a major-version bump. Adding new
-functions is a minor-version bump. Internal refactors that do not change
-the public surface are patch-version bumps.
+## Public surface
+
+Consumers import directly from the sub-modules under
+`livespec_runtime.cross_repo`, not from the package namespace. The
+importable-symbol inventory is canonicalized in `contracts.md`
+§"Module-level public surface"; that section is the single source of
+truth for what is in v1's stable API and which fields each variant
+carries. All other names in the package tree are implementation
+detail. Versioning rules for surface changes live in `contracts.md`
+§"Versioning".
```


## Proposal: consolidate-inherited-from-livespec-into-non-functional-requirements

### Target specification files

- SPECIFICATION/constraints.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Move the full "inherited from livespec" inventory into
`non-functional-requirements.md` and replace
`constraints.md` §"Inherited from livespec" with a one-line pointer.
The two files currently both restate overlapping bullet lists
(toolchain pins, ruff, pyright strict-plus, 100% coverage, lefthook,
Conventional Commits, kw-only dataclasses) — the redundancy violates
NLSpec economy and forces readers to cross-check which file is
authoritative.

### Motivation

/livespec:doctor surfaced this as
`doctor-llm-subjective-nlspec-conformance: economy` [severity: low]:
constraints.md:14-27 and non-functional-requirements.md:26-41
substantively overlap. Because the inherited rules are primarily
contributor-facing (build/lint/test/release), the natural home is
`non-functional-requirements.md`. `constraints.md` retains its
architecture-level rules; the inherited list becomes a single bullet
pointing at the NFR file.

### Proposed Changes

1. Delete `SPECIFICATION/constraints.md` §"Inherited from livespec"
   (lines 7-27) entirely and replace with a short pointer paragraph:

```markdown
## Inherited from livespec

Every constraint in
`livespec/SPECIFICATION/non-functional-requirements.md` applies to
this library without restatement. The contributor-facing inherited
rules (toolchain pins, ruff/pyright/test discipline, lefthook
ordering, Conventional Commits, dataclass conventions) are catalogued
in this library's own
`SPECIFICATION/non-functional-requirements.md` §"Inherited from
livespec"; the rules below are architecture-level constraints
specific to this library's resolution substrate.
```

2. Leave `SPECIFICATION/non-functional-requirements.md` §"Inherited
   from livespec" as the canonical inventory; no edit needed there
   beyond ensuring the list is the complete contributor-facing
   inherited set.


## Proposal: name-required-and-optional-lookups-in-spec-md-public-surface

### Target specification files

- SPECIFICATION/spec.md

### Summary

When the §"Public surface" trim above lands (sibling proposal
`trim-spec-md-public-surface-to-pointer`), the surviving prose mentions
`resolve_ref` only briefly. The replacement text MUST name
`local_status_lookup` as REQUIRED and `sibling_status_lookup` as
OPTIONAL (default `None` ⇒ `SiblingWorkItemDependency` resolves to
`UNKNOWN`). Without that distinction, a reader who stops at `spec.md`
will assume both lookups are required.

### Motivation

/livespec:doctor surfaced this as `doctor-llm-subjective-prose-quality`
[severity: low]: spec.md:108-110 reads "two caller-supplied lookups"
without the required/optional split, even though the split is
contractual (the `None` branch ALWAYS collapses sibling resolution to
`UNKNOWN`). The reader should be able to learn the required/optional
shape without leaving spec.md, even after the trim above moves the
full signature into contracts.md.

### Proposed Changes

This proposal is contingent on
`trim-spec-md-public-surface-to-pointer` landing first. After that
edit, the surviving §"Public surface" prose still references
"caller-supplied lookups"; supplement it with the required/optional
distinction (suggested insertion at the end of that paragraph):

```markdown
The `resolve_ref` callable takes a REQUIRED `local_status_lookup`
(used for `LocalDependency` resolution) and an OPTIONAL
`sibling_status_lookup` (used for `SiblingWorkItemDependency`
resolution; absent ⇒ those resolutions return `RefStatus.UNKNOWN`).
The exhaustive signature lives in `contracts.md`
§"Module-level public surface".
```

If `trim-spec-md-public-surface-to-pointer` does NOT land, this
proposal applies as a stand-alone edit to the existing
`livespec_runtime.cross_repo.resolve` bullet on spec.md lines
108-110 (replacing "two caller-supplied lookups" with the explicit
REQUIRED / OPTIONAL phrasing).


## Proposal: add-parse-cross-repo-manifest-failure-scenario

### Target specification files

- SPECIFICATION/scenarios.md

### Summary

Add a Gherkin scenario for `parse_cross_repo_manifest` raising
`CrossRepoSchemaError` when a target dict is missing its REQUIRED
`github_url` field. The two `parse_depends_on_entry` failure paths
have scenarios (`rejects unknown kind`, `rejects missing required
field`); the symmetric failure on the manifest parser does not.

### Motivation

/livespec:doctor surfaced this as
`doctor-llm-subjective-prose-quality` [severity: low]: scenarios.md's
intro paragraph says "adding a new public symbol SHOULD land with at
least one scenario here". `parse_cross_repo_manifest` has one
success-path scenario but zero failure-path scenarios, while the
sibling `parse_depends_on_entry` has full coverage. Symmetric coverage
clarifies the failure contract.

### Proposed Changes

Add the following scenario to `SPECIFICATION/scenarios.md` immediately
after the existing `## Scenario: parse_cross_repo_manifest accepts
minimal target` block (currently lines 102-108):

```gherkin
## Scenario: parse_cross_repo_manifest rejects target missing github_url

Given a dict {"livespec": {"default_branch": "main"}}
When parse_cross_repo_manifest is invoked
Then CrossRepoSchemaError is raised
And the error detail names "github_url" as the missing field for slug "livespec"
```


## Proposal: relocate-versioning-section-to-non-functional-requirements

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Move `contracts.md` §"Versioning" (lines 222-235) to
`non-functional-requirements.md` §"Release flow" (or as a sibling
subsection next to it). The current section is release-discipline
prose — semver bump rules, pin-and-bump consumer responsibility —
which fits the NFR file's role (contributor-facing
build/test/release invariants) rather than `contracts.md`'s role
(wire-level / CLI-level contracts).

### Motivation

/livespec:doctor surfaced this as
`doctor-llm-subjective-template-compliance` [severity: low]:
contracts.md §"Versioning" is not wire-level / CLI-level surface; it
describes how versions are bumped and what consumers must do at
bump time. The livespec template's "contracts.md content is
wire-level / CLI-level; does NOT contain implementation prose or
constraint declarations" guidance places this content one file over.

### Proposed Changes

1. Move the entire §"Versioning" block from `contracts.md` (lines
   222-235) to `non-functional-requirements.md` under a new
   §"Versioning" subsection, positioned immediately before the
   existing §"Release flow" section. The relocated content stays
   verbatim.

2. Replace the now-empty §"Versioning" anchor in `contracts.md` with
   a short pointer:

```markdown
## Versioning

Semver bump rules and the consumer pin-and-bump mechanism live in
`non-functional-requirements.md` §"Versioning". Surface-change
classifications (additions / removals / refactors) are referenced
by `spec.md` §"Public surface" and by the per-symbol bullets above.
```


## Proposal: resolve-dangling-templates-library-reference

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Replace the dangling forward-reference to `templates/library/` in
`non-functional-requirements.md` line 31 with either an upstream
livespec work-item link or remove the parenthetical entirely. As
written, the reader has no path to the extracted-templates concept,
and the note does not itself define a follow-up that anyone in this
repo can act on.

### Motivation

/livespec:doctor surfaced this as
`doctor-llm-objective-dangling-reference` [severity: low]: the bullet
"Drift between `.mise.toml` here and `livespec`'s `.mise.toml` is a
follow-up to detect via tooling once `templates/library/` is
extracted" references an upstream extraction with no link or local
glossary entry. If the extraction is genuinely planned upstream, the
reference SHOULD point at a livespec work-item id. If it is
aspirational, the bullet SHOULD be deleted to avoid dead weight.

### Proposed Changes

Replace line 31 in `SPECIFICATION/non-functional-requirements.md`
(under §"Inherited from livespec", the first bullet) with one of
the two forms below. The choice is for `/livespec:revise` to make
based on upstream livespec state at revision time:

- **If upstream `templates/library/` work-item exists**: rewrite as
  "Drift between `.mise.toml` here and `livespec`'s `.mise.toml` is a
  follow-up to detect via tooling once livespec's `templates/library/`
  extraction (upstream work-item `<id>`) lands." Replace `<id>` with
  the actual work-item identifier.
- **If no concrete upstream work-item exists**: delete the parenthetical
  "(`templates/library/` is extracted)" entirely and leave the bullet
  as "Drift between `.mise.toml` here and `livespec`'s `.mise.toml` is
  a follow-up to detect via tooling."


## Proposal: document-or-harden-branch-existence-404-detection

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Document `branch_exists_on_remote`'s 404-detection mechanism on the
contract bullet (currently lines 77-79) so consumers and reviewers
know what makes the False return correct. The companion impl change
(harden the substring-on-stderr probe to use `gh`'s exit code or
`--jq`-parsed body) is filed as an impl-side work-item below; the
two travel together.

### Motivation

/livespec:doctor surfaced this as `doctor-llm-subjective-spec-impl-drift`
[severity: low]: contracts.md says "404 responses translate to False"
but does not specify the detection mechanism. The current impl probes
`"404" in exc.stderr`, which is fragile (any unrelated stderr text
containing the substring "404" — a body fragment, an HTTP 404-redirect
mention — would mis-categorize as a missing branch). Documenting
either makes the consumer aware of the fragility, or motivates the
hardening work-item.

### Proposed Changes

Edit `SPECIFICATION/contracts.md` lines 77-79:

```diff
-- `branch_exists_on_remote(*, github_url: str, name: str) -> bool` —
-  returns True iff the named branch exists on the remote. 404 responses
-  translate to `False`; any other CalledProcessError propagates.
+- `branch_exists_on_remote(*, github_url: str, name: str) -> bool` —
+  returns True iff the named branch exists on the remote. The impl
+  invokes `gh api repos/<owner>/<name>/branches/<branch>` and treats
+  a 404 response as `False`. The 404 SHOULD be detected via `gh`'s
+  exit code (or a structured response field), not via a substring
+  match on stderr; consumers MAY rely on the False return for any
+  branch the remote does not currently host. Any other
+  CalledProcessError propagates.
```


## Proposal: merge-what-this-spec-is-not-into-scope-boundary

### Target specification files

- SPECIFICATION/spec.md

### Summary

Merge `spec.md` §"What this spec is not" (lines 117-129) into the
preceding §"Scope boundary" (lines 26-42). The two sections cover the
same material from positive (what the spec describes) and negative
(what the spec does not) angles; the negative bullets read as exclusions
of the positive scope.

### Motivation

/livespec:doctor surfaced this as
`doctor-llm-subjective-nlspec-conformance: economy` [severity: low]:
both sections restate the spec's boundary against `livespec`'s
upstream contract. NLSpec economy favors one cohesive boundary
section over a positive section plus a parallel negative section.

### Proposed Changes

Delete `SPECIFICATION/spec.md` §"What this spec is not" entirely
(lines 117-129) and, if any of its bullets carry information that
§"Scope boundary" does not already imply, append a short "Out of
scope:" paragraph to the end of §"Scope boundary" enumerating those
items (e.g., "Out of scope: re-statement of upstream contracts;
Python implementation manual content; doctor-invariant catalog
extracted into livespec-core").


## Proposal: name-cross-repo-manifest-targets-attribute-in-contracts

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Specify `CrossRepoManifest`'s `.targets` dict attribute on the
`contracts.md` bullet (currently lines 54-56). Consumers access
`manifest.targets[slug]` (as the resolve walker does in
`livespec_runtime/cross_repo/resolve.py`), but the contract describes
the dataclass as "wrapping a `dict[str, CrossRepoTarget]`" without
naming the field. Pinning the attribute name is necessary for the
v1 stable surface to be load-bearing.

### Motivation

/livespec:doctor surfaced this as
`doctor-llm-subjective-spec-impl-drift` [severity: low]: the impl
exposes `.targets` as the access point; the spec doesn't name it.
Future refactors could rename the attribute without flagging a
major-version bump because the contract never named what was being
renamed.

### Proposed Changes

Edit `SPECIFICATION/contracts.md` lines 54-56:

```diff
-- `CrossRepoManifest` — a frozen, slotted, kw-only dataclass wrapping
-  a `dict[str, CrossRepoTarget]` keyed by the consumer-chosen repo
-  slug used as the `repo` field on cross-repo `DependsOnEntry` variants.
+- `CrossRepoManifest` — a frozen, slotted, kw-only dataclass with a
+  single REQUIRED field `targets: dict[str, CrossRepoTarget]`, keyed
+  by the consumer-chosen repo slug used as the `repo` field on
+  cross-repo `DependsOnEntry` variants. Consumers access entries via
+  `manifest.targets[slug]`; renaming or removing the `targets`
+  attribute is a major-version bump.
```


## Impl-side follow-ups (filed as work-items, not spec changes)

The two findings below are implementation changes, not spec changes;
they are noted here for traceability and SHOULD be filed as
`livespec-impl-plaintext` freeform work-items once
`work-items.jsonl` is initialized (the static `no-stalled-epic` /
`no-orphan-dependency` invariants currently `pass` because the store
does not yet exist).

### Work-item: refresh-impl-docstring-version-pins

Affected files (7 occurrences):

- `livespec_runtime/cross_repo/__init__.py`
- `livespec_runtime/cross_repo/errors.py`
- `livespec_runtime/cross_repo/providers/__init__.py`
- `livespec_runtime/cross_repo/providers/github.py`
- `livespec_runtime/cross_repo/resolve.py`
- `livespec_runtime/cross_repo/retry.py`
- `livespec_runtime/cross_repo/types.py`

Replace every occurrence of `livespec/SPECIFICATION/contracts.md
v072 §"…"` with either `livespec/SPECIFICATION/contracts.md
§"…"` (drop the version pin entirely — the `.livespec.jsonc`
`livespec-runtime.compat.pinned` field is the authoritative pin
location) or with the actual current pin once the first post-v072
livespec release tag lands. The `compat.pinned` value is `"master"`
during bootstrap, so the docstring pins are stale; dropping them
eliminates the drift class entirely.

When this work-item lands, the `livespec_runtime/cross_repo/resolve.py`
module docstring's "exhaustive live-walk" phrase (line 1) should also
be replaced with "per-variant live-walk" to align with the spec
edit in `rename-exhaustive-live-walk-to-per-variant-live-walk`.

### Work-item: harden-branch-exists-404-detection

File: `livespec_runtime/cross_repo/providers/github.py` lines 96-99.

Replace the current `"404" in exc.stderr` substring probe with a
more robust detection. Two options:

1. Inspect `exc.returncode` and parse `gh`'s stderr line-by-line
   for the structured "HTTP 404" prefix.
2. Use `gh api --silent` with an explicit `--jq` query that returns
   a stable success/failure shape, then branch on the parsed
   output instead of the stderr text.

Either approach unblocks the spec's documented contract (the spec
change in `document-or-harden-branch-existence-404-detection` lands
alongside this work-item).

These two work-items SHOULD be filed via
`/livespec-impl-plaintext:capture-work-item` after this proposed
change is accepted and the spec edits are revised in.
