"""The backend seam: the one file a company replaces to talk to its MCP gateway instead of the dummy data.

Every adapter in this plugin reaches its data only through a `Backend`: `call(tool, arguments)` returns a `Reply`
with the tool's JSON answer (`data`), its text, and the segments the gateway marked as untrusted. Here `connect`
serves each connector from an in-memory dummy server (`_dummy`) through `StandInConnector`, which does what a real
MCP client must do: check at startup that the server has every tool the adapter calls (under its own name or an
alias), and take the gateway's untrusted-content markers off every string in an answer.

In the real plugin each connector is one local stdio launcher that reaches the company MCP gateway; the launcher
holds the sign-in, the plugin holds no secret. Switching is this file only. With ADR 0159 Head B's public helper
(`heinzel.connectors.mcp`, not released yet; names as its builder gave them), `connect` becomes:

    from heinzel.connectors.mcp import McpConnector, McpTool

    def connect(name: str) -> Backend:
        spec = CONNECTORS[name]
        tools = [McpTool(t.name, mode=t.mode, aliases=t.aliases) for t in spec.tools]
        connector = McpConnector(spec.launcher, tools=tools, markers=spec.markers)
        connector.start()  # raises McpToolsMissingError when the server lacks a tool
        return connector

with Core's `UntrustedMarker`, `INLINE_UNTRUSTED` and `ENVELOPE_UNTRUSTED` in `CONNECTORS`, and `StandInConnector`,
`McpTool` here, `_markers` and `_dummy` are deleted. The adapters stay as they are: they call canonical tool names and
read `.data`, which `McpResult` has too.
"""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from heinzel import HeinzelError

from heinzel_acme_connectors._markers import ENVELOPE_UNTRUSTED, INLINE_UNTRUSTED, UntrustedMarker, unwrap


@dataclass(frozen=True)
class McpTool:
    """A tool an adapter calls: its canonical name, whether it reads or writes, and other names a gateway may use.

    The local stand-in for Head B's `McpTool(name, mode="read", aliases=())`.
    """

    name: str
    mode: Literal["read", "write"] = "read"
    aliases: tuple[str, ...] = ()


def read(*names: str) -> tuple[McpTool, ...]:
    """Read tools by name."""
    return tuple(McpTool(name) for name in names)


def write(*names: str) -> tuple[McpTool, ...]:
    """Write tools by name."""
    return tuple(McpTool(name, mode="write") for name in names)


@dataclass(frozen=True)
class Reply:
    """One tool's answer, markers removed: the shape of Head B's `McpResult` (`text`, `data`, `untrusted`)."""

    data: Any
    text: str = ""
    untrusted: tuple[str, ...] = ()


class Backend(Protocol):
    """What an adapter calls: one gateway connector."""

    def call(self, tool: str, arguments: Mapping[str, Any] | None = None) -> Reply:
        """Call `tool` (a canonical name) with `arguments` and return its answer."""
        ...


class Server(Protocol):
    """An MCP server as the stand-in sees it: its tool names, and a call by the server's own name."""

    def tools(self) -> list[str]:
        """The names of the tools the server offers."""
        ...

    def call(self, tool: str, arguments: Mapping[str, Any]) -> Any:  # noqa: ANN401 - a tool answers JSON
        """Run the tool `tool` and return its JSON answer, markers still on."""
        ...


@dataclass(frozen=True)
class Connector:
    """One gateway connector: how it is launched, the tools its adapter calls, and the markers its answers carry."""

    name: str
    launcher: tuple[str, ...]
    tools: tuple[McpTool, ...]
    markers: tuple[UntrustedMarker, ...] = (INLINE_UNTRUSTED,)
    env: Mapping[str, str] = field(default_factory=dict[str, str])


def _launcher(connector: str) -> tuple[str, ...]:
    # One local launcher per connector; it signs in and reaches the gateway. Made up: this plugin never runs it.
    return ("acme-mcp", "--connector", connector)


CONNECTORS: Mapping[str, Connector] = {
    spec.name: spec
    for spec in (
        Connector(
            "mail",
            _launcher("mail"),
            (
                McpTool("search_messages", aliases=("mail_search",)),
                *read("get_message", "get_thread", "get_draft"),
                *write("create_draft", "modify_labels"),
            ),
            (INLINE_UNTRUSTED, ENVELOPE_UNTRUSTED),
        ),
        Connector(
            "calendar",
            _launcher("calendar"),
            (*read("list_events", "get_event", "free_busy"), *write("create_event", "update_event", "cancel_event")),
        ),
        Connector("docs", _launcher("docs"), read("get_document", "search_documents")),
        Connector("wiki", _launcher("wiki"), read("get_page", "search_pages")),
        Connector(
            "tracker",
            _launcher("tracker"),
            (
                *read("search_issues", "get_issue"),
                *write("create_issue", "assign_issue", "transition_issue", "add_comment"),
            ),
        ),
        Connector("chat", _launcher("chat"), (*read("list_channels", "list_messages"), *write("post_message"))),
        Connector("meetings", _launcher("meetings"), read("list_meetings", "get_transcript")),
        Connector("code-host", _launcher("code-host"), read("list_merged_pull_requests")),
        Connector("directory", _launcher("directory"), read("get_person", "list_reports")),
    )
}
"""Every connector this plugin's adapters use, by name."""


class StandInConnector:
    """A stand-in for Head B's `McpConnector`, over an in-process `Server` instead of a stdio launcher."""

    def __init__(self, spec: Connector, server: Server) -> None:
        """Check that `server` offers every tool of `spec`, by its name or an alias, before any call.

        Raises:
            HeinzelError: If a tool is missing: a gateway change would otherwise fail later, in the middle of a run.
        """
        offered = set(server.tools())
        self._spec = spec
        self._server = server
        self._names: dict[str, str] = {}
        missing: list[str] = []
        for tool in spec.tools:
            found = next((name for name in (tool.name, *tool.aliases) if name in offered), None)
            if found is None:
                missing.append(tool.name)
            else:
                self._names[tool.name] = found
        if missing:
            msg = (
                f"The {spec.name} connector's server lacks the tools {', '.join(sorted(missing))}; "
                "update the launcher or ask the gateway's owner."
            )
            raise HeinzelError(msg)

    def call(self, tool: str, arguments: Mapping[str, Any] | None = None) -> Reply:
        """Call the canonical `tool` by the server's own name, and unwrap the answer's markers.

        Raises:
            HeinzelError: If `tool` is not one of the connector's tools.
        """
        name = self._names.get(tool)
        if name is None:
            msg = f"The {self._spec.name} connector has no tool {tool!r}; declare it in CONNECTORS first."
            raise HeinzelError(msg)
        data, untrusted = unwrap(self._server.call(name, arguments or {}), self._spec.markers)
        return Reply(data=data, text=json.dumps(data, ensure_ascii=False, default=str), untrusted=untrusted)


def _dummy_server(name: str) -> Server:
    from heinzel_acme_connectors._dummy import server  # noqa: PLC0415 - the dummy is the part a real plugin deletes

    return server(name)


ServerFactory = Callable[[str], Server]


def connect(name: str, servers: ServerFactory = _dummy_server) -> Backend:
    """The backend of the connector `name`; here served by the dummy data.

    Raises:
        HeinzelError: If no connector has that name, or its server lacks a tool.
    """
    spec = CONNECTORS.get(name)
    if spec is None:
        msg = f"No connector {name!r}; known: {', '.join(sorted(CONNECTORS))}."
        raise HeinzelError(msg)
    return StandInConnector(spec, servers(name))
