from datetime import UTC, datetime, time
from zoneinfo import ZoneInfo

import pytest
from heinzel_acme_lisbon import LISBON, upcoming

pytestmark = pytest.mark.unit


def deadlines(start, days):
    return [o for o in upcoming(LISBON, start, days) if o.name == "Weekly report draft ready"]


def test_the_report_deadline_is_friday_17_lisbon_time_across_the_clock_change():
    # Lisbon leaves summer time on Sunday 25 October 2026: 17:00 is 16:00 UTC before and 17:00 UTC after.
    found = deadlines(datetime(2026, 10, 19, tzinfo=UTC), 14)
    assert [o.site_time.isoformat() for o in found] == ["2026-10-23T17:00:00+01:00", "2026-10-30T17:00:00+00:00"]
    assert [o.local_time.hour for o in found] == [16, 17]


def test_local_times_are_in_the_zone_of_the_start():
    berlin = datetime(2026, 10, 19, 8, 0, tzinfo=ZoneInfo("Europe/Berlin"))
    deadline = deadlines(berlin, 7)[0]
    assert deadline.local_time.hour == 18
    assert deadline.local_time.utcoffset() == berlin.utcoffset()


def test_occurrences_are_in_the_window_and_in_order():
    start = datetime(2026, 10, 21, 12, 0, tzinfo=UTC)  # a Wednesday noon
    found = upcoming(LISBON, start, 2)
    assert all(start <= o.site_time for o in found)
    assert found == sorted(found, key=lambda o: o.site_time)
    assert "Planning" not in {o.name for o in found}


def test_the_site_works_monday_to_friday_nine_to_six():
    assert LISBON.working_days == ["MON", "TUE", "WED", "THU", "FRI"]
    assert LISBON.working_hours == (time(9), time(18))
