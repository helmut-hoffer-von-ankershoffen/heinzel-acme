"""The chat command backend: tell and ask the user through a command-line chat tool such as `acme-chat`.

The command runs with an argument list, never a shell; with a timeout; with nothing on stdin. Its answer is one JSON
object on stdout, read only up to `MAX_OUTPUT` bytes; a non-zero exit, a timeout or anything but that object is a
`HeinzelError` that says which. What the answer says is data from outside this process: it is cleaned like every
other gateway string.
"""

import json
import subprocess
import threading
import time
from collections.abc import Sequence
from typing import Any

from heinzel import HeinzelError

from heinzel_acme_connectors._text import as_dict, line
from heinzel_acme_connectors._text import text as clean

MAX_OUTPUT = 64 * 1024
"""Bytes of a command's answer read; a longer answer is refused, not cut."""
POLL = 0.1
"""Seconds between looks at `cancel` while a question waits."""


class ChatCommand:
    """One chat command, e.g. `acme-chat` or `python -m heinzel_acme_connectors.acme_chat`."""

    def __init__(self, command: Sequence[str], timeout: float) -> None:
        """Run `command` (the program and its first arguments) with `timeout` seconds of its own to spare."""
        self._command = list(command)
        self._timeout = timeout

    def tell(self, text: str, topic: str | None, note: str | None) -> dict[str, Any]:
        """Tell the user `text`; the answer names the message and its topic.

        Raises:
            HeinzelError: If the command fails, takes too long or answers no JSON object.
        """
        return self._run(["tell", *_options(topic, note), "--", text], self._timeout, None) or {}

    def question(  # noqa: PLR0913 - what one question carries
        self,
        text: str,
        *,
        choices: Sequence[str],
        wait: float,
        topic: str | None,
        note: str | None,
        cancel: threading.Event | None,
    ) -> dict[str, Any] | None:
        """Ask the user `text`; the answer, or None when `cancel` was set first.

        Raises:
            HeinzelError: If the command fails, takes longer than `wait` plus its own timeout, or answers no object.
        """
        options = [*(f"--choice={choice}" for choice in choices), f"--wait-seconds={wait:g}", *_options(topic, note)]
        return self._run(["question", *options, "--", text], wait + self._timeout, cancel)

    def _run(self, arguments: list[str], limit: float, cancel: threading.Event | None) -> dict[str, Any] | None:
        name = self._command[0] if self._command else "the chat command"
        try:
            process = subprocess.Popen(  # noqa: S603 - an argument list from the user's own settings, no shell
                [*self._command, *arguments],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        except OSError as exc:
            msg = f"Can't run {name}: {exc.strerror or exc}. Check acme-connectors.chat_command."
            raise HeinzelError(msg) from exc
        deadline = time.monotonic() + limit
        while True:
            try:
                out, err = process.communicate(timeout=POLL)
                break
            except subprocess.TimeoutExpired:
                if cancel is not None and cancel.is_set():
                    _stop(process)
                    return None
                if time.monotonic() >= deadline:
                    _stop(process)
                    msg = f"{name} took longer than {limit:g} seconds and was stopped."
                    raise HeinzelError(msg) from None
        if process.returncode != 0:
            why = line(err.decode("utf-8", "replace").strip().splitlines()[-1], 300) if err.strip() else ""
            msg = f"{name} failed (exit {process.returncode})" + (f": {why}" if why else ".")
            raise HeinzelError(msg)
        if len(out) > MAX_OUTPUT:
            msg = f"{name} answered more than {MAX_OUTPUT // 1024} KiB; a chat answer is one short JSON object."
            raise HeinzelError(msg)
        try:
            answer = json.loads(out.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            msg = f"{name} answered no JSON: {clean(out.decode('utf-8', 'replace'), 120)!r}"
            raise HeinzelError(msg) from exc
        found = as_dict(answer)
        if not found and answer != {}:
            msg = f"{name} answered JSON that is no object."
            raise HeinzelError(msg)
        return found


def _options(topic: str | None, note: str | None) -> list[str]:
    # `--name=value`, and the text after `--`: a value that starts with a dash is never read as an option.
    return [*([f"--topic={topic}"] if topic else []), *([f"--note={note}"] if note else [])]


def _stop(process: subprocess.Popen[bytes]) -> None:
    process.kill()
    process.communicate()
