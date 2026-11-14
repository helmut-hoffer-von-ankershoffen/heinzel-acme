"""The `chat` adapter: Slack-style channels in memory, or a chat command that only tells and asks the user.

The setting `acme-connectors.chat_backend` picks the backend. `memory` (the default) serves every method on the
dummy channels. `command` runs a chat command (`acme-connectors.chat_command`, the bundled `acme-chat` unless set)
for `notify_self` and `ask_self`, and declares `messages` and `post` unsupported: the shape of a self-only chat tool.
"""

import re
import threading
from collections.abc import Sequence

from heinzel import HeinzelError, Message, PostedMessage, Window

from heinzel_acme_connectors._backend import Backend
from heinzel_acme_connectors._base import ConnectorAdapter, bounded, participant, window_arguments
from heinzel_acme_connectors._chat_command import ChatCommand
from heinzel_acme_connectors._compat import SelfAnswer, SelfMessage
from heinzel_acme_connectors._settings import DEFAULTS, ConnectorSettings
from heinzel_acme_connectors._text import as_dict, as_list, line, moment, optional, text

MAX_POST = 4_000
"""Characters one post keeps; the rest is cut with an ellipsis."""
_BROADCAST = re.compile(r"<!(?:channel|here|everyone)(?:\|[^>]*)?>|<!subteam\^[^>]*>", re.IGNORECASE)
_MENTION = re.compile(r"<@[A-Z0-9]+(?:\|[^>]*)?>")
_BARE = re.compile(r"(?<![\w@])@(channel|here|everyone)\b", re.IGNORECASE)


def neutralised(value: str) -> str:
    """`value` without broadcast or mention syntax: `<!here>` pages nobody, `<@U1>` names nobody."""
    value = _BROADCAST.sub("(everyone)", value)
    value = _MENTION.sub("(someone)", value)
    return _BARE.sub(r"(\1)", value)


SELF = "D100"
"""The direct-message channel with the user themself, where `notify_self` and `ask_self` post."""


