#!/usr/bin/env bash
set -euo pipefail

nprocs="$("$(dirname "$0")/test-nprocs.sh")"
# Clean-env producer (livespec-dev-tooling-yilyxr.8, dev-tooling PR #1462
# design): COVERAGE_FILE unset so the repo-root .coverage exists for
# check-coverage's consume-once reuse even under the dispatcher's
# namespaced export, and measures identically to a clean CI job.
env -u COVERAGE_FILE uv run pytest -n "$nprocs" --cov --cov-branch --cov-config=pyproject.toml --cov-report=term-missing
env -u COVERAGE_FILE uv run python -m livespec_dev_tooling.checks.per_file_coverage
