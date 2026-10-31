import pytest

pytestmark = pytest.mark.integration


def test_info_places_the_site_under_the_company(hz):
    layer = hz("acme-lisbon", "info").json["layer"]
    assert layer["parent"] == "acme"
    assert layer["label"] == "site"


def test_the_time_zone_is_a_setting_of_the_site(hz, monkeypatch):
    monkeypatch.setenv("HZ_ACME_LISBON__TIME_ZONE", "Atlantic/Azores")
    assert hz("acme-lisbon", "calendar").json["calendar"]["time_zone"] == "Atlantic/Azores"


def test_calendar_is_readable_in_the_cli_and_preserves_structured_output(hz):
    result = hz("acme-lisbon", "calendar", "--days", "1", json=False)
    assert result.exit_code == 0
    for text in ("Lisbon's weekly rhythm", "Coming up", "Europe/Lisbon", "Weekly report", "17:00"):
        assert text in result.output
    assert hz("acme-lisbon", "calendar", "--days", "1").json["calendar"]["working_hours"] == ["09:00:00", "18:00:00"]
