"""Consumer-tier scenario test for composition refusing an invalid candidate.

Covers the composition-refusal scenario in `SPECIFICATION/scenarios.md`;
`tests/heading-coverage.json` carries the authoritative heading-to-test
mapping.

This is the producer-side NEGATIVE CONTROL. The constraint it pins exists
because a silently shortened list is indistinguishable from a quiet repo,
so a dropped candidate manufactures a false all-clear rather than an
error. Asserting only that the invalid candidate is absent would pass
against the very silent-drop behaviour this closes, so every test here
asserts on the REFUSAL and on the valid candidate NOT being returned
alone.

Consumer-tier discipline: this reaches only the public surface --
`compose_needs_attention`, its injected primitive-output types, and the
error TYPE -- and drives a consumer-shaped workflow, asserting on
consumer-visible behaviour rather than on internal shape.
"""

import pytest

from livespec_runtime.attention_item import InvalidAttentionItemIdError
from livespec_runtime.needs_attention import (
    ImplNextOutput,
    PlanThreadOutput,
    compose_needs_attention,
)

__all__: list[str] = []


def _valid_thread() -> PlanThreadOutput:
    return PlanThreadOutput(
        topic="durable-topic",
        path="plan/thread.md",
        summary="Keep the durable plan topic.",
        command="open plan/thread.md",
    )


def _positional_impl() -> ImplNextOutput:
    """An id-bearing candidate whose work-item is a positional index, not a key."""
    return ImplNextOutput(
        work_item="0",
        summary="Index-like ids are not stable natural keys.",
        command="drive 0",
    )


def test_composition_refuses_a_workflow_carrying_an_invalid_candidate() -> None:
    """A consumer composing a real attention list gets a refusal, not a short list."""
    with pytest.raises(InvalidAttentionItemIdError) as excinfo:
        _ = compose_needs_attention(
            repo="runtime",
            impl_next=_positional_impl(),
            plan_threads=(_valid_thread(),),
        )

    assert "impl:0" in str(excinfo.value)


def test_the_valid_candidate_is_never_returned_alone() -> None:
    """The negative control: one invalid plus one valid MUST NOT yield one item.

    Under the retired silent-drop behaviour this workflow returned a
    one-element list naming only the plan thread, which a consumer could
    not distinguish from a repo where nothing else needed attention.
    """
    with pytest.raises(InvalidAttentionItemIdError):
        _ = compose_needs_attention(
            repo="runtime",
            impl_next=_positional_impl(),
            plan_threads=(_valid_thread(),),
        )


def test_a_wholly_valid_workflow_still_composes() -> None:
    """Refusal MUST be reserved for invalid ids; valid input still returns a list."""
    attention = compose_needs_attention(
        repo="runtime",
        impl_next=ImplNextOutput(
            work_item="li-abc123",
            summary="A stable natural key.",
            command="drive li-abc123",
        ),
        plan_threads=(_valid_thread(),),
    )

    assert [item.id for item in attention] == ["impl:li-abc123", "plan:durable-topic"]


def test_the_error_type_is_catchable_by_name_not_by_a_builtin_ancestor() -> None:
    """v015 requires consumers to catch this library's errors by name.

    Pinned at the consumer tier because it is a consumer-visible property
    of the public surface: a consumer guarding this workflow with an
    `except ValueError` would NOT catch the refusal.
    """
    with pytest.raises(InvalidAttentionItemIdError) as excinfo:
        _ = compose_needs_attention(repo="runtime", impl_next=_positional_impl())

    assert not isinstance(excinfo.value, ValueError)
