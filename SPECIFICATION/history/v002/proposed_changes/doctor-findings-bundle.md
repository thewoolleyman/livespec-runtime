---
topic: doctor-findings-bundle
author: claude-opus-4-7
created_at: 2026-05-25T16:57:18Z
---

## Proposal: strip-narrative-version-pins-from-spec-prose

### Target specification files

- SPECIFICATION/spec.md
- SPECIFICATION/constraints.md
- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Remove the five narrative `v0.2.0` pins that describe v0-line-stable architecture as if it were version-specific. The library's public surface, the local-clone-not-read state, the runtime-deps inventory, and the release-history paragraph were all written with `v0.2.0` literals, but each describes behavior that is stable across the v0 line or already authoritatively recorded elsewhere (`pyproject.toml`, `uv.lock`, `CHANGELOG.md`). Stripping the pins prevents the drift class entirely — the version literal cannot go stale if it isn't there.

### Motivation

/livespec:doctor surfaced this as `doctor-llm-subjective-spec-impl-drift` [severity: high]: pyproject.toml is at livespec-runtime v0.3.0 (release-please cut the v0.3.0 release in commit e754809) but the SPECIFICATION/ tree references v0.2.0 in eight places. The user's root-cause framing was correct — most of those references should never have carried a version literal in the first place.

### Proposed Changes

Apply the following edits:

- `SPECIFICATION/spec.md` line 87: change `## Public surface\n\nConsumers import directly from the sub-modules, not the package\nnamespace. The public surface as of v0.2.0:` → `## Public surface\n\nConsumers import directly from the sub-modules, not the package\nnamespace. The public surface:`. The major-bump rule on this section already pins surface stability without needing a version literal.
- `SPECIFICATION/constraints.md` line 86-89: change `library's perspective (the v0.2.0 surface does not read local clones\nat all; consumers wire local-clone reading via \`sibling_status_lookup\`).` → `library's perspective (the v1 surface does not read local clones\nat all; consumers wire local-clone reading via \`sibling_status_lookup\`).` so the constraint is pinned to the v1 contract rather than a release tag.
- `SPECIFICATION/constraints.md` line 93-94: change `Python runtime dependencies are pinned in \`pyproject.toml\` and locked\nin \`uv.lock\`. At v0.2.0 the only runtime dep is \`typing_extensions\`.` → `Python runtime dependencies are pinned in \`pyproject.toml\` and locked\nin \`uv.lock\` (see those files for the authoritative current list).`. The spec stops echoing what `pyproject.toml` already names.
- `SPECIFICATION/contracts.md` line 192-195: change `- No Python runtime dependencies at v0.2.0 outside \`typing_extensions\`\n  (for \`assert_never\` on Python <3.11 — the project's\n  \`requires-python\` is \`>=3.10.16\`).` → `- The only Python runtime dependency outside the standard library is\n  \`typing_extensions\` (for \`assert_never\` on Python <3.11 — the\n  project's \`requires-python\` is \`>=3.10.16\`). The authoritative\n  current list lives in \`pyproject.toml\` and \`uv.lock\`.`.
- `SPECIFICATION/non-functional-requirements.md` line 90-92: change `- The first useful release is \`v0.2.0\` (per the parent epic\n  \`li-6d2wpj\` plan); \`v0.1.0\` shipped the empty scaffold.` → delete this bullet entirely. Release history belongs in `CHANGELOG.md`, not in a contributor-facing invariant document.

The four Bucket-B example snippets in `contracts.md` (lines 142, 164, 172, 176, 209) are addressed by the sibling `wire-release-please-extra-files` proposal — they remain in place, with sentinel comments and release-please automation.

## Proposal: require-project-name-prefix-on-version-references

### Target specification files

- SPECIFICATION/non-functional-requirements.md

### Summary

Adopt the convention that every version reference in this spec's prose includes the owning project name as a prefix (`livespec-runtime v0.3.0`, `livespec vNNN`, `livespec-impl-plaintext v0.x`). External / third-party versions follow the same shape (`uv 0.5.x`, `gh 2.x`, `Python 3.10+`). Inline JSON/TOML example snippets where the version is the value of a typed field whose key already encodes the project name (e.g. `livespec-runtime.compat.pinned`) are exempt — the structural key already disambiguates.

### Motivation

Same /livespec:doctor pass that surfaced the version drift. The reader of a bare `v0.2.0` in a livespec-governed repo cannot tell whether it refers to the meta-tool (`livespec`), to this library (`livespec-runtime`), or to a sibling (`livespec-impl-plaintext`). Adding the project-name prefix removes that ambiguity locally. This proposal codifies the same rule that an upstream propose-change against `livespec/SPECIFICATION/` will adopt globally; this one applies it library-side.

### Proposed Changes

Add a new bullet under `SPECIFICATION/non-functional-requirements.md` §"Spec evolution" (or as a new §"Prose conventions" section near it):

