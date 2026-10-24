import pytest

pytestmark = pytest.mark.integration


def test_info_places_the_team_under_its_org_at_its_site(hz):
    about = hz("acme-payments-checkout", "info").json
    assert about["layer"]["parent"] == "acme-payments"
    assert about["layer"]["site"] == "acme-lisbon"
    assert about["layer"]["stack"] == ["acme", "acme-payments", "acme-lisbon", "acme-payments-checkout"]
    assert "weekly-report" in about["draft_tags"]
