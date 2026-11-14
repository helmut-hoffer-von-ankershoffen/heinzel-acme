"""Gateway answers are untrusted shapes: odd values become empty ones or clear errors, never a crash in a model."""

import pytest
from heinzel import HeinzelError
from heinzel_acme_connectors._base import MAX_ITEMS, bounded
from heinzel_acme_connectors._text import as_dict, as_list, line, moment, optional, text

pytestmark = pytest.mark.unit


def test_text_cleans_cuts_and_turns_non_strings_into_nothing():
    assert text("a\u202eb\u200bc\x07") == "abc"
    assert text("x" * 30, limit=10) == "x" * 9 + "…"
    assert text(42) == ""
    assert line("one\n  two\tthree") == "one two three"
    assert optional("") is None
    assert (as_dict([1]), as_list({"a": 1})) == ({}, [])


@pytest.mark.parametrize("value", [None, "yesterday", "2026-11-02T08:15:00"])
def test_a_timestamp_without_a_zone_or_not_a_timestamp_is_a_clear_error(value):
    with pytest.raises(HeinzelError, match="without a timestamp with a time zone"):
        moment(value, "a message")


def test_more_items_than_a_window_may_hold_asks_for_a_narrower_window():
    assert bounded(list(range(MAX_ITEMS)), "things") == list(range(MAX_ITEMS))
    with pytest.raises(HeinzelError, match=f"More than {MAX_ITEMS} things in this window; ask for a narrower window"):
        bounded(list(range(MAX_ITEMS + 1)), "things")