```markdown
## Prose conventions

- Every version reference in spec prose MUST be prefixed with the
  owning project name. Library-local references use
  `livespec-runtime vX.Y.Z`; upstream meta-tool references use
  `livespec vNNN`; sibling impl-plugin references use the
  plugin name (`livespec-impl-plaintext v0.x`, etc.). External
  dependency versions follow the same shape (`uv 0.5.x`,
  `gh 2.x`, `Python 3.10+`).
- Inline JSON or TOML example snippets are exempt when the
  version is the value of a typed field whose key already encodes
  the project name (e.g. `livespec-runtime.compat.pinned`,
  `[tool.uv.sources].livespec-runtime`). The structural key
  carries the disambiguation; the value stays unprefixed.
```

Apply the convention to any version literal that survives the sibling `strip-narrative-version-pins-from-spec-prose` proposal.

## Proposal: wire-release-please-to-bump-consumer-example-tags

### Target specification files

- SPECIFICATION/contracts.md
- SPECIFICATION/non-functional-requirements.md

### Summary

Add `x-release-please-version` sentinel comments to the four consumer-facing example snippets in `contracts.md` (`compat.pinned` value and two `[tool.uv.sources].livespec-runtime` `tag` values) and extend `release-please-config.json` so the next release rewrites them in place. The semver-range example on line 209 (`>=0.2.0,<1.0.0`) gets the same sentinel so its lower bound floats with the release floor when intentional.

### Motivation

These four snippets are consumer copy-paste material and SHOULD reflect the current release. They're the only legitimate version literals in the spec; the right fix is automation, not manual updates. release-please supports the `generic` updater for markdown via inline sentinel comments per the release-please config schema.

### Proposed Changes

Two coupled edits:

1. Annotate the four snippet sites in `SPECIFICATION/contracts.md`:

```markdown
  "livespec-runtime": {
    "compat": {
      "livespec": ">=0.1.0,<1.0.0",
      "pinned": "v0.2.0" // x-release-please-version
    }
  }
```

and similarly at the two `tag = "v0.2.0"` sites under `[tool.uv.sources]` (lines 164 and 176), and the `"livespec-runtime>=0.2.0"` floor at line 172. Each line carries a trailing `# x-release-please-version` (TOML) or `// x-release-please-version` (JSONC) comment.

2. Document the wiring in `SPECIFICATION/non-functional-requirements.md` §"Release flow" by adding the bullet:

```markdown
- The consumer-facing example version literals in
  `SPECIFICATION/contracts.md` carry inline
  `x-release-please-version` sentinel comments. The release-please
  config (`release-please-config.json`) lists
  `SPECIFICATION/contracts.md` under `extra-files` with the `generic`
  updater so each release rewrites the example tags in place. The
  authoritative location for what the consumer copy-paste should
  pin to is therefore always the freshest commit on `master`.
```

A separate implementation-side change (not a spec change) will update `release-please-config.json` to add the `extra-files` entry; that change is filed as a freeform work-item rather than a spec proposal because the file is hand-authored tooling configuration, not part of the SPECIFICATION/ tree.

## Proposal: correct-retry-policy-description-to-1s-2s

### Target specification files

- SPECIFICATION/spec.md

### Summary

Rewrite `spec.md`'s `cross_repo.retry` public-surface bullet so it describes the policy as `3-attempt 1s/2s` instead of `3-attempt 1s/2s/4s`. The current phrasing implies three backoffs fire for three attempts; in fact only two delays fire (between attempts) and the `4.0` value in the `_BACKOFFS_SECONDS` tuple is dead code reserving room for a documented future widening. `contracts.md` §"Retry policy" already documents this correctly; `spec.md` is the outlier.

### Motivation

/livespec:doctor surfaced this as `doctor-llm-objective-contradiction-retry-policy` [severity: medium]: `spec.md:102-103` characterizes the policy as `1s/2s/4s`, but `contracts.md:113-119` clarifies `3 attempts using the first two delays only` and `livespec_runtime/cross_repo/retry.py:47-52` sleeps only on `attempt_index < _ATTEMPTS - 1` — confirming only 1.0s and 2.0s ever fire in v1.

### Proposed Changes

Edit `SPECIFICATION/spec.md` line 102-103:

```diff
-- `livespec_runtime.cross_repo.retry` — `retry_with_backoff`
-  implementing the 3-attempt 1s/2s/4s policy.
++ `livespec_runtime.cross_repo.retry` — `retry_with_backoff`
+  implementing the 3-attempt 1s/2s backoff policy (see
+  `contracts.md` §"Retry policy" for the full description,
+  including the reserved-but-unused 4.0s constant).
```

## Proposal: align-exhaustive-live-walk-definition-with-v1-surface

### Target specification files

- SPECIFICATION/spec.md

### Summary

Weaken `spec.md`'s `Exhaustive live walk` terminology entry so it no longer promises a local-clone view the library doesn't access. The current wording lists `GitHub, local clone when configured, caller-supplied lookups` as views walked per call, but `constraints.md` lines 86-89 explicitly state the v1 surface does not read local clones — the consumer wires local-clone reading via `sibling_status_lookup`. The terminology entry SHOULD match that reality.

