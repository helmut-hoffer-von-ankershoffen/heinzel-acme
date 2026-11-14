"""The chat command backend: `acme-chat` and the chat adapter that runs it, in real subprocesses. Offline."""

import json
import sys
import threading
import tracemalloc
from datetime import UTC, datetime

import pytest
from heinzel import HeinzelError, Window
from heinzel_acme_connectors import AcmeChat, NotSupportedError
from heinzel_acme_connectors._chat_command import MAX_OUTPUT, ChatCommand
from heinzel_acme_connectors._settings import ACME_CHAT, ConnectorSettings
from heinzel_acme_connectors.acme_chat import main

pytestmark = pytest.mark.integration

WEEK = Window(since=datetime(2026, 11, 1, tzinfo=UTC), until=datetime(2026, 11, 8, tzinfo=UTC))


def python(code: str) -> list[str]:
    """A chat command that runs `code`."""
    return [sys.executable, "-c", code]


def chat(command: list[str] | None = None, timeout: float = 5) -> AcmeChat:
    settings = ConnectorSettings(chat_backend="command", chat_command=command or list(ACME_CHAT), chat_timeout=timeout)
    return AcmeChat(settings)


def test_acme_chat_tells_and_answers_from_its_fixture(capsys, monkeypatch, tmp_path):
    assert main(["tell", "--topic=t-1", "--", "Draft ready"]) == 0
    told = json.loads(capsys.readouterr().out)
    assert told == {"message": told["message"], "topic": "t-1"}
    assert told["message"].startswith("msg-")

    monkeypatch.setenv("ACME_CHAT_ANSWER", '{"choice": "Yes"}')
    assert main(["question", "--choice=Yes", "--choice=No", "--", "Send it?"]) == 0
    assert json.loads(capsys.readouterr().out)["choice"] == "Yes"

    table = tmp_path / "answers.json"
    table.write_text(json.dumps({"anything": {"reply": "Ship on Thursday"}}), encoding="utf-8")
    monkeypatch.delenv("ACME_CHAT_ANSWER")
    monkeypatch.setenv("ACME_CHAT_ANSWERS", str(table))
    assert main(["question", "--", "Anything to add?"]) == 0
    assert json.loads(capsys.readouterr().out)["reply"] == "Ship on Thursday"
    assert main(["question", "--wait-seconds=30", "--", "Unasked?"]) == 0  # no answer: expires at once
    assert json.loads(capsys.readouterr().out)["expired"] is True


def test_acme_chat_refuses_an_answer_that_is_not_a_choice(capsys, monkeypatch):
    monkeypatch.setenv("ACME_CHAT_ANSWER", '{"choice": "Maybe"}')
    assert main(["question", "--choice=Yes", "--", "Send it?"]) == 2
    assert "'Maybe' is not one of the choices" in capsys.readouterr().err


def test_the_command_backend_tells_and_asks_through_acme_chat(monkeypatch):
    adapter = chat()
    assert adapter.unsupported == frozenset({"messages", "post"})
    told = adapter.notify_self("Draft ready <!here>", thread="t-7", context="from the weekly report")
    assert told.thread == "t-7"
    assert told.id.startswith("msg-")
    monkeypatch.setenv("ACME_CHAT_ANSWER", '{"choice": "Send"}')
    answer = adapter.ask_self("Send it?", options=["Send", "Wait"], timeout=1, thread="t-7")
    assert (answer.option, answer.thread, answer.timed_out) == ("Send", "t-7", False)
    monkeypatch.setenv("ACME_CHAT_ANSWER", '{"reply": "Add the crash numbers"}')
    assert adapter.ask_self("Anything to add?", timeout=1).text == "Add the crash numbers"
    monkeypatch.delenv("ACME_CHAT_ANSWER")
    assert adapter.ask_self("Still there?", timeout=1).timed_out


def test_the_command_backend_reads_no_channels():
    adapter = chat()
    with pytest.raises(NotSupportedError, match="can't messages: the chat command only tells and asks you"):
        adapter.messages("#checkout", WEEK)
    with pytest.raises(NotSupportedError, match="can't post: the chat command only tells and asks you"):
        adapter.post("#checkout", "hi")