class AcmeChat(ConnectorAdapter):
    """Channels through the gateway's `chat` connector; a channel is an id (`C100`) or a `#name`.

    `notify_self` and `ask_self` (ADR 0160, not in a released Core yet) post to the user's own direct-message
    channel. The dummy answers a question with its first option at once, and a free-text question never: it waits
    until `cancel` is set or `timeout` passes, then reports a timeout. A real plugin waits for the user's reply.
    """

    connector = "chat"
    capability = "chat"

    def __init__(self, settings: ConnectorSettings = DEFAULTS, backend: Backend | None = None) -> None:
        """Build the adapter on the backend `settings` choose; the kernel passes the plugin's settings.

        The annotation is the settings class itself, not optional: the kernel injects by that exact type.
        """
        chosen = settings
        self._command: ChatCommand | None = None
        if chosen.chat_backend == "command":
            self._command = ChatCommand(chosen.chat_command, chosen.chat_timeout)
            self.unsupported = frozenset({"messages", "post"})
        super().__init__(backend)

    def _no_channels(self, method: str) -> None:
        if self._command is not None:
            reason = (
                "the chat command only tells and asks you; choose acme-connectors.chat_backend = memory for channels"
            )
            self._refuse(method, reason)

    def _channel(self, channel: str) -> str:
        if not channel.startswith("#"):
            return channel
        name = channel.removeprefix("#").casefold()
        for entry in as_list(self._call("list_channels")):
            if line(as_dict(entry).get("name"), 80).casefold() == name:
                return line(as_dict(entry).get("id"), 80)
        msg = f"No channel {channel[:80]!r}; give a channel id or an existing #name."
        raise HeinzelError(msg)

    def messages(self, channel: str, window: Window) -> list[Message]:
        """Messages posted in `channel` within `window`, top-level or reply, oldest first. Mode: read.

        Raises:
            HeinzelError: If the channel is unknown, or the window is backwards or holds too many messages.
        """
        self._no_channels("messages")
        key = self._channel(channel)
        found: list[Message] = []
        for value in as_list(self._call("list_messages", channel=key, **window_arguments(window))):
            entry = as_dict(value)
            ts = line(entry.get("ts"), 40)
            found.append(
                Message(
                    channel=key,
                    id=ts,
                    author=participant(entry.get("user")),
                    posted_at=moment(entry.get("posted"), "a message"),
                    text=text(entry.get("text")),
                    thread=optional(entry.get("thread_ts"), 40),
                    reply_count=max(0, int(entry.get("reply_count") or 0)),
                    url=f"https://chat.acme.example/archives/{key}/p{ts.replace('.', '')}",
                )
            )
        return bounded(sorted(found, key=lambda m: m.posted_at), "messages")

    def post(self, channel: str, text: str, thread: str | None = None) -> PostedMessage:
        """Post `text` to `channel`, as a reply in `thread` when given, broadcasts neutralised. Mode: write.

        Raises:
            HeinzelError: If the channel is unknown.
        """
        self._no_channels("post")
        key = self._channel(channel)
        body = neutralised(text)
        body = body if len(body) <= MAX_POST else body[: MAX_POST - 1] + "…"
        entry = as_dict(self._call("post_message", channel=key, text=body, thread_ts=thread))
        return PostedMessage(
            channel=line(entry.get("channel"), 80),
            id=line(entry.get("ts"), 40),
            thread=optional(entry.get("thread_ts"), 40),
            url=optional(entry.get("permalink"), 500),
        )

    def _post_self(self, text: str, thread: str | None, context: str | None) -> SelfMessage:
        body = neutralised(f"{text}\n\n{context}" if context else text)
        entry = as_dict(self._call("post_message", channel=SELF, text=body[:MAX_POST], thread_ts=thread))
        key = line(entry.get("ts"), 40)
        return SelfMessage(
            id=key, thread=optional(entry.get("thread_ts"), 40) or key, url=optional(entry.get("permalink"), 500)
        )

    def notify_self(self, text: str, *, thread: str | None = None, context: str | None = None) -> SelfMessage:
        """Tell the user `text` in their own direct messages, in `thread` when given (ADR 0160). Mode: write.

        Raises:
            HeinzelError: If the chat command fails, takes too long or answers no JSON object.
        """
        if self._command is None:
            return self._post_self(text, thread, context)
        told = self._command.tell(neutralised(text), thread, neutralised(context) if context else None)
        key = line(told.get("message"), 100)
        return SelfMessage(id=key, thread=optional(told.get("topic"), 100) or key)

    def ask_self(  # noqa: PLR0913 - the protocol's shape
        self,
        question: str,
        *,
        options: Sequence[str] = (),
        timeout: float,
        thread: str | None = None,
        context: str | None = None,
        cancel: threading.Event | None = None,
    ) -> SelfAnswer:
        """Ask the user `question` in their own direct messages and wait for the answer (ADR 0160). Mode: write.

        Raises:
            HeinzelError: If the chat command fails, takes too long, or answers a choice that wasn't offered.
        """
        if self._command is not None:
            return self._ask_command(
                question, options=options, timeout=timeout, thread=thread, context=context, cancel=cancel
            )
        listed = "\n".join(f"- {option}" for option in options)
        asked = self._post_self(f"{question}\n{listed}" if listed else question, thread, context)
        if options:
            return SelfAnswer(thread=asked.thread, option=options[0])
        (cancel or threading.Event()).wait(max(0.0, timeout))
        return SelfAnswer(thread=asked.thread, timed_out=True)

    def _ask_command(  # noqa: PLR0913 - the question's parts
        self,
        question: str,
        *,
        options: Sequence[str],
        timeout: float,
        thread: str | None,
        context: str | None,
        cancel: threading.Event | None,
    ) -> SelfAnswer:
        assert self._command is not None  # noqa: S101 - only called with a command
        note = neutralised(context) if context else None
        answer = self._command.question(
            neutralised(question), choices=options, wait=max(0.0, timeout), topic=thread, note=note, cancel=cancel
        )
        if answer is None or answer.get("expired") is True:
            return SelfAnswer(thread=optional((answer or {}).get("topic"), 100) or thread, timed_out=True)
        topic = optional(answer.get("topic"), 100)
        if "choice" in answer:
            choice = line(answer.get("choice"), 200)
            if choice not in options:
                msg = f"The chat command answered {choice!r}, which wasn't one of the choices offered."
                raise HeinzelError(msg)
            return SelfAnswer(thread=topic, option=choice)
        reply = text(answer.get("reply"))
        if not reply:
            msg = "The chat command answered neither a choice, a reply nor an expired wait."
            raise HeinzelError(msg)
        return SelfAnswer(thread=topic, text=reply)
