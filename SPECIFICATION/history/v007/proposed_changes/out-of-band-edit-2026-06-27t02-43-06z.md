---
topic: out-of-band-edit-2026-06-27t02-43-06z
author: livespec-doctor
created_at: 2026-06-27T02:43:06Z
---

## Proposal: out-of-band-edit-2026-06-27t02-43-06z

doctor detected drift between HEAD-active spec content and the
HEAD-history-vN snapshot; this auto-backfill records the active
state as the new canonical version.

### Proposed Changes

```diff
--- history/vN/contracts.md
+++ active/contracts.md
@@ -128,8 +128,7 @@
   `spec_commitment_hint: str | None = None`, `supersedes: str | None = None`.
   The two defaulted fields are OPTIONAL-on-read (legacy records lacking
   them read back as `None`) and written explicitly on append. The record
-  schema is codified upstream in `livespec/SPECIFICATION/contracts.md`
-  §"Work-items JSONL record schema".
+  schema is codified upstream in `livespec/SPECIFICATION/contracts.md`.
 - `AuditRecord` — frozen, slotted, kw-only dataclass:
   `verification_timestamp: str`, `commits: tuple[str, ...]`,
   `files_changed: tuple[str, ...]`, `merge_sha: str`,
@@ -213,8 +212,8 @@
 Every consumer MUST declare a top-level section on its `.livespec.jsonc`
 keyed by the consumer's own plugin / library name and MUST include a
 `compat` block under that section per
-`livespec/SPECIFICATION/contracts.md` §"Cross-repo coordination —
-pin-and-bump". The block shape for the `livespec-runtime` consumer slot
+`livespec/SPECIFICATION/contracts.md`. The block shape for the
+`livespec-runtime` consumer slot
 is:
 
 ```jsonc
@@ -222,7 +221,7 @@
   "livespec-runtime": {
     "compat": {
       "livespec": ">=0.1.0,<1.0.0",
-      "pinned": "v0.3.1" // x-release-please-version
+      "pinned": "v0.4.0" // x-release-please-version
     }
   }
 }
@@ -244,7 +243,7 @@
 ]
 
 [tool.uv.sources]
-livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.3.1" } # x-release-please-version
+livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.4.0" } # x-release-please-version
 ```
 
 Or as a runtime dependency:
@@ -256,7 +255,7 @@
 ]
 
 [tool.uv.sources]
-livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.3.1" } # x-release-please-version
+livespec-runtime = { git = "https://github.com/thewoolleyman/livespec-runtime.git", tag = "v0.4.0" } # x-release-please-version
 ```
 
 The tag value in `[tool.uv.sources]` MUST match the `compat.pinned`
--- history/vN/non-functional-requirements.md
+++ active/non-functional-requirements.md
@@ -43,8 +43,8 @@
 ## Task-runner discipline
 
 - `just` is the single canonical entry point for every dev-tooling
-  invocation in this repo (per upstream §"Enforcement-suite
-  invocation"). Direct invocations of `ruff`, `pyright`, `pytest`,
+  invocation in this repo (per the upstream livespec convention).
+  Direct invocations of `ruff`, `pyright`, `pytest`,
   `coverage`, or `gh` in lefthook hooks or CI YAML are FORBIDDEN; all
   such invocations MUST go through a `just <target>` indirection.
 - The `just check` target is the load-bearing aggregate. It MUST run
--- history/vN/spec.md
+++ active/spec.md
@@ -29,9 +29,9 @@
 decisions this library implements — the four-variant `DependsOnEntry`
 shape, the `cross_repo_targets` manifest schema, the resolve-ref
 semantics, retry policy, the pin-and-bump mechanism, doctor invariants
-that consume `resolve_ref` — are all FIXED upstream in
-`livespec/SPECIFICATION/contracts.md` §"Cross-repo dependency awareness"
-and §"Cross-repo coordination — pin-and-bump". This `SPECIFICATION/`
+that consume `resolve_ref` — are all FIXED upstream in `livespec`'s
+`SPECIFICATION/` (its `contracts.md` and `non-functional-requirements.md`).
+This `SPECIFICATION/`
 MUST NOT re-state `livespec`'s contract; it MUST concretize how this
 library realizes the runtime portion of that contract and point upstream
 for anything else.
@@ -45,13 +45,12 @@
 implementation manual content; the upstream doctor-invariant catalog
 that consumes `resolve_ref` (`no-orphan-dependency`,
 `no-stalled-epic`'s cross-repo extension) — those live in
-`livespec/SPECIFICATION/contracts.md` §"Doctor cross-boundary
-invariants".
+`livespec/SPECIFICATION/contracts.md`.
 
 ## Terminology
 
 This spec adopts every term defined in `livespec/SPECIFICATION/spec.md`
-§"Terminology" verbatim. The terms below are library-local additions or
+verbatim. The terms below are library-local additions or
 refinements; they extend the upstream glossary, never contradict it.
 
 **Runtime code (this library) vs enforcement-suite code
```
