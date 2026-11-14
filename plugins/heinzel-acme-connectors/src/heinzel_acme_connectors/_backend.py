"""The backend seam: the one file a company replaces to talk to its MCP gateway instead of the dummy data.

Every adapter in this plugin reaches its data only through a `Backend`: `call(tool, arguments)` returns an
`McpResult`, Core's answer of an MCP tool: its JSON (`data`), its text, and the parts the gateway marked as untrusted.
Here `connect` serves each connector from an in-memory dummy server (`_dummy`) through `StandInConnector`, which does
what Core's `McpConnector` does: check that the server has every tool the adapter calls (under its own name or an
alias), refuse a write tool on a read-only connector, and take the gateway's untrusted-content markers off every
string in an answer, with Core's own rules.

In the real plugin each connector is one local stdio launcher that reaches the company MCP gateway; the launcher holds
the sign-in, the plugin holds no secret. Switching is this file only. With Core's MCP helper (ADR 0159,
`heinzel.connectors.mcp`, in the Core release after 0.9.42), `connect` becomes:

    from heinzel.connectors.mcp import McpConnector

    def connect(name: str) -> Backend:
        spec = CONNECTORS[name]
        return McpConnector(spec.launcher, tools=spec.tools, markers=spec.markers, modes=spec.modes)

`McpConnector` starts the launcher on the first call and raises `McpToolsMissingError` when the server lacks a tool;
`McpConnector.in_process(server, tools=..., markers=...)` runs an MCP server object in the test process, for a
company's own adapter tests. Then `StandInConnector` and `_dummy` are deleted, and the adapters stay as they are.
"""

import json
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from typing import Any, Literal, Protocol

from heinzel import HeinzelError

from heinzel_acme_connectors._compat import ENVELOPE_UNTRUSTED, INLINE_UNTRUSTED, McpResult, McpTool, UntrustedMarker
from heinzel_acme_connectors._standins import Unmarker

Mode = Literal["read", "write"]
READ_ONLY: tuple[Mode, ...] = ("read",)
READ_WRITE: tuple[Mode, ...] = ("read", "write")


def read(*names: str) -> tuple[McpTool, ...]:
    """Read tools by name."""
    return tuple(McpTool(name) for name in names)


def write(*names: str) -> tuple[McpTool, ...]:
    """Write tools by name."""
    return tuple(McpTool(name, mode="write") for name in names)


class Backend(Protocol):
    """What an adapter calls: one gateway connector."""

    def call(self, tool: str, arguments: Mapping[str, Any] | None = None) -> McpResult:
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
    """One gateway connector: how it is launched, its tools, its answers' markers, and the modes it serves.

    A read-only connector refuses write tools: least privilege, as `McpConnector(modes=...)` does.
    """

    name: str
    launcher: tuple[str, ...]
    tools: tuple[McpTool, ...]
    markers: tuple[UntrustedMarker, ...] = (INLINE_UNTRUSTED,)
    modes: tuple[Mode, ...] = READ_WRITE
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
        Connector("docs", _launcher("docs"), read("get_document", "search_documents"), modes=READ_ONLY),
        Connector("wiki", _launcher("wiki"), read("get_page", "search_pages"), modes=READ_ONLY),
        Connector(
            "tracker",
            _launcher("tracker"),
            (
                *read("search_issues", "get_issue"),
                *write("create_issue", "assign_issue", "transition_issue", "add_comment"),
            ),
        ),
        Connector("chat", _launcher("chat"), (*read("list_channels", "list_messages"), *write("post_message"))),
        Connector("meetings", _launcher("meetings"), read("list_meetings", "get_transcript"), modes=READ_ONLY),
        Connector("code-host", _launcher("code-host"), read("list_merged_pull_requests"), modes=READ_ONLY),
        Connector("directory", _launcher("directory"), read("get_person", "list_reports"), modes=READ_ONLY),
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
        self._writes = {tool.name: tool.mode == "write" for tool in spec.tools}
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

    def call(self, tool: str, arguments: Mapping[str, Any] | None = None) -> McpResult:
        """Call the canonical `tool` by the server's own name; its answer unmarked with Core's rules.

        Raises:
            HeinzelError: If `tool` is not one of the connector's tools, or writes on a read-only connector.
        """
        name = self._names.get(tool)
        if name is None:
            msg = f"The {self._spec.name} connector has no tool {tool!r}; declare it in CONNECTORS first."
            raise HeinzelError(msg)
        if self._writes[tool] and "write" not in self._spec.modes:
            msg = f"The tool {tool!r} writes, and the {self._spec.name} connector serves only read."
            raise HeinzelError(msg)
        unmarker = Unmarker(self._spec.markers)
        data = unmarker.value(self._server.call(name, arguments or {}))  # field by field, as Core does structured data
        text = json.dumps(data, ensure_ascii=False, default=str)
        return McpResult(text=text, data=data, untrusted=tuple(dict.fromkeys(unmarker.found)))


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
