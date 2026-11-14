"""The `mail` adapter (Google-style mailbox): read, keep drafts, file conversations; sending is not supported.

The gateway offers no send tool, so `send_draft` is unsupported: people send a draft from their mail client. The
rest is served in read and write mode. Bodies arrive in the gateway's mail envelope, which the backend takes off.
"""

from typing import Any

from heinzel import (
    DraftedMail,
    MailContent,
    MailDraft,
    MailLabels,
    MailMessage,
    MailQuery,
    MailThread,
    SentMail,
    Window,
)

from heinzel_acme_connectors._base import ConnectorAdapter, bounded, participant, window_arguments
from heinzel_acme_connectors._text import as_dict, as_list, line, moment, optional, text

MAX_TEXT = 200_000
"""Characters of one body kept."""
PORTABLE = {"inbox": "INBOX", "unread": "UNREAD"}
"""The portable label names every mail adapter knows (Core), in this gateway's words."""


def _message(value: object) -> MailMessage:
    entry = as_dict(value)
    return MailMessage(
        id=line(entry.get("id"), 200),
        thread=optional(entry.get("thread"), 200),
        sender=participant(entry.get("from")),
        recipients=[participant(p) for p in [*as_list(entry.get("to")), *as_list(entry.get("cc"))]],
        subject=line(entry.get("subject")),
        received_at=moment(entry.get("received"), "a message"),
        labels=[line(label, 100) for label in as_list(entry.get("labels"))],
        url=f"https://mail.acme.example/m/{line(entry.get('id'), 200)}",
    )


def _content(value: object) -> MailContent:
    entry = as_dict(value)
    headers = {line(k, 100): line(v, 1000) for k, v in as_dict(entry.get("headers")).items()}
    return MailContent(message=_message(entry), text=text(entry.get("body"), MAX_TEXT), headers=headers)


def _drafted(value: object) -> DraftedMail:
    entry = as_dict(value)
    key = line(entry.get("id"), 200)
    return DraftedMail(id=key, content=_content(entry.get("message")), url=f"https://mail.acme.example/d/{key}")


class AcmeMail(ConnectorAdapter):
    """A mailbox through the gateway's `mail` connector."""

    connector = "mail"
    capability = "mail"
    unsupported = frozenset({"send_draft"})

    def messages(self, query: str, window: Window) -> list[MailMessage]:
        """Messages that match `query` (see `MailQuery`) and were received within `window`, oldest first. Mode: read.

        Raises:
            HeinzelError: If the query or window is invalid, there are too many messages, or the gateway fails.
        """
        wanted = MailQuery.parse(query)
        arguments: dict[str, Any] = window_arguments(window)
        # Translate what the gateway's search understands; `matches` checks every answer anyway.
        arguments |= {k: v for k, v in {"from": wanted.sender, "label": wanted.label}.items() if v}
        found = [_message(m) for m in as_list(self._call("search_messages", **arguments))]
        kept = [m for m in found if window.since <= m.received_at < window.until and wanted.matches(m)]
        return bounded(sorted(kept, key=lambda m: m.received_at), "messages")

    def read(self, message: str) -> MailContent:
        """The message `message` (a `MailMessage.id`) with its text and headers. Mode: read.

        Raises:
            HeinzelError: If the gateway knows no such message.
        """
        return _content(self._call("get_message", id=message))

    def thread(self, thread: str) -> MailThread:
        """The conversation `thread` with every message's text, oldest first. Mode: read.

        Raises:
            HeinzelError: If the gateway knows no such conversation.
        """
        entry = as_dict(self._call("get_thread", id=thread))
        messages = sorted((_content(m) for m in as_list(entry.get("messages"))), key=lambda c: c.message.received_at)
        return MailThread(id=line(entry.get("id"), 200), subject=line(entry.get("subject")), messages=messages)

    def draft(self, draft: str) -> DraftedMail:
        """The draft `draft` as it stands. Mode: read.

        Raises:
            HeinzelError: If the gateway knows no such draft.
        """
        return _drafted(self._call("get_draft", id=draft))

    def create_draft(self, draft: MailDraft) -> DraftedMail:
        """Keep `draft` as a draft in the mailbox, unsent; a reply joins its conversation. Mode: write.

        Raises:
            HeinzelError: If the gateway refuses it (a reply to an unknown message).
        """
        made = self._call(
            "create_draft",
            to=draft.to,
            cc=draft.cc,
            subject=draft.subject,
            text=draft.text,
            reply_to=draft.reply_to,
            reply_all=draft.reply_all,
        )
        return _drafted(made)

    def send_draft(self, draft: str, seen: str) -> SentMail:  # noqa: ARG002 - the protocol's shape; refused
        """Not supported: the gateway has no send tool. Mode: write.

        Raises:
            NotSupportedError: Always.
        """
        self._refuse("send_draft", "the gateway keeps drafts but never sends them; send it from your mail app")

    def relabel(self, thread: str, add: list[str], remove: list[str]) -> MailLabels:
        """File the conversation `thread`: add `add` and remove `remove`, by name. Mode: write.

        Raises:
            HeinzelError: If the gateway knows no such conversation.
        """

        def names(labels: list[str]) -> list[str]:
            return [PORTABLE.get(label.casefold(), label) for label in labels]

        entry = as_dict(self._call("modify_labels", thread=thread, add=names(add), remove=names(remove)))
        return MailLabels(
            thread=line(entry.get("thread"), 200), labels=[line(x, 100) for x in as_list(entry.get("labels"))]
        )
