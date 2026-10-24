import pytest

pytestmark = pytest.mark.integration


def test_info_places_the_site_under_the_company(hz):
    layer = hz("acme-lisbon", "info").json["layer"]
    assert layer["parent"] == "acme"
    assert layer["label"] == "site"


def test_the_time_zone_is_a_setting_of_the_site(hz, monkeypatch):
    monkeypatch.setenv("HZ_ACME_LISBON__TIME_ZONE", "Atlantic/Azores")
    assert hz("acme-lisbon", "calendar").json["calendar"]["time_zone"] == "Atlantic/Azores"
