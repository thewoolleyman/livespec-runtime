"""The shared spec-stated judgement, driven through the library's public surface.

Binds the three `SPECIFICATION/scenarios.md` scenarios ratified as v027 by
proposal `spec-stated-judgement`; `tests/heading-coverage.json` carries the
heading-to-test mapping. The consumer here is an orchestrator holding a spec
tree, a behaviour statement and a model it reaches itself: it hands the model
in as `run_model` and reads consumer-visible return values — a `Success`
carrying a `SpecStatedVerdict` or an `ItemClass`, or a `Failure` carrying a
`SpecStatedParseError` whose `field` names what it could not read.

No model is reached: `run_model` is a stub the test supplies, which is the
whole point of the injection — the library carries no provider binding, so
there is nothing to patch out.
"""

import json
import socket
import subprocess

from returns.result import Failure, Success

from livespec_runtime.spec_stated import (
    SpecStatedParseError,
    SpecStatedVerdict,
    classify,
    judge,
    parse_verdict,
)

__all__: list[str] = []

_HEADINGS = ("## Widgets", "## Gadgets")
_ITEM_CLASSES = ("feature", "bug", "chore", "non_functional")
_RATIONALE = "the Widgets clause states that a widget is blue"
_SPEC_TREE = {
    "SPECIFICATION/contracts.md": (
        "# Contracts\n\n## Widgets\n\nA widget MUST be blue.\n\n"
        "### Widget colour\n\nBlue is the only colour.\n\n"
        "## Gadgets\n\nA gadget MUST be round.\n"
    )
}


class _Runner:
    """A `ModelRunner` stub that records every prompt it is handed.

    `ModelRunner` is `Callable[[str], str]`, so the prompt arrives
    POSITIONALLY; a `__call__` carries that externally-fixed convention.
    """

    def __init__(self, *, responses: list[str]) -> None:
        self.responses = responses
        self.prompts: list[str] = []

    def __call__(self, prompt: str) -> str:
        self.prompts.append(prompt)
        return self.responses[len(self.prompts) - 1]


class _Spawned:
    """A stand-in for a process or socket constructor that records every attempt."""

    def __init__(self) -> None:
        self.attempts: list[str] = []

    def __call__(self, *args: object, **kwargs: object) -> object:
        self.attempts.append(f"{args!r} {kwargs!r}")
        return self


def _response(**fields: object) -> str:
    """One model response, rendered as the JSON object the prompt asks for."""
    return json.dumps(
        {
            "kind": "stated",
            "stated_by": ["## Widgets"],
            "generalization_target": None,
            "rationale": _RATIONALE,
            **fields,
        }
    )


def _without(*, field: str) -> str:
    """One model response with `field` omitted entirely."""
    parsed: dict[str, object] = json.loads(_response())
    del parsed[field]
    return json.dumps(parsed)


def _refusal(*, response: str) -> SpecStatedParseError:
    """The `SpecStatedParseError` a refused response rides back on."""
    result = parse_verdict(text=response, headings=_HEADINGS)
    assert isinstance(result, Failure), f"expected a Failure for {response!r}, got {result}"
    return result.failure()


def test_the_spec_stated_judgement_names_the_governing_heading_the_generalization_target_or_neither(
    monkeypatch,
) -> None:
    """Witness the scenario, including the `unstated` case its heading promises.

    The governing heading set is the tree's own: a response naming a heading
    the tree does not carry is refused, which is what shows `judge` deriving
    the set from `spec_tree` rather than trusting the model. `### Widget
    colour` is in the tree so the derivation is seen to take H2 headings only.

    The two spawn constructors are replaced by recorders rather than merely
    left alone, so the scenario's no-subprocess-no-socket line is a
    MEASUREMENT here and not an absence of evidence. The recorder is fired
    once first and then cleared: an instrument that cannot record cannot
    witness that nothing was recorded.
    """
    spawned = _Spawned()
    monkeypatch.setattr(subprocess, "Popen", spawned)
    monkeypatch.setattr(socket, "socket", spawned)
    assert socket.socket() is spawned
    assert len(spawned.attempts) == 1
    spawned.attempts.clear()
    stated_by_widgets = _Runner(responses=[_response()])
    partially = _Runner(responses=[_response(kind="partial", generalization_target="## Widgets")])
    unstated = _Runner(responses=[_response(kind="unstated", stated_by=[])])
    invented = _Runner(responses=[_response(stated_by=["## Sprockets"])])
    runners = (stated_by_widgets, partially, unstated, invented)

    stated = judge(spec_tree=_SPEC_TREE, statement="a widget is blue", run_model=stated_by_widgets)
    partial = judge(
        spec_tree=_SPEC_TREE, statement="a widget is blue and square", run_model=partially
    )
    neither = judge(spec_tree=_SPEC_TREE, statement="a widget hums", run_model=unstated)
    refused = judge(spec_tree=_SPEC_TREE, statement="a widget is blue", run_model=invented)

    assert stated == Success(
        SpecStatedVerdict(
            kind="stated",
            stated_by=("## Widgets",),
            generalization_target=None,
            rationale=_RATIONALE,
        )
    )
    assert partial == Success(
        SpecStatedVerdict(
            kind="partial",
            stated_by=("## Widgets",),
            generalization_target="## Widgets",
            rationale=_RATIONALE,
        )
    )
    assert neither == Success(
        SpecStatedVerdict(
            kind="unstated",
            stated_by=(),
            generalization_target=None,
            rationale=_RATIONALE,
        )
    )
    assert isinstance(refused, Failure)
    assert refused.failure().field == "stated_by"
    assert [len(runner.prompts) for runner in runners] == [1, 1, 1, 1]
    assert spawned.attempts == []
    assert "## Widgets" in stated_by_widgets.prompts[0]
    assert "A widget MUST be blue." in stated_by_widgets.prompts[0]
    assert "a widget is blue" in stated_by_widgets.prompts[0]


