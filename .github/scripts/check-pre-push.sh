#!/usr/bin/env bash
set -euo pipefail

# Release gate. Runs BEFORE the green-token early exit, because that exit
# answers "does this push need the check aggregate?" while this answers a
# different question: does the semver classification the commits since the last
# release tag declare still cover the public-surface delta? A green token means
# the tree is byte-identical to the last green aggregate; it says nothing about
# the tag-relative surface delta, so skipping the gate on that basis would skip
# exactly the pushes closest to a release.
#
# Per livespec-dev-tooling SPECIFICATION/contracts.md §"`release_bump_classification`
# check", this is a release-workflow check with no mandated caller — wiring it
# here is this repository's own opt-in adoption.
#
# HONEST LIMIT: pre-push gates DEVELOPER pushes, not CI. A merge landing through
# any path that does not run this hook is not covered. An airtight CI gate is a
# separate decision, now takeable with the check written and proven.
echo ":: pre-push: release-bump classification gate"
uv run python -m livespec_dev_tooling.workflow_checks.release_bump_classification

# The zero-.py doc-only subset was RETIRED (plan pr-gate-master-parity R3):
# pre-push now runs the FULL `just check` aggregate for every push regardless of
# whether the changeset touches `.py`, so a developer push is gated by the same
# aggregate CI runs — PR gate ≡ master gate. The green-token clean-tree
# memoization stays: it short-circuits ONLY when the working tree is
# byte-identical to the last green aggregate, which is a correctness-preserving
# skip (nothing changed), not a change-detection subset.
if uv run python -m livespec_dev_tooling.green_token check 2>&1; then
    echo ":: pre-push: green token matched - tree byte-identical to last green check; skipping full aggregate (CI is authoritative)"
    exit 0
fi

just check
