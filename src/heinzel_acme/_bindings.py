"""How Acme reaches its tools: one capability binding per row, the adapter that serves it and how people sign in.

Acme uses only what an ordinary employee may (Heinzelmännchen ADR 0035): each adapter is a first-party plugin whose
transport is the vendor's CLI, logged in as the person. The rows become the company playbook's recommended settings,
which `hz setup acme` offers one by one and writes only on yes; `hz system doctor` says which adapter plugin is
missing. A company that reaches its tools differently replaces this table in its own company plugin
(docs/PORT_TO_YOUR_COMPANY.md).
"""

from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True, slots=True)
class Binding:
    """One capability, the adapter Acme binds to it, and what that adapter needs on the person's machine."""

    capability: str
    """The core's capability name, e.g. `code-host`."""
    adapter: str
    """The adapter configuration binds to it, e.g. `github`."""
    plugin: str
    """The first-party plugin that brings the adapter, as `hz system plugin add` takes it."""
    transport: str
    """What the adapter talks through, in words."""
    login: str
    """The command the person runs once so the adapter can read as them."""

    @property
    def setting(self) -> str:
        """The setting key, as `hz system config set` takes it: `capabilities.code_host`."""
        return f"capabilities.{self.capability.replace('-', '_')}"


BINDINGS: tuple[Binding, ...] = (
    Binding(
        capability="code-host",
        adapter="github",
        plugin="github",
        transport="GitHub through gh",
        login="gh auth login",
    ),
    Binding(
        capability="tracker",
        adapter="atlassian",
        plugin="atlassian",
        transport="Jira through acli",
        login="acli jira auth login --web",
    ),
    Binding(
        capability="documents",
        adapter="google",
        plugin="google",
        transport="Google Docs and Sheets through gws",
        login="gws auth login",
    ),
    Binding(
        capability="calendar",
        adapter="google",
        plugin="google",
        transport="Google Calendar through gws",
        login="gws auth login",
    ),
    Binding(
        capability="mail",
        adapter="google",
        plugin="google",
        transport="Gmail through gws",
        login="gws auth login",
    ),
    Binding(
        capability="meetings",
        adapter="zoom",
        plugin="zoom",
        transport="Zoom's meeting-summary e-mails, read through the mail binding",
        login="switch on meeting summaries in Zoom, mailed to you",
    ),
)
"""Acme's default bindings: code host, tracker, documents, calendar, mail and meetings."""


def recommended() -> dict[str, str]:
    """The bindings as a playbook's recommended settings: `{"capabilities.code_host": "github", ...}`."""
    return {binding.setting: binding.adapter for binding in BINDINGS}
