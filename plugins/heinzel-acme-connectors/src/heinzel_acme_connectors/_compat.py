"""Core's classes for ADR 0159, 0160 and 0161 when the installed Core has them, else the exact copies in `_standins`.

Each feature is checked on its own, as an older Core may have one and not another. Type checkers see the stand-ins;
at runtime every name is Core's own class where it exists, so `except NotSupportedError` and `isinstance` checks
match what Core raises and returns. Once the minimum Core is the release that ships them, import them from `heinzel`
(`heinzel.connectors.mcp` for the MCP helper) and delete this file and `_standins.py`.
"""

import importlib
from typing import TYPE_CHECKING, Any

import heinzel

from heinzel_acme_connectors import _standins


def _core(module: Any, name: str) -> Any:  # noqa: ANN401 - a class, typed by the stand-in below
    return getattr(module, name, getattr(_standins, name))


try:
    _mcp: Any = importlib.import_module("heinzel.connectors.mcp")
except ImportError:  # a Core before ADR 0159's MCP helper
    _mcp = _standins

HAS_AI_MODELS = hasattr(heinzel, "AiModels")
"""Whether the installed Core has the `ai-models` capability (ADR 0159)."""
HAS_MULTI_DOCS = hasattr(heinzel, "DocumentHit")
"""Whether the installed Core binds several documents adapters and routes by their `links` (ADR 0161)."""
HAS_MCP_HELPER = _mcp is not _standins
"""Whether the installed Core has `heinzel.connectors.mcp` (ADR 0159)."""

if TYPE_CHECKING:
    from heinzel_acme_connectors._standins import (
        ENVELOPE_UNTRUSTED,
        INLINE_UNTRUSTED,
        DocumentHit,
        McpResult,
        McpTool,
        ModelOffer,
        ModelUnavailableError,
        NotSupportedError,
        SelfAnswer,
        SelfMessage,
        UntrustedMarker,
    )
else:
    NotSupportedError = _core(heinzel, "NotSupportedError")
    ModelOffer = _core(heinzel, "ModelOffer")
    ModelUnavailableError = _core(heinzel, "ModelUnavailableError")
    SelfMessage = _core(heinzel, "SelfMessage")
    SelfAnswer = _core(heinzel, "SelfAnswer")
    DocumentHit = _core(heinzel, "DocumentHit")
    McpTool = _core(_mcp, "McpTool")
    McpResult = _core(_mcp, "McpResult")
    UntrustedMarker = _core(_mcp, "UntrustedMarker")
    INLINE_UNTRUSTED = _core(_mcp, "INLINE_UNTRUSTED")
    ENVELOPE_UNTRUSTED = _core(_mcp, "ENVELOPE_UNTRUSTED")

__all__ = [
    "ENVELOPE_UNTRUSTED",
    "HAS_AI_MODELS",
    "HAS_MCP_HELPER",
    "HAS_MULTI_DOCS",
    "INLINE_UNTRUSTED",
    "DocumentHit",
    "McpResult",
    "McpTool",
    "ModelOffer",
    "ModelUnavailableError",
    "NotSupportedError",
    "SelfAnswer",
    "SelfMessage",
    "UntrustedMarker",
]
