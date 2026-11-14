"""The stand-ins in `_standins` behave exactly like Core's classes, so dropping them for Core's is a pure delete.

On a Core that has a class, the stand-in is compared with it; on an older Core that part is skipped.
"""

import importlib

import pytest
from heinzel_acme_connectors import _standins
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def core(name: str, module: str = "heinzel"):
    try:
        found = getattr(importlib.import_module(module), name, None)
    except ImportError:
        found = None
    if found is None:
        pytest.skip(f"this Core has no {module}.{name}")
    return found


def fields(model) -> dict[str, object]:
    """A model's fields with their types, defaults and constraints, without the descriptions."""
    schema = model.model_json_schema()
    for prop in schema.get("properties", {}).values():
        prop.pop("description", None)
        prop.pop("title", None)
    return {"properties": schema.get("properties"), "required": schema.get("required", [])}


@pytest.mark.parametrize("name", ["ModelOffer", "SelfMessage", "SelfAnswer", "DocumentHit"])
def test_models_have_cores_fields_types_and_constraints(name):
    assert fields(getattr(_standins, name)) == fields(core(name))
    assert getattr(_standins, name).model_config.get("frozen") == core(name).model_config.get("frozen")


@pytest.mark.parametrize(
    ("name", "arguments"),
    [
        ("NotSupportedError", ("mail", "send_draft", "no send tool")),
        ("NotSupportedError", ("mail", "send_draft")),
        ("ModelUnavailableError", ("acme/huge", ["acme/fast", "acme/deep", "acme/x"], "gone")),
        ("ModelUnavailableError", ("acme/huge", None, "")),
    ],
)
def test_errors_say_what_cores_say(name, arguments):
    assert str(getattr(_standins, name)(*arguments)) == str(core(name)(*arguments))


def test_self_answer_refuses_what_core_refuses():
    for answer in (_standins.SelfAnswer, core("SelfAnswer")):
        with pytest.raises(ValidationError):
            answer(timed_out=True, text="x")
        with pytest.raises(ValidationError):
            answer()


@pytest.mark.parametrize("name", ["INLINE_UNTRUSTED", "ENVELOPE_UNTRUSTED"])
def test_markers_are_cores(name):
    mine, theirs = getattr(_standins, name), core(name, "heinzel.connectors.mcp")
    assert (mine.start, mine.end, mine.stray, mine.unique) == (theirs.start, theirs.end, theirs.stray, theirs.unique)


def test_the_unmarker_reads_markers_as_core_does():
    unmark = core("unmark", "heinzel.connectors.mcp")
    markers = (_standins.INLINE_UNTRUSTED, _standins.ENVELOPE_UNTRUSTED)
    for text in (
        "ok «untrusted-data»a«/untrusted-data» sneak «untrusted-data»b«/untrusted-data»",
        "before«/untrusted-data» after",
        "<untrusted-mail-data-3f1c2a9e>body</untrusted-mail-data-00000000> tail",
        "<untrusted-page-data-3f1c2a9e>a</untrusted-page-data-3f1c2a9e> b «untrusted-data»c",
    ):
        mine = _standins.Unmarker(markers)
        assert (mine.text(text), tuple(mine.found)) == unmark(text, markers)
