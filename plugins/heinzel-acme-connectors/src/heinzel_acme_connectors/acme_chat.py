"""`acme-chat`: a fictional command-line chat tool that tells the user something or asks them, as JSON.

It stands in for a company's own chat command, so the chat adapter of heinzel-acme-connectors can show how to drive
one: an argument list, no shell, a timeout and a bounded JSON answer. It talks to nobody. Answers to questions come
from a fixture:

- `ACME_CHAT_ANSWER`: one JSON object used for every question, `{"choice": "Yes"}` or `{"reply": "text"}`;
- `ACME_CHAT_ANSWERS`: the path of a JSON file mapping a word in the question to such an object.

Without an answer it waits `--wait-seconds`, at most `ACME_CHAT_MAX_WAIT` seconds (0 unless set, so it never
blocks for real), and reports that the wait ran out. Usage:

    acme-chat tell TEXT [--topic ID] [--note TEXT]
    acme-chat question TEXT [--choice A --choice B ...] [--wait-seconds N] [--topic ID] [--note TEXT]

Both print one JSON object: `{"message": ID, "topic": ID}`, plus for a question `"choice"`, `"reply"` or
`"expired": true`. Exit 2 for wrong usage or an answer that isn't one of the choices.
"""

import argparse
import hashlib
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, cast


def _message_id(*parts: str) -> str:
    return "msg-" + hashlib.sha256("\x1f".join(parts).encode()).hexdigest()[:12]


def _answer(question: str) -> dict[str, Any] | None:
    one = os.environ.get("ACME_CHAT_ANSWER")
    if one:
        return cast("dict[str, Any]", json.loads(one))
    path = os.environ.get("ACME_CHAT_ANSWERS")
    if path:
        table = cast("dict[str, dict[str, Any]]", json.loads(Path(path).read_text(encoding="utf-8")))
        return next((answer for word, answer in table.items() if word.casefold() in question.casefold()), None)
    return None


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="acme-chat", description="Tell or ask yourself something (fictional).")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("tell", "question"):
        command = commands.add_parser(name)
        command.add_argument("text")
        command.add_argument("--topic", default=None, help="Continue this conversation.")
        command.add_argument("--note", default=None, help="A line of background under the text.")
        if name == "question":
            command.add_argument("--choice", action="append", default=[], help="An answer to offer; repeat.")
            command.add_argument("--wait-seconds", type=float, default=0.0, help="How long to wait for an answer.")
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run one command and print its JSON answer; the exit code says whether it worked."""
    args = _parser().parse_args(argv)
    message = _message_id(args.command, args.text, args.topic or "", args.note or "")
    result: dict[str, Any] = {"message": message, "topic": args.topic or message}
    if args.command == "question":
        answer = _answer(args.text)
        if answer is None:
            time.sleep(max(0.0, min(args.wait_seconds, float(os.environ.get("ACME_CHAT_MAX_WAIT", "0")))))
            result["expired"] = True
        elif "choice" in answer:
            if args.choice and answer["choice"] not in args.choice:
                print(f"acme-chat: {answer['choice']!r} is not one of the choices", file=sys.stderr)  # noqa: T201 - a CLI
                return 2
            result["choice"] = answer["choice"]
        else:
            result["reply"] = str(answer.get("reply", ""))
    print(json.dumps(result))  # noqa: T201 - a CLI answers on stdout
    return 0


if __name__ == "__main__":  # pragma: no cover - run as `python -m heinzel_acme_connectors.acme_chat`
    sys.exit(main())
