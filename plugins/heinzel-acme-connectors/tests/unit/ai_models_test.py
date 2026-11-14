"""The `ai-models` adapter: ACME's models, the default first, a dummy model built and never called, clear refusals."""

import pytest
from heinzel_acme_connectors import AcmeModels, module
from heinzel_acme_connectors._compat import HAS_AI_MODELS, ModelOffer, ModelUnavailableError
from pydantic import ValidationError

pytestmark = pytest.mark.unit


def test_the_models_are_offered_default_first_and_one_is_switched_off():
    offers = AcmeModels().models()
    assert [(m.id, m.available) for m in offers] == [("acme/fast", True), ("acme/deep", True), ("acme/retired", False)]
    assert offers[1].aliases == ["acme/default"]
    assert all(isinstance(m, ModelOffer) for m in offers)


def test_a_model_is_built_by_id_or_alias_and_answers_offline():
    from pydantic_ai import Agent

    fast = AcmeModels().model("acme/fast")
    assert fast.model_name == "acme/fast"
    deep = AcmeModels().model("acme/default")
    assert deep.model_name == "acme/deep"
    answer = Agent(fast).run_sync("Summarise the week").output
    assert answer == "ACME Fast (dummy) read 1 message(s); a real gateway answers here."


@pytest.mark.parametrize(
    ("model_id", "why"), [("acme/huge", "ACME offers no such model"), ("acme/retired", "switched off")]
)
def test_an_unknown_or_switched_off_model_is_refused_naming_the_others(model_id, why):
    with pytest.raises(ModelUnavailableError) as refused:
        AcmeModels().model(model_id)
    assert why in str(refused.value)
    assert refused.value.others[:2] == ["acme/fast", "acme/deep"]


def test_an_offer_is_frozen_and_checks_its_id():
    with pytest.raises(ValidationError):
        ModelOffer(id="bad id with spaces")
    with pytest.raises(ValidationError):
        AcmeModels().models()[0].title = "changed"  # type: ignore[misc]


def test_the_adapter_is_registered_only_on_a_core_with_ai_models():
    names = {let.name for let in module.lets}
    assert ("acme-connectors:ai-models" in names) == HAS_AI_MODELS
