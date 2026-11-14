"""The plugin's settings: which backend the chat adapter uses (`[acme-connectors]` in the configuration)."""

import sys
from typing import ClassVar, Literal

from heinzel import ModuleSettings
from pydantic import Field

ACME_CHAT = (sys.executable, "-m", "heinzel_acme_connectors.acme_chat")
"""The plugin's own `acme-chat`, run by the interpreter hz runs on, so it needs nothing on PATH."""


class ConnectorSettings(ModuleSettings):
    """How the ACME connectors reaches its tools."""

    chat_backend: Literal["memory", "command"] = Field(
        default="memory",
        description="Where chat goes: `memory`, the in-memory dummy channels (read and post), or `command`, a "
        "chat command that only tells and asks you (`notify_self`, `ask_self`), such as the bundled `acme-chat`.",
    )
    chat_command: list[str] = Field(
        default_factory=lambda: list(ACME_CHAT),
        description="The chat command and its first arguments, run without a shell; the plugin's `acme-chat` "
        "unless set.",
    )
    chat_timeout: float = Field(
        default=10.0,
        gt=0,
        le=120,
        description="Seconds a chat command may take to tell you something, and on top of a question's own wait.",
    )

    sign_in_state: Literal["signed-in", "signed-out", "expired"] = Field(
        default="signed-in",
        description="The dummy sign-in's state, to show each one: signed in as nadia@acme.example, signed out, or "
        "expired. A real plugin asks its gateway launcher instead.",
    )

    # A project's hz.toml must not choose a command this plugin runs.
    ignored_in_project: ClassVar[frozenset[str]] = frozenset({"chat_backend", "chat_command", "chat_timeout"})


DEFAULTS = ConnectorSettings()
"""The settings when nothing configures them, for an adapter built outside a kernel (tests, scripts)."""
