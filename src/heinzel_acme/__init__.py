"""ACME, a made-up company: the root layer of Heinzelmännchen's reference company (ADR 0040 of the core).

The company layer brings what every ACME team shares: how ACME reaches its tools (capability bindings to the
first-party adapters, all through vendor CLIs as an ordinary employee), the roles ACME adds to the core's vocabulary,
and a doctor check for both. Its org, site and team are their own plugins in this repository: `acme-payments`,
`acme-lisbon` and `acme-payments-checkout`. `hz acme seed` (rehearsal only) writes the made-up world into your own
trial accounts.
"""

from pathlib import Path

from heinzel import Check, Module

from heinzel_acme import layers
from heinzel_acme._bindings import BINDINGS, recommended
from heinzel_acme._models import AcmeAbout, LayerAbout, LayerList, LayerView
from heinzel_acme._service import AcmeService, about_layer

module = Module("acme", "ACME, a made-up company: its tool bindings, roles and layer tree.")
layers.declare(module, roles=["tech-lead", "report-owner"])
module.service(AcmeService)
module.theme(Path(__file__).parent / "themes")
module.soundscape(Path(__file__).parent / "soundscapes")
module.playbook(
    "How ACME reaches its tools: GitHub through gh, Jira through acli, Google Workspace through gws, Zoom summaries.",
    defaults=recommended(),
)


@module.operation
def info(service: AcmeService) -> AcmeAbout:
    """Show this plugin, its place in ACME's tree, and the bindings it recommends and how they stand."""
    return service.about()


@module.operation(name="layers")
def layer_tree(service: AcmeService) -> LayerList:
    """Show ACME's installed layers, root first, with each one's stack, and what is missing."""
    return service.layers()


@module.info
def system_info(service: AcmeService) -> AcmeAbout:
    """Contribute this plugin's details to `hz system info`."""
    return service.about()


@module.health
def health(service: AcmeService) -> list[Check]:
    """Missing ACME layers, and whether each binding ACME recommends is installed and bound."""
    return service.checks()


__all__ = ["BINDINGS", "AcmeAbout", "AcmeService", "LayerAbout", "LayerList", "LayerView", "about_layer", "module"]
