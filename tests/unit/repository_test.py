"""The repository keeps ADR 0040's rules for a company's plugins: one plugin per layer, named after its path,
depending on the layers above it, released together; a connector plugin (ADR 0004) is no layer and needs none."""

import tomllib
from pathlib import Path

import pytest

from heinzel_acme import layers

pytestmark = pytest.mark.unit

ROOT = Path(__file__).resolve().parents[2]


def tomls():
    paths = [ROOT / "pyproject.toml", *sorted((ROOT / "plugins").glob("*/pyproject.toml"))]
    return {p.parent: tomllib.loads(p.read_text(encoding="utf-8")) for p in paths}


def connector(data):
    return data.get("tool", {}).get("acme", {}).get("kind") == "connector"


def projects():
    """The layers: every plugin but the connector plugins."""
    return {path: data["project"] for path, data in tomls().items() if not connector(data)}


def connectors():
    return {path: data["project"] for path, data in tomls().items() if connector(data)}


def declared():
    import heinzel_acme_lisbon  # noqa: F401 - importing a plugin declares its layer
    import heinzel_acme_payments  # noqa: F401
    import heinzel_acme_payments_checkout  # noqa: F401

    return {layer.name: layer for layer in layers.declared()}


def test_every_plugin_is_a_layer_named_heinzel_and_its_path():
    found = declared()
    for project in projects().values():
        (module,) = project["entry-points"]["heinzel.modules"]
        assert project["name"] == f"heinzel-{module}"
        assert module in found


def test_every_plugin_depends_on_its_parent_and_site():
    found = declared()
    for project in projects().values():
        (module,) = project["entry-points"]["heinzel.modules"]
        layer = found[module]
        needed = {f"heinzel-{n}" for n in (layer.parent, layer.site) if n}
        names = {dependency.split(">")[0].split("=")[0].strip() for dependency in project["dependencies"]}
        assert needed <= names, module


def test_every_layer_is_released_with_the_same_version():
    assert len({project["version"] for project in [*projects().values(), *connectors().values()]}) == 1


def test_a_connector_plugin_is_named_after_its_module_declares_no_layer_and_needs_none():
    found = declared()
    assert connectors(), "heinzel-acme-connectors is the connector plugin"
    for project in connectors().values():
        (module,) = project["entry-points"]["heinzel.modules"]
        assert project["name"] == f"heinzel-{module}"
        assert module not in found
        names = {dependency.split(">")[0].split("=")[0].strip() for dependency in project["dependencies"]}
        assert names == {"heinzel"}, "a connector serves every layer and depends on none"


def test_the_layer_api_is_reached_only_through_the_bridge():
    calls = [
        path
        for path in [*ROOT.glob("src/**/*.py"), *ROOT.glob("plugins/*/src/**/*.py")]
        if ".layer(" in path.read_text(encoding="utf-8") and path.name != "layers.py"
    ]
    assert calls == []
