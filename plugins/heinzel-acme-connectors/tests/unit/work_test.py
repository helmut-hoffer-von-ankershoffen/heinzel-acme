"""The Atlassian-style adapters (documents and tracker), chat, meetings, code host and directory on the dummy week."""

import threading

import pytest
from heinzel import HeinzelError
from heinzel_acme_connectors import (
    AcmeChat,
    AcmeCodeHost,
    AcmeDirectory,
    AcmeDocs,
    AcmeMeetings,
    AcmeTracker,
    AcmeWiki,
    NotSupportedError,
)
from heinzel_acme_connectors._chat import MAX_POST, neutralised

pytestmark = pytest.mark.unit


def test_the_drive_reads_its_links_and_ids():
    docs = AcmeDocs()
    by_id = docs.read("doc-roadmap")
    assert (by_id.title, by_id.revision, by_id.url) == ("Roadmap 2027", "7", "https://docs.acme.example/d/doc-roadmap")
    assert "Ship the reading list" in by_id.text
    assert docs.read("https://docs.acme.example/d/doc-onboarding").text == "Welcome to ACME."


def test_the_wiki_reads_its_links_and_page_ids():
    wiki = AcmeWiki()
    page = wiki.read("https://wiki.acme.example/pages/10002")
    assert (page.ref, page.title, page.revision) == ("https://wiki.acme.example/pages/10002", "Release checklist", "3")
    assert page.text == "1. Freeze\n2. Test\n3. Ship"
    assert wiki.read("10001").title == "Team handbook"
    with pytest.raises(HeinzelError, match="No page '404'"):
        wiki.read("404")


@pytest.mark.parametrize(
    ("store", "ref"),
    [
        (AcmeDocs, "https://wiki.acme.example/pages/10002"),
        (AcmeDocs, "10002"),
        (AcmeDocs, "http://docs.acme.example/d/doc-roadmap"),
        (AcmeWiki, "https://docs.acme.example/d/doc-roadmap"),
        (AcmeWiki, "doc-roadmap"),
        (AcmeWiki, "https://evil.example/pages/10002"),
    ],
)
def test_each_store_refuses_the_other_stores_refs_and_foreign_links_without_a_call(store, ref):
    with pytest.raises(HeinzelError, match=f"is no document of https://{store.host}"):
        store(backend=Untouchable()).read(ref)


class Untouchable:
    def call(self, tool, arguments=None):
        msg = f"{tool} reached a store"
        raise AssertionError(msg)


def test_each_store_searches_itself_best_match_first():
    hits = AcmeDocs().search("roadmap", 5)
    assert [(h.ref, h.title, h.source) for h in hits] == [
        ("https://docs.acme.example/d/doc-roadmap", "Roadmap 2027", None)
    ]
    assert [h.title for h in AcmeWiki().search("release checklist", 5)] == ["Release checklist"]
    assert AcmeWiki().search("nothing like this", 5) == []
    assert len(AcmeDocs().search("acme roadmap welcome", 1)) == 1


@pytest.mark.parametrize("limit", [0, 51])
def test_a_search_limit_out_of_range_is_refused(limit):
    with pytest.raises(HeinzelError, match=f"Ask for 1 to 50 documents, not {limit}"):
        AcmeDocs(backend=Untouchable()).search("roadmap", limit)


def test_tracker_lists_issues_updated_in_the_window(week):
    issues = AcmeTracker().issues_updated("CHK", week)
    assert [(i.key, i.state, i.assignee) for i in issues] == [
        ("CHK-1", "To Do", None),
        ("CHK-2", "In Progress", "Tomas Leal"),
    ]
    assert issues[1].attachments[0].model_dump() == {
        "name": "notes.md",
        "media_type": "text/markdown",
        "size": 812,
        "ref": "att-9",
    }


def test_tracker_writes_name_their_actor():
    tracker = AcmeTracker()
    made = tracker.create("CHK", "Dark mode", "Please add it.", "Nadia Moreira", ["ui"])
    assert (made.key, made.state, made.reporter, made.labels) == ("CHK-4", "To Do", "Nadia Moreira", ["ui"])
    claimed = tracker.claim("CHK-4", "Nadia Moreira")
    assert (claimed.assignee, claimed.state) == ("Nadia Moreira", "In Progress")
    assert tracker.claim("CHK-4", "Nadia Moreira").assignee == "Nadia Moreira"  # claiming your own again is fine
    assert tracker.transition("CHK-4", "In Review", "Nadia Moreira").state == "In Review"
    assert tracker.note("CHK-4", "Looks good.", "Nadia Moreira").key == "CHK-4"
    closed = tracker.close("CHK-4", "Nadia Moreira", "Shipped in 2.4")
    assert closed.state == "Done"
    assert closed.closed_at is not None


def test_a_claim_held_by_someone_else_is_refused():
    with pytest.raises(HeinzelError, match="CHK-2 is claimed by Tomas Leal; it stays theirs"):
        AcmeTracker().claim("CHK-2", "Nadia Moreira")


