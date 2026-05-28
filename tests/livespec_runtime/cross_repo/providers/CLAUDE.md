# tests/livespec_runtime/cross_repo/providers/

Mirrors `livespec_runtime/cross_repo/providers/` one-to-one. One
test module per provider implementation under
`livespec_runtime/cross_repo/providers/` (e.g., `test_github.py`
for `github.py`). Provider tests cover the documented contract
surface — branch-existence detection, PR-state derivation, and
graceful degradation under `gh` / network failure modes.
