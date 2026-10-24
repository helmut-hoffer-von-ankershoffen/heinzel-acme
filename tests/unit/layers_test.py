import pytest
from heinzel import Module

from heinzel_acme import layers

pytestmark = pytest.mark.unit


@pytest.fixture(autouse=True)
def fresh(monkeypatch):
    monkeypatch.setattr(layers, "_DECLARED", {})


def tree():
    layers.declare(Module("acme", "The company."), roles=["tech-lead"])
    layers.declare(Module("acme-payments", "An org."), parent="acme")
    layers.declare(Module("acme-lisbon", "A site."), parent="acme")
    layers.declare(Module("acme-payments-checkout", "A team."), parent="acme-payments", site="acme-lisbon")


def test_stack_runs_general_to_specific_with_the_site_before_the_team():
    tree()
    assert layers.stack("acme-payments-checkout") == ["acme", "acme-payments", "acme-lisbon", "acme-payments-checkout"]
    assert layers.stack("acme-payments") == ["acme", "acme-payments"]
    assert layers.stack("acme") == ["acme"]


def test_labels_come_from_where_a_layer_sits():
    tree()
    labels = {layer.name: layers.label(layer) for layer in layers.declared()}
    assert labels == {
        "acme": "company",
        "acme-payments": "org",
        "acme-lisbon": "site",
        "acme-payments-checkout": "team",
    }


def test_declared_lists_the_root_first():
    tree()
    assert next(layer.name for layer in layers.declared()) == "acme"


def test_a_missing_parent_or_site_has_no_stack():
    layers.declare(Module("acme-payments-checkout", "A team."), parent="acme-payments", site="acme-lisbon")
    with pytest.raises(KeyError):
        layers.stack("acme-payments-checkout")


@pytest.mark.parametrize(
    ("name", "parent", "site"),
    [
        ("checkout", "acme-payments", None),  # not named after its path
        ("acme-payments", "acme-payments", None),  # its own parent
        ("acme-x", "acme", "acme"),  # its site is its parent
        ("acme-x", "acme", "Lisbon"),  # not a layer name
    ],
)
def test_declarations_that_break_the_rules_are_refused(name, parent, site):
    with pytest.raises(ValueError, match=r"(?i)layer"):
        layers.declare(Module(name, "A layer."), parent=parent, site=site)


def test_a_core_with_the_layer_api_gets_the_declaration_too():
    taken = []

    class LayeredModule(Module):
        def layer(self, **declaration):
            taken.append(declaration)

    layer = layers.declare(LayeredModule("acme-payments", "An org."), parent="acme", roles=["lead"])
    assert taken == [{"parent": "acme", "site": None, "roles": ("lead",)}]
    assert layer.native


def test_without_the_layer_api_the_declaration_is_kept_here():
    class OlderModule(Module):
        layer = None  # a core before Module.layer

    layer = layers.declare(OlderModule("acme", "The company."))
    assert not layer.native
    assert layers.declared() == [layer]