def test_chat_resolves_a_channel_name_and_lists_top_level_and_replies(week):
    listed = AcmeChat().messages("#Release", week)
    assert [(m.channel, m.text, m.thread, m.reply_count) for m in listed] == [
        ("C100", "2.4 is ready for review", None, 1),
        ("C100", "Thanks, looking now", "1762077600.000100", 0),
    ]
    assert listed[0].author.name == "Tomas Leal"
    assert [m.text for m in AcmeChat().messages("C200", week)] == ["Cake in the kitchen"]
    with pytest.raises(HeinzelError, match="No channel '#nope'"):
        AcmeChat().messages("#nope", week)


def test_a_post_pages_nobody_and_reads_back(week):
    chat = AcmeChat()
    posted = chat.post("#release", "<!here> <!channel|channel> @everyone ask <@U123|jonas>", thread="1762077600.000100")
    assert posted.channel == "C100"
    assert posted.thread == "1762077600.000100"
    assert posted.url == f"https://chat.acme.example/archives/C100/p{posted.id.replace('.', '')}"
    assert chat.messages("C100", week)[-1].text == "(everyone) (everyone) (everyone) ask (someone)"


def test_neutralising_keeps_ordinary_at_signs_and_a_long_post_is_cut():
    assert neutralised("mail nadia@acme.example at 9") == "mail nadia@acme.example at 9"
    posted = AcmeChat().post("C200", "x" * (MAX_POST + 10))
    assert posted.id


def test_meetings_list_both_and_transcribe_only_the_recorded_one(week):
    meetings = AcmeMeetings()
    ended = meetings.ended(week)
    assert [(m.id, m.has_transcript, m.conference_id) for m in ended] == [
        ("mt-1", True, "81234567890"),
        ("mt-2", False, None),
    ]
    assert [p.name for p in ended[0].participants] == ["Nadia Moreira", "Tomas Leal", "Priya Raman"]
    (transcript,) = meetings.transcripts(week)
    assert transcript.language == "en"
    assert [(s.speaker, s.offset_seconds, s.text) for s in transcript.segments] == [
        ("Nadia Moreira", 0.0, "Shall we ship 2.4?"),
        ("Tomas Leal", 12.5, "Yes, on Thursday."),
    ]
    assert meetings.transcript("mt-1") == transcript


def test_the_transcript_of_an_unrecorded_meeting_is_not_supported_and_an_unknown_one_an_error():
    with pytest.raises(NotSupportedError, match="can't transcript: only recorded meetings have a transcript"):
        AcmeMeetings().transcript("mt-2")
    with pytest.raises(HeinzelError, match="No meeting 'mt-9'"):
        AcmeMeetings().transcript("mt-9")


def test_a_gateway_that_answers_nothing_for_a_meeting_is_an_error():
    class Empty:
        def call(self, tool, arguments):
            from heinzel_acme_connectors._compat import McpResult

            return McpResult(text="{}", data={})

    with pytest.raises(HeinzelError, match=r"take Meeting\.id from `ended`"):
        AcmeMeetings(backend=Empty()).transcript("mt-1")


def test_code_host_lists_merged_pull_requests_of_one_repository(week):
    pulls = AcmeCodeHost().merged_pull_requests("acme/acme-checkout", week)
    assert [(p.number, p.title, p.author, p.labels) for p in pulls] == [
        (41, "Add the reading list", "tomas", ["feature"]),
        (42, "Fix a crash on older phones", "priya", ["bug"]),
    ]
    assert pulls[0].url == "https://code.acme.example/acme/acme-checkout/pull/41"


def test_directory_knows_people_by_login_or_email_with_their_reporting_lines():
    directory = AcmeDirectory()
    mira = directory.person("NADIA@acme.example")
    assert mira is not None
    assert (mira.login, mira.title, mira.team) == ("nadia", "Engineering Manager", "Reading")
    assert mira.manager is not None
    assert mira.manager.who.name == "Rui Almeida"
    assert [r.who.name for r in mira.reports] == ["Tomas Leal", "Priya Raman"]
    assert directory.person("nobody") is None
    assert [p.login for p in directory.reports("rui")] == ["nadia"]
    assert directory.reports("nobody") == []


def test_notify_self_posts_to_the_users_own_messages_with_mentions_neutralised(week):
    chat = AcmeChat()
    told = chat.notify_self("Draft ready <!here>", context="from the weekly summary")
    assert told.thread == told.id
    assert told.url == f"https://chat.acme.example/archives/D100/p{told.id.replace('.', '')}"
    assert chat.messages("D100", week)[-1].text == "Draft ready (everyone)\n\nfrom the weekly summary"
    assert chat.notify_self("again", thread=told.id).thread == told.id


def test_ask_self_answers_with_the_first_option_or_times_out_without_text():
    chat = AcmeChat()
    answer = chat.ask_self("Send it?", options=["yes", "no"], timeout=5)
    assert (answer.option, answer.timed_out, answer.text) == ("yes", False, "")
    cancel = threading.Event()
    cancel.set()
    waited = chat.ask_self("Anything to add?", timeout=30, cancel=cancel)
    assert (waited.timed_out, waited.text, waited.option) == (True, "", None)
    assert chat.ask_self("Quick?", timeout=0).timed_out
