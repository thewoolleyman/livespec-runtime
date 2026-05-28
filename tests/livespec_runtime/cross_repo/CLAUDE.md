# tests/livespec_runtime/cross_repo/

Mirrors `livespec_runtime/cross_repo/` one-to-one. One test module
per source module under `livespec_runtime/cross_repo/`, plus a
`providers/` subdirectory mirroring the providers subpackage.
Provider tests (`providers/test_github.py`) shell out to `gh`/`git`
subprocesses through documented contract surfaces.