def test_classify_treats_the_stored_type_as_evidence_not_as_the_answer() -> None:
    """Witness the scenario, and that the stored type reaches the model as evidence.

    The scenario's own Given/Then — a `task`-typed item whose description asks
    for new observable behaviour and a stub returning `feature` — cannot fail
    for an implementation that drops `item_type` from the prompt entirely,
    because `task` is not an `ItemClass` and so never collides with the answer.
    So the stored type is also asserted to BE in the prompt the stub was
    handed: that is the half of "MUST be passed to the model as evidence" the
    scenario leaves unexercised.

    Evidence-not-answer is measured in the direction that can actually fail:
    an item stored as `bug` whose model answer is `chore` classifies as
    `chore`, so a stored type that IS a member of the vocabulary is still not
    returned unexamined. All four members and the out-of-vocabulary refusal
    are driven too, so the `Failure` track of `classify` is witnessed rather
    than assumed.
    """
    stored_task = _Runner(responses=["feature"])
    stored_bug = _Runner(responses=["chore"])
    members = {member: _Runner(responses=[member]) for member in _ITEM_CLASSES}
    unrecognized = _Runner(responses=["enhancement"])

    classified = classify(
        title="widgets report their colour",
        description="a widget MUST expose the colour it is, which nothing does today",
        item_type="task",
        run_model=stored_task,
    )
    disagreed = classify(
        title="rename the widget module",
        description="no observable behaviour changes",
        item_type="bug",
        run_model=stored_bug,
    )
    answered = {
        member: classify(
            title="widgets report their colour",
            description="a widget MUST expose the colour it is",
            item_type="task",
            run_model=runner,
        )
        for member, runner in members.items()
    }
    refused = classify(
        title="widgets report their colour",
        description="a widget MUST expose the colour it is",
        item_type="task",
        run_model=unrecognized,
    )

    assert classified == Success("feature")
    assert disagreed == Success("chore")
    assert answered == {member: Success(member) for member in _ITEM_CLASSES}
    assert isinstance(refused, Failure)
    assert refused.failure().field is None
    assert refused.failure().detail != ""
    assert "task" in stored_task.prompts[0]
    assert "bug" in stored_bug.prompts[0]
    assert "widgets report their colour" in stored_task.prompts[0]
    assert len(stored_task.prompts) == 1
    assert [len(runner.prompts) for runner in members.values()] == [1, 1, 1, 1]


def test_parse_verdict_returns_the_typed_verdict_for_a_well_formed_response() -> None:
    """A well-formed response yields the verdict, with every field typed.

    The `## ` marker is part of the heading text the model copies out of the
    tree, so `stated_by` carries it verbatim rather than a stripped title.
    """
    stated = parse_verdict(text=_response(), headings=_HEADINGS)
    partial = parse_verdict(
        text=_response(kind="partial", generalization_target="## Widgets"),
        headings=_HEADINGS,
    )
    unstated = parse_verdict(text=_response(kind="unstated", stated_by=[]), headings=_HEADINGS)

    assert stated == Success(
        SpecStatedVerdict(
            kind="stated",
            stated_by=("## Widgets",),
            generalization_target=None,
            rationale=_RATIONALE,
        )
    )
    assert partial == Success(
        SpecStatedVerdict(
            kind="partial",
            stated_by=("## Widgets",),
            generalization_target="## Widgets",
            rationale=_RATIONALE,
        )
    )
    assert unstated == Success(
        SpecStatedVerdict(
            kind="unstated",
            stated_by=(),
            generalization_target=None,
            rationale=_RATIONALE,
        )
    )


def test_parse_verdict_names_the_offending_field_or_the_parse_error() -> None:
    """Witness the scenario: the refusal names the field, or names the parse error.

    Every refusal route is walked, because a parser that names the first field
    it can and `None` for the rest would satisfy the scenario's three lines
    while leaving a consumer unable to report what went wrong.
    """
    missing_kind = _refusal(response=_without(field="kind"))
    missing_rationale = _refusal(response=_without(field="rationale"))
    not_json = _refusal(response="I think the Widgets clause covers it.")
    not_an_object = _refusal(response=json.dumps(["## Widgets"]))
    absent_heading = _refusal(response=_response(stated_by=["## Sprockets"]))
    ill_typed_kind = _refusal(response=_response(kind="maybe"))
    ill_typed_stated_by = _refusal(response=_response(stated_by="## Widgets"))
    ill_typed_heading = _refusal(response=_response(stated_by=["## Widgets", 7]))
    ill_typed_target = _refusal(response=_response(generalization_target=7))
    ill_typed_rationale = _refusal(response=_response(rationale=None))

    assert missing_kind.field == "kind"
    assert missing_rationale.field == "rationale"
    assert not_json.field is None
    assert not_json.detail != ""
    assert not_an_object.field is None
    assert not_an_object.detail != ""
    assert absent_heading.field == "stated_by"
    assert ill_typed_kind.field == "kind"
    assert ill_typed_stated_by.field == "stated_by"
    assert ill_typed_heading.field == "stated_by"
    assert ill_typed_target.field == "generalization_target"
    assert ill_typed_rationale.field == "rationale"
