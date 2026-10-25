import pytest

pytestmark = pytest.mark.integration


def test_info_places_the_org_under_the_company(hz):
    about = hz("acme-payments", "info").json
    assert about["layer"]["parent"] == "acme"
    assert about["layer"]["label"] == "org"
