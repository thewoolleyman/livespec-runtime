# Release Please and the App installation rate limit

Read this before treating a red `Release Please` run on `master` as a code
defect, or before re-running it.

## What the failure looks like

The `Release Please` workflow (`.github/workflows/release-please.yml`)
authenticates with a token minted from the livespec GitHub App installation,
not with `GITHUB_TOKEN`. When that installation exhausts its hourly API budget
the run fails with `API rate limit exceeded for installation ID 131208965`
(the `thewoolleyman-factory-bot` App). `CI` stays green in the same push, so
`master` is not broken, but no release pull request is cut and any release
owed by that merge stays unreleased.

Measured 2026-09-06: the workflow failed this way on four merges in one day
(`d5063b0`, `3932e9d`, `5adbac1`, `1c211eb`). On `3932e9d` it left 0.24.0
unreleased until a later run succeeded hours afterwards.

## Why the operator's own budget tells you nothing

The App installation's budget is separate from the operator's personal `gh`
budget. `gh api rate_limit` reporting 5000 of 5000 remaining describes the
operator's token, not the installation that failed.

## What to do

- Do not re-run inside the same hour. A re-run at 17:03Z after a 16:51Z
  failure on 2026-09-06 failed again for the same reason.
- Wait for the hourly reset and re-run, or let the next merge to `master`
  trigger a fresh run. Release Please cuts any release that is still owed, so
  the missed release is recovered either way.
- Do not file it as a code defect or treat it as a red `master`.

## Current state

As of 2026-10-18 this has not recurred: the most recent failed `Release
Please` run is the 2026-09-06 16:51Z run on `1c211eb`, and every run since
then (through 2026-10-15) succeeded. Keep this file for triage if it
recurs.
