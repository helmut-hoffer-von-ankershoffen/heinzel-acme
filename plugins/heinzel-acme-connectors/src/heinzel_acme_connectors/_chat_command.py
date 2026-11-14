"""The chat command backend: tell and ask the user through a command-line chat tool such as `acme-chat`.

The command runs with an argument list, never a shell; with a timeout; with nothing on stdin; with only the basics of
hz's environment. Its answer is one JSON object on stdout. Both streams are read as they come, stdout up to
`MAX_OUTPUT` bytes (more stops the command) and the last `STDERR_KEPT` bytes of stderr, so memory stays bounded
however much the command writes. A non-zero exit, a timeout or anything but that object is a `HeinzelError` that says
which. What the answer says is data from outside this process: it is cleaned like every
other gateway string.
"""

import json
import os
import selectors
import subprocess
import threading
import time
from collections.abc import Sequence
from typing import Any

from heinzel import HeinzelError

from heinzel_acme_connectors._settings import ACME_CHAT
from heinzel_acme_connectors._text import as_dict, line
from heinzel_acme_connectors._text import text as clean

MAX_OUTPUT = 64 * 1024
"""Bytes of a command's answer read; a longer answer stops the command and is refused, not cut."""
STDERR_KEPT = 4 * 1024
"""Bytes of a command's stderr kept, the last ones: its last line says why it failed."""
CHUNK = 8 * 1024
"""Bytes read at a time, so memory never exceeds the limits by more than this."""
ENVIRONMENT = frozenset({"PATH", "HOME", "LANG", "LC_ALL", "LC_CTYPE", "TMPDIR", "SYSTEMROOT"})
"""The variables of hz's environment a chat command gets, besides `ACME_CHAT_*`."""
POLL = 0.1
"""Seconds between looks at `cancel` while a question waits."""


class ChatCommand:
    """One chat command, e.g. `acme-chat` or `python -m heinzel_acme_connectors.acme_chat`."""

    def __init__(self, command: Sequence[str], timeout: float) -> None:
        """Run `command` (the program and its first arguments) with `timeout` seconds of its own to spare."""
        self._command = list(command)
        self._timeout = timeout
        bundled = self._command == list(ACME_CHAT)
        self._label = "acme-chat" if bundled else (self._command[0].rsplit("/", 1)[-1] if self._command else "?")

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
        name = self._label
        try:
            process = subprocess.Popen(  # noqa: S603 - an argument list from the user's own settings, no shell
                [*self._command, *arguments],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                env=_environment(),
            )
        except OSError as exc:
            msg = f"Can't run {name}: {exc.strerror or exc}. Check acme-connectors.chat_command."
            raise HeinzelError(msg) from exc
        try:
            read = _read(process, time.monotonic() + limit, cancel)
        except _TooLongError:
            msg = f"{name} took longer than {limit:g} seconds and was stopped."
            raise HeinzelError(msg) from None
        except _TooMuchError:
            msg = f"{name} answered more than {MAX_OUTPUT // 1024} KiB and was stopped; a chat answer is short JSON."
            raise HeinzelError(msg) from None
        finally:
            _reap(process)
        if read is None:
            return None
        out, err = read
        if process.returncode != 0:
            lines = err.decode("utf-8", "replace").strip().splitlines()
            why = line(lines[-1], 300) if lines else ""
            msg = f"{name} failed (exit {process.returncode})" + (f": {why}" if why else ".")
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


class _TooLongError(Exception):
    pass


class _TooMuchError(Exception):
    pass


def _read(
    process: subprocess.Popen[bytes], deadline: float, cancel: threading.Event | None
) -> tuple[bytes, bytes] | None:
    """Stdout (at most `MAX_OUTPUT` bytes) and the last `STDERR_KEPT` bytes of stderr, read as they come.

    Memory stays bounded however much the command writes: nothing is kept past the limits. None when `cancel` is set
    first.

    Raises:
        _TooLongError: If `deadline` passes first.
        _TooMuchError: If stdout passes `MAX_OUTPUT`.
    """
    out, err = bytearray(), bytearray()
    with selectors.DefaultSelector() as streams:
        streams.register(process.stdout, selectors.EVENT_READ, "out")  # type: ignore[arg-type]
        streams.register(process.stderr, selectors.EVENT_READ, "err")  # type: ignore[arg-type]
        while streams.get_map():
            if _given_up(cancel, deadline):
                return None
            for key, _ in streams.select(POLL):
                chunk = os.read(key.fd, CHUNK)
                if not chunk:
                    streams.unregister(key.fileobj)
                elif key.data == "out":
                    out += chunk
                    if len(out) > MAX_OUTPUT:
                        raise _TooMuchError
                else:
                    err = (err + chunk)[-STDERR_KEPT:]
    while process.poll() is None:  # both streams closed; the exit follows
        if _given_up(cancel, deadline):
            return None
        time.sleep(POLL / 10)
    return bytes(out), bytes(err)


def _given_up(cancel: threading.Event | None, deadline: float) -> bool:
    """Whether the caller cancelled.

    Raises:
        _TooLongError: If `deadline` has passed.
    """
    if cancel is not None and cancel.is_set():
        return True
    if time.monotonic() >= deadline:
        raise _TooLongError
    return False


def _reap(process: subprocess.Popen[bytes]) -> None:
    if process.poll() is None:
        process.kill()
    process.wait()
    for stream in (process.stdout, process.stderr):
        if stream is not None:
            stream.close()


def _environment() -> dict[str, str]:
    """What the chat command sees of hz's environment: the basics and its own `ACME_CHAT_*` variables, nothing else.

    hz's environment can hold keys of model providers and other tools; a chat command needs none of them.
    """
    return {k: v for k, v in os.environ.items() if k in ENVIRONMENT or k.startswith("ACME_CHAT_")}


def _options(topic: str | None, note: str | None) -> list[str]:
    # `--name=value`, and the text after `--`: a value that starts with a dash is never read as an option.
    return [*([f"--topic={topic}"] if topic else []), *([f"--note={note}"] if note else [])]
