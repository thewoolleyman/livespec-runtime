---
topic: branch-exists-404-detection-structured-marker
author: claude-fable-5-1
created_at: 2026-09-06T11:56:22Z
---

## Proposal: branch_exists_on_remote 404 detection via gh's structured (HTTP 404) marker, not its exit code

### Target specification files

- SPECIFICATION/contracts.md

### Summary

Replace the `branch_exists_on_remote` clause that prefers `gh`'s exit code (or a structured response field) over a stderr substring match with one that names the mechanisms that actually work: `gh api`'s structured `(HTTP 404)` stderr marker line or an explicit HTTP status header (`gh api --include`), surfaced to callers as a typed field; and state that `gh`'s exit code is 1 for every API failure and MUST NOT be relied on to discriminate a 404. This ratifies the shipped `github_process.stderr_indicates_http_404` -> `GithubQueryFailed.http_404` design and closes gap `gap-nyckdcxc` / work-item `livespec-runtime-5s4ax2` as accept-as-satisfied.

### Motivation

Work-item livespec-runtime-5s4ax2 (gap-nyckdcxc) flags that the 404 in `branch_exists_on_remote` is detected via a stderr substring rather than the exit code or a structured field the spec asks for. Measured (plan runtime-backlog-drain, research/004): `gh` exits 1 for every API error so the exit code cannot discriminate a 404; the shipped discriminator matches `gh api`'s dedicated structured `(HTTP 404)` stderr line and feeds a typed `http_404: bool` field, which is the structured-field intent of the clause; a status header via `gh api --include` is obtainable but costs a parse of the response head for no gain over the marker line. The batch-1 triage ruling (ratified by the maintainer 2026-09-06) re-scoped 5s4ax2 to accept-as-satisfied via a one-clause propose-change; the maintainer authorized the drive session to file it on 2026-09-06.

### Proposed Changes

In `SPECIFICATION/contracts.md` §`livespec_runtime.cross_repo.providers.github`, under the `branch_exists_on_remote` bullet, replace the clause

> The 404 SHOULD be detected via `gh`'s exit code
> (or a structured response field), not via a substring match on
> stderr;

with

> The 404 SHOULD be detected from `gh`'s structured `(HTTP 404)`
> stderr marker line or an explicit HTTP status header (for example via
> `gh api --include`), surfaced to callers as a typed field rather than by
> callers matching stderr text themselves; `gh`'s exit code is 1 for every
> API failure and MUST NOT be relied on to discriminate a 404;

Rationale for the shape: `gh` exits 1 for every API error, so the exit code cannot discriminate a 404 from any other failure and the existing SHOULD names a mechanism that cannot satisfy it. The shipped discriminator (`github_process.stderr_indicates_http_404`) matches the structured trailing `(HTTP 404)` marker that `gh api` emits on its own dedicated stderr line and feeds the typed `GithubQueryFailed.http_404: bool` field that `branch_exists_on_remote` consumes; that is a structured field populated from `gh`'s structured line, which is what the clause was protecting callers from bare-substring collisions for. A status header via `gh api --include` remains a permitted alternative mechanism. The MUST NOT on the exit code closes the reading that produced gap `gap-nyckdcxc`.

Scenarios: no scenario change. The observable behavior (404 -> `False` on the success track; other transport failures -> `GithubFailure` on the failure track) is unchanged; only the permitted detection mechanism is restated. `tests/heading-coverage.json`: the heading keeps its existing coverage entry; no co-edit is required.

Disposition of the tied work: on ratification, `livespec-runtime-5s4ax2` (gap `gap-nyckdcxc`) closes as accept-as-satisfied naming the revision, per the batch-1 ruling on plan `runtime-backlog-drain` (research/003 §4). No impl follow-up is owed.
