"""The `ai-models` adapter: ACME's models for hz's own Pydantic AI engine (ADR 0159, not in a released Core yet).

`models()` answers from a fixed list, in no time, the default first. `model(id)` builds a Pydantic AI model and
never calls it: here a dummy that answers in a fixed sentence, offline; a real plugin builds a model for the
company's model gateway on its own HTTP client, its auth coming from the connector's local launcher, never from Core
or from this plugin. An id it doesn't offer raises `ModelUnavailableError`, naming the ones it does.

The adapter is registered only on a Core that has the `ai-models` capability (`__init__.py`); Core lists it as an AI
access option, not on the connector page, and derives `ai-access` from it. `ModelOffer` and `ModelUnavailableError`
come from Core when it has them, else from `_compat`.
"""

from typing import Any

from heinzel_acme_connectors._compat import ModelOffer, ModelUnavailableError

MODELS = (
    ModelOffer(
        id="acme/fast",
        title="ACME Fast",
        description="Quick answers and drafts, made up and offline.",
        context_window=128_000,
    ),
    ModelOffer(
        id="acme/deep",
        title="ACME Deep",
        description="Longer reasoning, made up and offline.",
        aliases=["acme/default"],
        context_window=200_000,
    ),
    ModelOffer(id="acme/retired", title="ACME Retired", description="Switched off; pick another.", available=False),
)
"""ACME's models: the default first."""


class AcmeModels:
    """ACME's models through the company model gateway; a dummy that answers in a fixed sentence."""

    title = "ACME models"
    summary = "ACME's own models, through the company model gateway (dummy, offline)."

    def models(self) -> list[ModelOffer]:
        """The models on offer now, the default first. Mode: read."""
        return list(MODELS)

    def model(self, model_id: str) -> Any:  # noqa: ANN401 - a pydantic_ai Model; Core doesn't type the SDK
        """A Pydantic AI model for `model_id` (or one of its aliases), built and never called. Mode: read.

        Raises:
            ModelUnavailableError: If ACME offers no such model, or not now.
        """
        offer = next((m for m in MODELS if model_id == m.id or model_id in m.aliases), None)
        others = [m.id for m in MODELS if m.available and m is not offer]
        if offer is None:
            raise ModelUnavailableError(model_id, others=others, reason="ACME offers no such model")
        if not offer.available:
            raise ModelUnavailableError(model_id, others=others, reason="switched off")
        # Pydantic AI comes with Heinzelmännchen; imported here so the other connectors never load it.
        from pydantic_ai.messages import ModelMessage, ModelResponse, TextPart  # noqa: PLC0415
        from pydantic_ai.models.function import AgentInfo, FunctionModel  # noqa: PLC0415

        def answer(messages: list[ModelMessage], _info: AgentInfo) -> ModelResponse:
            sentence = f"{offer.title} (dummy) read {len(messages)} message(s); a real gateway answers here."
            return ModelResponse(parts=[TextPart(sentence)])

        return FunctionModel(answer, model_name=offer.id)
