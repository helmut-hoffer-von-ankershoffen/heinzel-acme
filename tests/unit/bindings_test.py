import tomllib
from pathlib import Path

import pytest
from heinzel import PlaybookLet
from heinzel.kernel import CAPABILITIES

from heinzel_acme import module
from heinzel_acme._bindings import BINDINGS, recommended

pytestmark = pytest.mark.unit


def test_every_binding_names_a_core_capability_once():
    capabilities = [binding.capability for binding in BINDINGS]
    assert len(capabilities) == len(set(capabilities))
    assert set(capabilities) <= set(CAPABILITIES) - {"agent-runner"}


def test_the_company_playbook_recommends_the_bindings():
    playbook = next(let for let in module.heinzel_lets() if isinstance(let, PlaybookLet))
    assert dict(playbook.defaults) == recommended()
    assert recommended()["capabilities.code_host"] == "github"
    assert recommended()["capabilities.meetings"] == "zoom"


def test_everything_goes_through_a_vendor_cli_or_mail():
    transports = {binding.adapter: binding.transport for binding in BINDINGS}
    assert "gh" in transports["github"]
    assert "acli" in transports["atlassian"]
    assert "gws" in transports["google"]
    assert "e-mails" in transports["zoom"]


def test_the_plugins_the_bindings_read_through_are_required_or_recommended():
    project = tomllib.loads((Path(__file__).resolve().parents[2] / "pyproject.toml").read_text(encoding="utf-8"))
    table = project["tool"]["heinzel"]["plugin"]
    required = {f"heinzel-{b.plugin}" for b in BINDINGS if b.capability in {"code-host", "tracker"}}
    assert set(table["requires-plugins"]) == required
    assert set(table["recommends-plugins"]) == {f"heinzel-{b.plugin}" for b in BINDINGS} - required
