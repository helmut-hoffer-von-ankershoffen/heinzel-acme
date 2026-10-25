import pytest
from heinzel import Status

from heinzel_acme._service import AcmeService

pytestmark = pytest.mark.unit


class View:
    """What a CapabilityView answers, for given installed adapters and bindings."""

    def __init__(self, installed, bound):
        self._installed, self._bound = installed, bound

    def installed(self, capability):
        return self._installed.get(capability, [])

    def bound(self, capability):
        return self._bound.get(capability)


def checks(installed, bound):
    return {c.name.removeprefix("acme binding "): c for c in AcmeService(View(installed, bound)).checks()}


def test_a_missing_adapter_names_the_plugin_and_the_login():
    found = checks({}, {})["code-host"]
    assert found.status is Status.DEGRADED
    assert found.fix == "hz system plugin add github, then gh auth login"


def test_an_installed_adapter_nobody_bound_says_how_to_bind_it():
    found = checks({"tracker": ["atlassian"]}, {})["tracker"]
    assert found.status is Status.DEGRADED
    assert "hz setup acme" in found.fix


def test_the_persons_own_binding_wins_over_the_company():
    found = checks({"tracker": ["atlassian", "github"]}, {"tracker": "github"})["tracker"]
    assert found.status is Status.UP
    assert "you bound github" in found.detail


def test_the_recommended_binding_is_up():
    assert checks({"documents": ["google"]}, {"documents": "google"})["documents"].status is Status.UP


def test_about_lists_every_binding_and_what_it_brings():
    about = AcmeService(View({}, {})).about()
    assert about.plugin == "heinzel-acme"
    assert [b.capability for b in about.bindings][:2] == ["code-host", "tracker"]
    assert any("seed" in line for line in about.brings)