def test_a_choice_that_was_not_offered_is_an_error():
    adapter = chat(python('print(\'{"message": "m", "topic": "t", "choice": "Later"}\')'))
    with pytest.raises(HeinzelError, match="answered 'Later', which wasn't one of the choices offered"):
        adapter.ask_self("Send it?", options=["Send", "Wait"], timeout=1)


def test_an_answer_with_nothing_in_it_is_an_error():
    with pytest.raises(HeinzelError, match="neither a choice, a reply nor an expired wait"):
        chat(python('print(\'{"message": "m"}\')')).ask_self("Hm?", timeout=1)


def test_a_command_that_takes_too_long_is_stopped():
    with pytest.raises(HeinzelError, match=r"took longer than 0\.3 seconds and was stopped"):
        ChatCommand(python("import time; time.sleep(30)"), timeout=0.3).tell("hi", None, None)


def test_a_question_is_given_up_when_cancelled():
    cancel = threading.Event()
    cancel.set()
    answer = chat(python("import time; time.sleep(30)")).ask_self("Hm?", timeout=20, cancel=cancel)
    assert answer.timed_out


@pytest.mark.parametrize(
    ("code", "error"),
    [
        ("print('not json')", "answered no JSON: 'not json'"),
        ("print('[1, 2]')", "answered JSON that is no object"),
        (f"print('x' * {MAX_OUTPUT + 1})", "answered more than 64 KiB"),
        ("import sys; sys.stderr.write('first\\nsign in again\\n'); sys.exit(3)", r"failed \(exit 3\): sign in again"),
        ("import sys; sys.exit(4)", r"failed \(exit 4\)\."),
    ],
)
def test_a_bad_answer_or_exit_is_a_clear_error(code, error):
    with pytest.raises(HeinzelError, match=error):
        chat(python(code)).notify_self("hi")


def test_a_missing_command_says_which_setting_to_fix():
    with pytest.raises(HeinzelError, match=r"Can't run acme-chat: .*Check acme-connectors\.chat_command"):
        chat(["/nonexistent/acme-chat"]).notify_self("hi")


def test_text_that_looks_like_an_option_stays_text(capsys):
    assert main(["tell", "--", "--topic=sneaky"]) == 0
    assert json.loads(capsys.readouterr().out)["topic"].startswith("msg-")
    told = chat().notify_self("--note=sneaky")
    assert told.thread == told.id


def test_a_huge_answer_stops_the_command_while_reading_and_memory_stays_bounded():
    endless = python("import sys\nwhile True:\n    sys.stdout.write('x' * 65536)")
    tracemalloc.start()
    try:
        with pytest.raises(HeinzelError, match="answered more than 64 KiB and was stopped"):
            ChatCommand(endless, timeout=10).tell("hi", None, None)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 1_000_000, f"reading took {peak:,} bytes"


def test_a_flood_on_stderr_keeps_only_its_end_and_still_names_the_last_line():
    flood = python(
        "import sys\nsys.stderr.write('noise\\n' * 4_000_000)\nsys.stderr.write('sign in again\\n')\nsys.exit(5)"
    )
    tracemalloc.start()
    try:
        with pytest.raises(HeinzelError, match=r"failed \(exit 5\): sign in again"):
            ChatCommand(flood, timeout=10).tell("hi", None, None)
        _, peak = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()
    assert peak < 1_000_000, f"reading took {peak:,} bytes"


def test_the_command_sees_only_the_basics_of_the_environment(monkeypatch):
    monkeypatch.setenv("PROVIDER_API_KEY", "fictional-key")
    monkeypatch.setenv("ACME_CHAT_ANSWER", '{"reply": "x"}')
    shows = python("import json, os\nprint(json.dumps({'message': 'm', 'topic': ' '.join(sorted(os.environ))}))")
    seen = set(chat(shows).notify_self("hi").thread.split())
    assert "PROVIDER_API_KEY" not in seen
    assert {"ACME_CHAT_ANSWER", "PATH"} <= seen


def test_the_bundled_command_is_named_acme_chat_in_errors(monkeypatch):
    monkeypatch.setenv("ACME_CHAT_ANSWER", "not json")
    with pytest.raises(HeinzelError, match=r"^acme-chat failed \(exit 1\)"):
        chat().ask_self("Send it?", options=["Yes"], timeout=1)
