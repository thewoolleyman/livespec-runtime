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

from returns.result import Failure, Success

from livespec_runtime.spec_stated import (
    SpecStatedParseError,
    SpecStatedVerdict,
    parse_verdict,
)

__all__: list[str] = []

_HEADINGS = ("## Widgets", "## Gadgets")
_RATIONALE = "the Widgets clause states that a widget is blue"


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
