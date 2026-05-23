"""Per-forge providers for cross-repo state queries.

v1 ships `github` exclusively. The `providers` package shape is
structured so adding a sibling module (e.g., `gitlab`) is a non-breaking
extension per livespec/SPECIFICATION/contracts.md §"Cross-repo
dependency awareness" → "Scope and non-goals".
"""

__all__: list[str] = []
