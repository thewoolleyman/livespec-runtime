"""Tests for `livespec_runtime.needs_attention`."""

from livespec_runtime.needs_attention import (
    HygieneScanFinding,
    ImplNextOutput,
    PlanThreadOutput,
    SpecNextOutput,
    WorkItemHumanValveLane,
    compose_needs_attention,
)

__all__: list[str] = []


def test_compose_needs_attention_normalizes_primitives_to_attention_list() -> None:
    attention = compose_needs_attention(
        repo="livespec-runtime",
        spec_next=SpecNextOutput(
            op="next",
            spec_target="SPECIFICATION/contracts.md",
            summary="Spec has a pending operation.",
            command="codex exec livespec:next",
        ),
        impl_next=ImplNextOutput(
            work_item="li-impl01",
            summary="Implement the next ready work item.",
            command="codex exec livespec:impl-next",
        ),
        human_valve_lanes=(
            WorkItemHumanValveLane(
                verb="approve",
                work_item="li-valve1",
                summary="Approve pending work.",
                action_id="approve",
                command="bd update li-valve1 --status ready",
            ),
        ),
        plan_threads=(
            PlanThreadOutput(
                topic="needs-attention",
                path="plan/needs-attention/research/design.md",
                summary="Resolve the plan thread.",
                command="codex exec livespec-orchestrator-beads-fabro:orchestrate",
            ),
        ),
        hygiene_scan=(
            HygieneScanFinding(
                type="stale-branch",
                resource="refs/heads/old",
                path=".git/refs/heads/old",
                summary="Delete stale branch.",
                command="git branch -d old",
            ),
        ),
    )

    assert [item.id for item in attention] == [
        "valve:approve:li-valve1",
        "impl:li-impl01",
        "spec:next:SPECIFICATION/contracts.md",
        "plan:needs-attention",
        "hygiene:stale-branch:refs/heads/old",
    ]
    assert [item.kind for item in attention] == [
        "human-valve",
        "impl",
        "spec",
        "plan",
        "hygiene",
    ]
    assert [item.urgency for item in attention] == [
        "high",
        "high",
        "medium",
        "medium",
        "low",
    ]


def test_compose_needs_attention_is_stateless_point_in_time() -> None:
    first = compose_needs_attention(
        repo="runtime",
        impl_next=ImplNextOutput(
            work_item="li-one",
            summary="One",
            command="drive li-one",
        ),
    )
    second = compose_needs_attention(
        repo="runtime",
        impl_next=ImplNextOutput(
            work_item="li-one",
            summary="One",
            command="drive li-one",
        ),
    )

    assert first == second
    assert not hasattr(first[0], "captured_at")
    assert not hasattr(first[0], "history")


def test_compose_needs_attention_drops_invalid_natural_keys() -> None:
    attention = compose_needs_attention(
        repo="runtime",
        impl_next=ImplNextOutput(
            work_item="0",
            summary="Index-like ids are not stable natural keys.",
            command="drive 0",
        ),
        plan_threads=(
            PlanThreadOutput(
                topic="durable-topic",
                path="plan/thread.md",
                summary="Keep the durable plan topic.",
                command="open plan/thread.md",
            ),
        ),
    )

    assert [item.id for item in attention] == ["plan:durable-topic"]
    assert [item.source_ref.path for item in attention] == ["plan/thread.md"]
    assert [item.handoff.command for item in attention] == ["open plan/thread.md"]
