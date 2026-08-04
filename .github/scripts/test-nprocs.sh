#!/usr/bin/env bash
set -euo pipefail

if [[ "${LIVESPEC_CI_LANE:-local}" == "hosted" ]]; then
    printf '%s\n' auto
    exit
fi

if [[ -n "${LIVESPEC_TEST_PARALLELISM:-}" ]]; then
    printf '%s\n' "$LIVESPEC_TEST_PARALLELISM"
    exit
fi

cores="$(nproc 2>/dev/null || echo 4)"
nprocs=$((cores / 4))
if [[ "$nprocs" -lt 1 ]]; then
    nprocs=1
fi
printf '%s\n' "$nprocs"
