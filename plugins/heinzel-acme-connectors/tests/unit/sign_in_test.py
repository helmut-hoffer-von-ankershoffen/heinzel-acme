"""How the connectors report that they are connected and signed in: every state of the dummy sign-in, and health."""

import threading

import pytest
from heinzel import SignInProvider, Status
from heinzel_acme_connectors import AcmeSignIn, health, health_live, module
from heinzel_acme_connectors._settings import ConnectorSettings
from heinzel_acme_connectors._sign_in import ACCOUNT, GRANTS

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def fresh():
    AcmeSignIn.state.clear()
    yield
    AcmeSignIn.state.clear()


def provider(state: str) -> AcmeSignIn:
    return AcmeSignIn(ConnectorSettings(sign_in_state=state))


def test_the_sign_in_is_declared_once_with_its_grants():
    (let,) = [let for let in module.lets if type(let).__name__ == "SignInLet"]
    assert let.factory is AcmeSignIn
    assert [(g.id, g.default) for g in let.grants] == [("read", True), ("write", False)]
    assert isinstance(provider("signed-in"), SignInProvider)


def test_signed_in_names_the_account_and_holds_every_grant():
    status = provider("signed-in").status(live=True)
    assert (status.signed_in, status.account, status.problem, status.live) == (True, ACCOUNT, "", True)
    assert [(g.grant.id, g.state, g.needed) for g in status.grants] == [
        ("read", "granted", True),
        ("write", "granted", False),
    ]


def test_signed_out_holds_nothing():
    status = provider("signed-out").status(live=False)
    assert (status.signed_in, status.account) == (False, "")
    assert {g.state for g in status.grants} == {"missing"}


def test_expired_names_the_problem_and_knows_no_grant():
    status = provider("expired").status(live=False)
    assert (status.signed_in, status.account) == (True, ACCOUNT)
    assert status.problem == "The ACME sign-in expired on 2026-11-13; sign in again."
    assert {g.state for g in status.grants} == {"unknown"}


def test_sign_in_reports_a_consent_page_at_acme_and_signs_in():
    pages = []
    outcome = provider("signed-out").sign_in(frozenset({"read", "write"}), pages.append, threading.Event())
    assert pages[0].url == "https://login.acme.example/consent?grants=read+write"
    assert pages[0].finish_on == "anywhere"
    assert (outcome.state, outcome.account) == ("succeeded", ACCOUNT)
    assert provider("signed-out").status(live=False).signed_in is True


def test_a_stopped_sign_in_changes_nothing():
    stop = threading.Event()
    stop.set()
    outcome = provider("signed-out").sign_in(frozenset({"read"}), lambda _: None, stop)
    assert outcome.state == "cancelled"
    assert provider("signed-out").status(live=False).signed_in is False


def test_sign_out_forgets_the_sign_in():
    assert "Signed out" in provider("signed-in").sign_out()
    assert provider("signed-in").status(live=False).signed_in is False


@pytest.mark.parametrize(
    ("state", "status", "detail"),
    [
        ("signed-in", Status.UP, f"signed in as {ACCOUNT}"),
        ("expired", Status.DEGRADED, "The ACME sign-in expired on 2026-11-13; sign in again."),
        ("signed-out", Status.DOWN, "not signed in"),
    ],
)
def test_the_offline_health_check_says_how_the_sign_in_stands(state, status, detail):
    launchers, sign_in = health(ConnectorSettings(sign_in_state=state))
    assert (launchers.name, launchers.status) == ("launchers", Status.UP)
    assert (sign_in.name, sign_in.status, sign_in.detail) == ("sign-in", status, detail)
    assert sign_in.login is not None
    assert (not sign_in.fix) == (state == "signed-in")


def test_the_live_check_starts_every_connector_only_when_signed_in():
    checks = health_live(ConnectorSettings())
    assert len(checks) == 9
    assert {c.status for c in checks} == {Status.UP}
    (refused,) = health_live(ConnectorSettings(sign_in_state="expired"))
    assert (refused.status, refused.detail) == (Status.DOWN, "not tested: expired")


def test_grants_are_plain_words():
    assert all(g.title and g.explanation for g in GRANTS)
