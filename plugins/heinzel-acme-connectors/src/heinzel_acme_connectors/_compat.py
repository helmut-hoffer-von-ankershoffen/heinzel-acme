"""Shims for ADR 0159 (`NotSupportedError`, `ModelOffer`, `ModelUnavailableError`), 0160 (chat self), 0161 (search).

Core ships them in a release after 0.9.42; until then this module defines the same shapes.

Core will export `heinzel.NotSupportedError(capability, method, reason="")`, a `HeinzelError` whose message is
"This {capability} connector can't {method with spaces}: {reason}.", and honour an `unsupported` class attribute on an
adapter: a `frozenset` of the capability's method names that the kernel's handle refuses with that error before it
calls the adapter. Until then this module defines the same shape locally; with that Core release it imports Core's
class, so `except NotSupportedError` catches both. Delete this file once the minimum Core version has it.
"""

from typing import TYPE_CHECKING

import heinzel
from heinzel import HeinzelError
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field


class _NotSupportedError(HeinzelError):
    """A capability method this connector can't do: the local stand-in for Core's `NotSupportedError`."""

    def __init__(self, capability: str, method: str, reason: str = "") -> None:
        """Say which method of which capability this connector can't do, and why if `reason` says."""
        self.capability = capability
        self.method = method
        self.reason = reason
        why = f": {reason}" if reason else ""
        super().__init__(f"This {capability} connector can't {method.replace('_', ' ')}{why}.")


if TYPE_CHECKING:
    NotSupportedError = _NotSupportedError
else:  # Core's class when the installed Core has it, else the local one with the same constructor and message
    NotSupportedError = getattr(heinzel, "NotSupportedError", _NotSupportedError)


class _SelfMessage(BaseModel):
    """What `Chat.notify_self` and `Chat.ask_self` posted to the user: the local stand-in for Core's (ADR 0160)."""

    id: str
    thread: str
    url: str | None = None


class _SelfAnswer(BaseModel):
    """The user's answer to `Chat.ask_self`: text or a chosen option, or nothing when it timed out (ADR 0160)."""

    thread: str | None = None
    text: str = ""
    option: str | None = None
    timed_out: bool = False


if TYPE_CHECKING:
    SelfMessage = _SelfMessage
    SelfAnswer = _SelfAnswer
else:  # Core's models once it ships ADR 0160 (stacked on ADR 0159, not released), else the local ones
    SelfMessage = getattr(heinzel, "SelfMessage", _SelfMessage)
    SelfAnswer = getattr(heinzel, "SelfAnswer", _SelfAnswer)


class _ModelOffer(BaseModel):
    """One model a plugin offers (ADR 0159): the local stand-in for Core's `ModelOffer`, the same fields."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str = Field(pattern=r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,199}$")
    title: str = ""
    description: str = Field(default="", max_length=500)
    aliases: list[str] = Field(default_factory=list[str])
    context_window: int | None = None
    efforts: list[str] = Field(default_factory=list[str])
    tools: bool = True
    thinking: str | None = None
    available: bool = True


class _ModelUnavailableError(HeinzelError):
    """A model isn't offered or doesn't answer now (ADR 0159): the local stand-in for Core's error."""

    def __init__(self, model_id: str, others: list[str] | None = None, reason: str = "") -> None:
        """Say which model is unavailable, why, and which to pick instead."""
        self.model_id = model_id
        self.others = list(others or [])
        why = f" ({reason})" if reason else ""
        pick = f"; pick {', '.join(self.others)}" if self.others else ""
        super().__init__(f"Model {model_id} is unavailable{why}{pick}.")


HAS_AI_MODELS = hasattr(heinzel, "AiModels")
"""Whether the installed Core has the `ai-models` capability (ADR 0159)."""

if TYPE_CHECKING:
    ModelOffer = _ModelOffer
    ModelUnavailableError = _ModelUnavailableError
else:  # Core's when it ships ADR 0159, else the local stand-ins with the same fields and constructor
    ModelOffer = getattr(heinzel, "ModelOffer", _ModelOffer)
    ModelUnavailableError = getattr(heinzel, "ModelUnavailableError", _ModelUnavailableError)


class _DocumentHit(BaseModel):
    """One search result of a documents adapter (ADR 0161): the local stand-in for Core's `DocumentHit`."""

    ref: str
    title: str
    url: str | None = None
    snippet: str | None = None
    updated_at: AwareDatetime | None = None
    source: str | None = None


HAS_MULTI_DOCS = hasattr(heinzel, "DocumentHit")
"""Whether the installed Core binds several documents adapters and routes by their `links` (ADR 0161)."""

if TYPE_CHECKING:
    DocumentHit = _DocumentHit
else:  # Core's once it ships ADR 0161, else the local stand-in with the same fields
    DocumentHit = getattr(heinzel, "DocumentHit", _DocumentHit)
