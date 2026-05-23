"""Smoke test — the v0.1.0 skeleton imports cleanly."""

import livespec_runtime
import livespec_runtime.cross_repo


def test_top_level_package_imports() -> None:
    assert livespec_runtime.__all__ == []


def test_cross_repo_subpackage_imports() -> None:
    assert livespec_runtime.cross_repo.__all__ == []
