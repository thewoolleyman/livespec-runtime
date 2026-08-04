#!/usr/bin/env bash
set -euo pipefail

nprocs="$("$(dirname "$0")/test-nprocs.sh")"
uv run pytest -n "$nprocs" --cov --cov-branch --cov-config=pyproject.toml --cov-report=term-missing
uv run python -m livespec_dev_tooling.checks.per_file_coverage
