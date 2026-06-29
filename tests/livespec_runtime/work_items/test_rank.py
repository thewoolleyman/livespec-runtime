"""Tests for the fractional-index `rank` wrapper (`livespec_runtime.work_items.rank`).

Exercises the thin livespec-facing wrapper (`key_between`, `n_keys_between`,
`BOTTOM_SENTINEL`) — and, through it, smoke-tests that the ported
`_fractional_indexing` algorithm produces the canonical base-62 keys
(`a0`, `a1`, `Zz`, evenly-spaced midpoints). The exhaustive behavioral
suite for the ported module proper rides under the coverage-omitted
verbatim port; this file covers the first-party wrapper to 100%.
"""

from livespec_runtime.work_items.rank import BOTTOM_SENTINEL, key_between, n_keys_between


def test_key_between_empty_range_returns_first_key() -> None:
    assert key_between(a=None, b=None) == "a0"


def test_key_between_after_returns_next_key() -> None:
    first = key_between(a=None, b=None)
    assert key_between(a=first, b=None) == "a1"


def test_key_between_before_first_returns_prior_key() -> None:
    first = key_between(a=None, b=None)
    assert key_between(a=None, b=first) == "Zz"


def test_key_between_midpoint_is_strictly_between_neighbors() -> None:
    a = key_between(a=None, b=None)
    b = key_between(a=a, b=None)
    mid = key_between(a=a, b=b)
    assert a < mid < b


def test_n_keys_between_returns_n_evenly_spaced_sorted_keys() -> None:
    keys = n_keys_between(a=None, b=None, n=3)
    assert keys == ["a0", "a1", "a2"]
    assert keys == sorted(keys)


def test_n_keys_between_zero_returns_empty_list() -> None:
    assert n_keys_between(a=None, b=None, n=0) == []


def test_bottom_sentinel_sorts_strictly_after_every_real_key() -> None:
    # "~" (0x7E) is OUTSIDE the base-62 alphabet (0-9A-Za-z, max 'z' 0x7A),
    # so a legacy rank-less line read as the sentinel sorts strictly last.
    assert BOTTOM_SENTINEL == "~"
    assert key_between(a=None, b=None) < BOTTOM_SENTINEL
    assert BOTTOM_SENTINEL > "zzzzzzzzzzzz"
