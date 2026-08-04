#!/usr/bin/env bash
set -euo pipefail

base_ref="master"
if ! git rev-parse --verify --quiet "$base_ref" >/dev/null; then
    base_ref="origin/master"
fi

if ! git diff --quiet "$base_ref"...HEAD -- .github/workflows/; then
    echo "ERROR: factory branch modifies .github/workflows/:" >&2
    git diff --name-status "$base_ref"...HEAD -- .github/workflows/ >&2
    exit 1
fi