### Motivation

/livespec:doctor surfaced this as `doctor-llm-objective-contradiction-local-clone-walk` [severity: medium]: spec.md and constraints.md disagree on whether local clones are part of the walked view set. The constraint document reflects the actual code in `livespec_runtime/cross_repo/resolve.py`; the spec.md definition is aspirational and should be revised to match.

### Proposed Changes

Edit `SPECIFICATION/spec.md` lines 73-76:

```diff
-**Exhaustive live walk** — The resolution policy this library
-implements: no cache; for each entry, walk every extant view
-(GitHub, local clone when configured, caller-supplied lookups)
-and return the first definitive `RefStatus`; degrade to `UNKNOWN`
-rather than raising. The walk is per-call, not pre-computed;
-consumers that need batching MUST batch at the call site.
+**Exhaustive live walk** — The resolution policy this library
+implements: no cache; for each entry, walk every extant view
+the library can directly access (GitHub via `gh`,
+caller-supplied lookups) and return the first definitive
+`RefStatus`; degrade to `UNKNOWN` rather than raising. Local
+clones are NOT walked by the library directly at v1; consumers
+that want a local-clone view wire it through
+`sibling_status_lookup`. The walk is per-call, not
+pre-computed; consumers that need batching MUST batch at the
+call site.
```

## Proposal: enumerate-per-variant-required-fields-on-depends-on-entry

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Add a per-variant required/optional fields enumeration to `contracts.md` §"livespec_runtime.cross_repo.types". The current text lists the four variant dataclass names and pins the `kind` discriminator's `Literal` shape, but never says which other fields are required on each variant. Readers infer the contract from `scenarios.md` (which expects `"number"` named as missing on a `pull_request`) or from `types.py`. The spec MUST state the contract directly.

### Motivation

/livespec:doctor surfaced this as `doctor-llm-objective-missing-per-variant-required-fields` [severity: low-medium]: the parser helpers' boundary contract depends on per-variant required fields, but the spec never enumerates them. Future contributors changing the dataclass shape have no specification anchor to compare against.

### Proposed Changes

Insert a new subsection under `SPECIFICATION/contracts.md` §"livespec_runtime.cross_repo.types" immediately after the bullet describing `DependsOnEntry` (current line 28):

```markdown
Per-variant required and optional fields (the `kind` field is
the discriminator on every variant, REQUIRED, and pinned to the
literal named above):

- `LocalDependency`: `work_item_id: str` (REQUIRED).
- `SiblingWorkItemDependency`: `repo: str` (REQUIRED),
  `work_item_id: str` (REQUIRED).
- `PullRequestDependency`: `repo: str` (REQUIRED), `number: int`
  (REQUIRED).
- `BranchDependency`: `repo: str` (REQUIRED), `name: str`
  (REQUIRED) — the branch name MUST be supplied without the
  `refs/heads/` prefix.

`parse_depends_on_entry` raises `CrossRepoSchemaError` when any
required field above is absent; the error's `detail` names the
specific missing field.
```

The `parse_depends_on_entry` bullet on the existing line 36-39 stays; the new subsection is what the bullet's `per-kind required field` phrase references.

## Proposal: clarify-refstatus-json-roundtrip-rule

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Rewrite the `RefStatus` JSON-round-trip rule in `contracts.md` so it names value-lookup vs name-lookup directly instead of cautioning about `casing of the member name`. The current phrasing is ambiguous: if consumers serialize `.value` (the lowercase strings), no member-name casing enters the round-trip at all — yet the rule cautions against depending on that casing without saying what consumers SHOULD do instead.

### Motivation

/livespec:doctor surfaced this as `doctor-llm-subjective-prose-quality` [severity: low]: the rule is binding but underspecified. The intent (deserialize by value-lookup, not name-lookup) is recoverable from context but not stated. Replacing with an explicit value-lookup-MUST / name-lookup-MUST-NOT clause removes the ambiguity.

### Proposed Changes

Edit `SPECIFICATION/contracts.md` lines 17-20:

```diff
-- `RefStatus` — `str`-valued Enum with members `OPEN`, `CLOSED`,
-  `UNKNOWN`. The value strings are the lowercase member names; consumers
-  MAY serialize the value but MUST NOT depend on the casing of the
-  member name when round-tripping through JSON.
+- `RefStatus` — `str`-valued Enum with members `OPEN`, `CLOSED`,
+  `UNKNOWN`. The `.value` strings are the lowercase member names
+  (`"open"`, `"closed"`, `"unknown"`). Consumers SHOULD round-trip
+  through JSON by serializing `.value` and deserializing via
+  value-lookup (`RefStatus(s)`); consumers MUST NOT deserialize
+  via name-lookup (`RefStatus[s]`), which would require uppercase
+  inputs.
```
