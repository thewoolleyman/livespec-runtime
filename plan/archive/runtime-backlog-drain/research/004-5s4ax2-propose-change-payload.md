# 004 — Prepared propose-change payload for `livespec-runtime-5s4ax2` (gap `gap-nyckdcxc`)

Prepared 2026-09-06 by the drive session under the batch-1 ruling (research/003
§4, scope event on `livespec-runtime-c7toen`). Per AGENTS.md this session does
NOT materialize `SPECIFICATION/proposed_changes/`; the maintainer runs the
spec lane with the payload below. On ratification the gap and the item close.

## Finding

`SPECIFICATION/contracts.md` lines 100–103 say the 404 in
`branch_exists_on_remote` "SHOULD be detected via `gh`'s exit code (or a
structured response field), not via a substring match on stderr". Measured:

- `gh` exits 1 for every API error, so the exit code cannot discriminate a 404
  from any other failure.
- The shipped discriminator (`github_process.py:168`,
  `stderr_indicates_http_404`) matches the structured trailing `(HTTP 404)`
  marker that `gh api` emits on its own dedicated stderr line, and feeds a
  typed `GithubQueryFailed.http_404: bool` field that
  `branch_exists_on_remote` consumes. That is a structured field populated
  from `gh`'s structured line, which is what the SHOULD was protecting
  against bare-substring collisions for.
- A status header is obtainable with `gh api --include`, so an alternative
  mechanism exists; it costs a parse of the response head for no gain over
  the marker line.

## Proposed delta (one clause)

Replace, in `contracts.md` under `branch_exists_on_remote`:

> The 404 SHOULD be detected via `gh`'s exit code (or a structured response
> field), not via a substring match on stderr;

with:

> The 404 SHOULD be detected from `gh`'s structured `(HTTP 404)` stderr
> marker line or an explicit HTTP status header (for example via
> `gh api --include`), surfaced to callers as a typed field rather than by
> callers matching stderr text themselves; `gh`'s exit code is 1 for every
> API failure and MUST NOT be relied on to discriminate a 404;

Scenarios and heading coverage: no scenario change; the heading keeps its
existing coverage entry.

## Handoff for the maintainer

```
/livespec:propose-change branch-exists-404-detection-structured-marker
```

with the delta above as the body, then `/livespec:revise --only-topic
branch-exists-404-detection-structured-marker`. After ratification the drive
session closes `livespec-runtime-5s4ax2` naming the revision, which closes
`gap-nyckdcxc`.
