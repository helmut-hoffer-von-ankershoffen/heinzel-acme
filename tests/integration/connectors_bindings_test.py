"""With ACME's recommended bindings set, installing heinzel-acme-connectors changes none of them. Offline."""

import json

import pytest
from heinzel.kernel import Config, Kernel, Settings, discover
from typer.testing import CliRunner

from heinzel_acme._bindings import BINDINGS

pytestmark = pytest.mark.integration


def connector_report(monkeypatch, bindings: dict[str, str]) -> dict[str, dict[str, object]]:
    from heinzel.heads.cli import build

    for capability, adapter in bindings.items():
        monkeypatch.setenv(f"HZ_CAPABILITIES__{capability.upper().replace('-', '_')}", adapter)
    config = Config.empty()
    records, errors = discover()
    kernel = Kernel(config.settings(Settings, "hz"), records, errors, config)
    result = CliRunner().invoke(build(kernel), ["system", "connector", "list", "--json"])
    assert result.exit_code == 0, result.output
    return {row["capability"]: row for row in json.loads(result.output)["capabilities"]}


def test_acmes_recommended_bindings_stay_with_the_first_party_plugins(monkeypatch):
    recommended = {binding.capability: binding.adapter for binding in BINDINGS}
    report = connector_report(monkeypatch, recommended)
    for capability, adapter in recommended.items():
        row = report[capability]
        assert (row["bound"], row["how"]) == (adapter, "configured"), capability
        offered = {candidate["adapter"] for candidate in row["candidates"]}
        assert offered & {"acme-connectors", "acme-connectors-docs"}, f"{capability}: offered as an alternative"


def test_a_capability_nothing_binds_is_served_by_its_only_adapter(monkeypatch):
    report = connector_report(monkeypatch, {binding.capability: binding.adapter for binding in BINDINGS})
    assert (report["chat"]["bound"], report["chat"]["how"]) == ("acme-connectors", "automatic")
