"""The adapters bound through configuration, used by a requester that names capabilities only, through the CLI."""

import json
from datetime import UTC, datetime

import pytest
from heinzel import Calendar, Chat, CodeHost, Directory, Documents, Kernel, Mail, Meetings, Module, Tracker, Window
from heinzel.heads.cli import build
from typer.testing import CliRunner

pytestmark = pytest.mark.integration

WEEK = Window(since=datetime(2026, 11, 1, tzinfo=UTC), until=datetime(2026, 11, 8, tzinfo=UTC))

ALL = {
    "mail": "acme-connectors",
    "calendar": "acme-connectors",
    "documents": "acme-connectors-docs",
    "tracker": "acme-connectors",
    "chat": "acme-connectors",
    "meetings": "acme-connectors",
    "code-host": "acme-connectors",
    "directory": "acme-connectors",
}


def requester() -> Module:
    """A test-only workflow module: it asks for capabilities, never for a vendor."""
    module = Module(
        "probe",
        "Test-only probe of every capability.",
        requires=[
            "mail:read",
            "calendar:read",
            "documents:read",
            "tracker:read",
            "chat:read",
            "meetings:read",
            "code-host:read",
            "directory:read",
        ],
    )

    @module.operation
    def week(  # noqa: PLR0913, PLR0917 - one handle per capability
        mail: Mail,
        calendar: Calendar,
        documents: Documents,
        tracker: Tracker,
        chat: Chat,
        meetings: Meetings,
        code: CodeHost,
        directory: Directory,
    ) -> dict[str, object]:
        """Read one thing from every capability."""
        mira = directory.person("nadia")
        return {
            "mail": len(mail.messages("label:inbox", WEEK)),
            "calendar": [e.title for e in calendar.events(WEEK)][:1],
            "documents": documents.read("doc-roadmap").title,
            "tracker": [i.key for i in tracker.issues_updated("CHK", WEEK)],
            "chat": len(chat.messages("#release", WEEK)),
            "meetings": [m.id for m in meetings.ended(WEEK)],
            "code": [p.number for p in code.merged_pull_requests("acme/acme-checkout", WEEK)],
            "directory": mira.title if mira else None,
        }

    @module.operation(read_only=False, requires=["mail:write"])
    def send(mail: Mail) -> str:
        """Try to send a draft."""
        return mail.send_draft("d-1", "m-draft-1").id

    @module.operation(read_only=False, requires=["documents:write"])
    def rewrite(documents: Documents) -> str:
        """Try to write a section."""
        return documents.replace_section("doc-roadmap", "goals", "x").ref

    return module


def hz(kernel: Kernel, *args: str) -> tuple[int, object]:
    result = CliRunner().invoke(build(kernel), [*args, "--json"])
    try:
        return result.exit_code, json.loads(result.output)
    except json.JSONDecodeError:
        return result.exit_code, result.output


def test_every_capability_is_served_by_acme_connectors_once_bound(connectors_kernel):
    code, answer = hz(connectors_kernel(ALL, probe=requester()), "probe", "week")
    assert code == 0, answer
    assert answer == {
        "mail": 3,
        "calendar": ["Weekly sync"],
        "documents": "Roadmap 2027",
        "tracker": ["CHK-1", "CHK-2"],
        "chat": 2,
        "meetings": ["mt-1", "mt-2"],
        "code": [41, 42],
        "directory": "Engineering Manager",
    }


def test_the_wiki_serves_documents_when_bound_instead(connectors_kernel):
    module = Module("wiki-probe", "Test-only.", requires=["documents:read"])

    @module.operation
    def page(documents: Documents) -> str:
        """Read a page."""
        return documents.read("10001").title

    code, answer = hz(
        connectors_kernel({"documents": "acme-connectors-wiki"}, **{"wiki-probe": module}), "wiki-probe", "page"
    )
    assert (code, answer) == (0, "Team handbook")


def test_an_unsupported_write_is_refused_with_a_clear_message(connectors_kernel):
    code, answer = hz(connectors_kernel(ALL, probe=requester()), "probe", "send")
    assert code != 0
    # A Core with ADR 0159 refuses an `unsupported` method itself, before the call, without the adapter's reason.
    assert "This mail connector can't send draft" in str(answer)


def test_a_write_mode_the_adapter_does_not_serve_is_refused_by_the_kernel(connectors_kernel):
    code, answer = hz(connectors_kernel(ALL, probe=requester()), "probe", "rewrite")
    assert code != 0
    assert "serves only read" in str(answer)


def test_the_connector_page_shows_the_sign_in_state_from_settings(configured_kernel):
    for state, signed_in in (("signed-in", True), ("expired", True), ("signed-out", False)):
        kernel = configured_kernel({"acme-connectors": {"sign_in_state": state}})
        code, report = hz(kernel, "system", "connector", "list")
        assert code == 0, report
        (mine,) = [c for c in report["connectors"] if c["name"] == "acme-connectors"]
        assert mine["login"]["signed_in"] is signed_in, state
        assert mine["state"] != "connected" or state == "signed-in"


def test_the_chat_backend_setting_reaches_the_adapter(configured_kernel):
    module = Module("poster", "Test-only.")

    @module.operation(read_only=False, requires=["chat:write"])
    def say(chat: Chat) -> str:
        """Post."""
        return chat.post("#checkout", "hi").id

    kernel = configured_kernel(
        {"capabilities": {"chat": "acme-connectors"}, "acme-connectors": {"chat_backend": "command"}}, poster=module
    )
    code, answer = hz(kernel, "poster", "say")
    assert code != 0
    assert "This chat connector can't post" in str(answer)
