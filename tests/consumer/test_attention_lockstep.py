"""Consumer-tier scenario test for the ratified kind-to-prefix lockstep.

Covers the kind-to-prefix lockstep scenario in
`SPECIFICATION/scenarios.md`; `tests/heading-coverage.json` carries the
authoritative heading-to-test mapping.

The DECLARED mapping in `SPECIFICATION/contracts.md` is the single source
of truth, so this test PARSES that table rather than restating it. A test
that hard-coded the pairs would drift from the spec silently, which is
the exact failure the ratified constraint exists to refuse.

Consumer-tier discipline: this reaches only the public surface —
`AttentionKind` and `validate_attention_item_id` — and asserts
consumer-visible behavior. The complementary "no accepted prefix without
a mapping row" direction needs the accepted-prefix sets themselves and so
lives in the unit tier.
"""

from pathlib import Path
from typing import get_args

from livespec_runtime.attention_item import AttentionKind, validate_attention_item_id

__all__: list[str] = []

_TABLE_MARKER = "The DECLARED kind-to-prefix mapping"
_ARITY_COMPONENTS = {"two-part": 2, "three-part": 3}


def _contracts_path() -> Path:
    return Path(__file__).resolve().parents[2] / "SPECIFICATION" / "contracts.md"


def declared_mapping() -> dict[str, tuple[str, int]]:
    """Parse the ratified kind-to-prefix table into {kind: (prefix, components)}."""
    lines = _contracts_path().read_text().splitlines()
    start = next(i for i, line in enumerate(lines) if _TABLE_MARKER in line)
    rows = (
        [cell.strip().strip("`") for cell in line.strip("|").split("|")]
        for line in lines[start:]
        if line.startswith("|")
    )
    return {
        cells[0]: (cells[1], _ARITY_COMPONENTS[cells[2]])
        for cells in rows
        if len(cells) == 3 and cells[2] in _ARITY_COMPONENTS
    }


def _id_with(*, prefix: str, components: int) -> str:
    return ":".join([prefix, *[f"c{n}" for n in range(1, components)]])


def test_declared_mapping_is_total_over_ratified_kinds() -> None:
    """Every ratified AttentionKind MUST have exactly one mapping row."""
    assert set(declared_mapping()) == set(get_args(AttentionKind))


def test_declared_mapping_is_injective_into_prefixes() -> None:
    """No two kinds may share a stable-ID prefix."""
    prefixes = [prefix for prefix, _ in declared_mapping().values()]
    assert len(prefixes) == len(set(prefixes))


def test_every_declared_prefix_validates_at_its_declared_arity() -> None:
    """Each row's prefix MUST be accepted at the arity the table declares."""
    for kind, (prefix, components) in declared_mapping().items():
        candidate = _id_with(prefix=prefix, components=components)
        assert validate_attention_item_id(id=candidate) is True, f"{kind} -> {candidate}"


def test_declared_prefixes_are_rejected_at_the_wrong_arity() -> None:
    """A row's prefix MUST NOT be accepted at an arity the table does not declare."""
    for kind, (prefix, components) in declared_mapping().items():
        other = 3 if components == 2 else 2
        candidate = _id_with(prefix=prefix, components=other)
        assert validate_attention_item_id(id=candidate) is False, f"{kind} -> {candidate}"


def test_a_prefix_absent_from_the_mapping_is_not_accepted() -> None:
    """An undeclared prefix MUST NOT validate at any arity."""
    declared = {prefix for prefix, _ in declared_mapping().values()}
    assert "workitem" not in declared
    assert validate_attention_item_id(id="workitem:abc") is False
    assert validate_attention_item_id(id="workitem:abc:def") is False


def test_kind_names_that_are_not_declared_prefixes_are_rejected() -> None:
    """A kind's own name MUST NOT validate as a prefix unless the table declares it.

    This is the converse direction of the lockstep constraint, reachable
    from the public surface: a prefix admitted in code without a ratified
    row would most plausibly be named after its kind. It also pins that
    `human-valve` was NOT admitted as a prefix — the remedy the superseded
    v012 text offered, which would have left `valve` unmatched while adding
    a prefix no producer emits.
    """
    mapping = declared_mapping()
    declared = {prefix for prefix, _ in mapping.values()}
    stray = [kind for kind in mapping if kind not in declared]

    assert "human-valve" in stray
    for kind in stray:
        for components in (2, 3):
            candidate = _id_with(prefix=kind, components=components)
            assert validate_attention_item_id(id=candidate) is False, candidate
