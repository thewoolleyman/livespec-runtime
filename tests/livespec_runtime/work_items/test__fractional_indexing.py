"""Round-trip / validation tests for the verbatim-ported `_fractional_indexing`.

The module is vendored VERBATIM (CC0-1.0) and coverage-omitted; the
first-party `rank.py` wrapper is the livespec-facing surface and is
covered to 100% by `test_rank.py`. This file pins the ported module's
own ordering + validation contract DIRECTLY — in particular
`validate_order_key`, which the wrapper does not re-export — so the
port's behavior stays locked independently of the wrapper (a drift guard
on the one file that may not take a reformat without ceasing to be
verbatim).
"""

import pytest

from livespec_runtime.work_items._fractional_indexing import (
    FIError,
    generate_key_between,
    generate_n_keys_between,
    validate_order_key,
)

__all__: list[str] = []


def test_generated_keys_validate_as_order_keys() -> None:
    first = generate_key_between(None, None)
    # validate_order_key raises ValueError on an invalid key; a freshly
    # generated key MUST validate.
    validate_order_key(first)
    nxt = generate_key_between(first, None)
    validate_order_key(nxt)


def test_generate_key_between_is_strictly_between_neighbors() -> None:
    a = generate_key_between(None, None)
    b = generate_key_between(a, None)
    mid = generate_key_between(a, b)
    assert a < mid < b
    for key in (a, b, mid):
        validate_order_key(key)


def test_generate_n_keys_between_round_trips_sorted_unique_and_valid() -> None:
    keys = generate_n_keys_between(None, None, 5)
    assert len(keys) == 5
    assert keys == sorted(keys)
    assert len(set(keys)) == 5
    for key in keys:
        validate_order_key(key)


def test_validate_order_key_rejects_the_bottom_sentinel() -> None:
    # "~" (0x7E) is OUTSIDE the base-62 alphabet, so the rank bottom
    # sentinel is NOT a valid order key — it only ever sorts last, it is
    # never generated or validated as a real rank. The ported module's
    # invalid-head guard raises its own `FIError`.
    with pytest.raises(FIError):
        validate_order_key("~")


def test_validate_order_key_rejects_trailing_zero_fraction() -> None:
    # A fractional part ending in the zero digit is non-canonical (the
    # generator never emits one), so the validator rejects it.
    with pytest.raises(FIError):
        validate_order_key("a00")
