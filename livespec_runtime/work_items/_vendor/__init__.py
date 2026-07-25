# ruff: noqa
"""Vendored third-party code carried inside `livespec_runtime`.

Package marker for the `_vendor/` subtree — the fleet's universally-excluded
vendoring home. Files under any `_vendor/` path are excluded from this repo's
first-party lint / type / coverage / structural gates (see the root
`pyproject.toml`; the shared `livespec_dev_tooling.config.iter_py_files` and
`filter_first_party_py` both skip `_vendor` path segments). The single
verbatim CC0 port `_fractional_indexing.py` lives here; import it only through
the keyword-only wrapper `livespec_runtime.work_items.rank`. See the repo-root
`NOTICES` file for the attribution entry.
"""
