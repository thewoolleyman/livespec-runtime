"""Consumer-tier scenario tests for the ratified stable-ID grammar.

Covers the two `validate_attention_item_id` grammar scenarios in
`SPECIFICATION/scenarios.md`; `tests/heading-coverage.json` carries the
authoritative heading-to-test mapping.

These pin the grammar's PURPOSE, not merely its arity: an attention item's
id is a stable natural key, so a component that is a positional index is
refused however well-formed the id's shape is. The sibling
`test_attention_lockstep.py` covers the kind-to-prefix correspondence and
each prefix's declared arity; this file covers the per-component rules
that hold regardless of which prefix is in play.

Consumer-tier discipline: this reaches only the public surface --
`validate_attention_item_id` -- and asserts on its consumer-visible
return value.
"""

from livespec_runtime.attention_item import validate_attention_item_id

__all__: list[str] = []


def test_rejects_an_id_whose_component_is_purely_decimal() -> None:
    """Scenario: `impl:42` MUST be false -- a positional index is not a key.

    The id is otherwise well-formed: `impl` is a declared two-part prefix
    and the component is non-empty. It is refused solely because a purely
    decimal component names a POSITION, which is not stable across
    reordering, rather than an identity.
    """
    assert validate_attention_item_id(id="impl:42") is False


def test_accepts_a_well_formed_three_part_hygiene_id() -> None:
    """Scenario: `hygiene:stale-worktree:my-repo` MUST be true."""
    assert validate_attention_item_id(id="hygiene:stale-worktree:my-repo") is True


def test_the_decimal_rule_applies_to_every_component_after_the_prefix() -> None:
    """The ratified rule binds EVERY component, not just the last one.

    Pinned because the single-component scenario above is satisfiable by
    an implementation that only inspects the final component, which would
    admit a positional class segment in a three-part id.
    """
    assert validate_attention_item_id(id="hygiene:7:my-repo") is False
    assert validate_attention_item_id(id="hygiene:stale-worktree:7") is False
    assert validate_attention_item_id(id="hygiene:7:7") is False


def test_a_component_that_merely_contains_digits_is_still_accepted() -> None:
    """Only a PURELY decimal component is refused, not any digit-bearing one.

    The negative control for the rule above: a rule implemented as
    "contains a digit" rather than "is purely decimal" would reject the
    work-item ids this library's own consumers actually emit.
    """
    assert validate_attention_item_id(id="impl:li-abc123") is True
    assert validate_attention_item_id(id="hygiene:stale-worktree:repo-2") is True


def test_an_empty_component_after_the_prefix_is_rejected() -> None:
    """The ratified rule requires every post-prefix component to be non-empty."""
    assert validate_attention_item_id(id="impl:") is False
    assert validate_attention_item_id(id="hygiene::my-repo") is False
    assert validate_attention_item_id(id="hygiene:stale-worktree:") is False
