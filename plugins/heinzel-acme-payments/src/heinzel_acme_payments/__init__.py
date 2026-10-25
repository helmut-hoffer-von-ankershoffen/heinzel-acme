"""Acme Payments, a made-up org of Acme: the org layer of the reference company (core ADR 0040).

An org layer brings how the org plans and reports, for every team below it. Acme Payments plans by quarterly OKRs in
one document, so its playbook declares the `okr` asset type, with a hint that confirms the org's own OKR document.
Its parent is the company layer `acme`; its teams (such as `acme-payments-checkout`) name it as theirs.
"""

from heinzel import AssetType, DiscoveryHint, Module

from heinzel_acme import LayerAbout, about_layer, layers

OKR_DOCUMENT = "1AcmePaymentsOkrQ4ReferenceDocumentId0000"
"""Acme's own OKR document: made up, like everything about Acme. A real org puts its document's id here; in a trial
account the hint reports it as not found, and you name your copy with `--asset okr=<id>` (docs/REHEARSAL.md)."""

module = Module("acme-payments", "Acme Payments, a made-up org: how it plans, by quarterly OKRs.")
layers.declare(module, parent="acme")
module.playbook(
    "How Acme Payments plans: one OKR document per quarter, which every team's report refers to.",
    assets=[
        AssetType(
            name="okr",
            description="The org's OKR document for the quarter: objectives, key results and where each stands.",
            hints=(
                DiscoveryHint(
                    read="documents.read",
                    args={"ref": OKR_DOCUMENT},
                    match=r"(?i)\bOKRs?\b",
                    summary="Acme Payments' own OKR document, titled with OKR",
                ),
            ),
        )
    ],
)


@module.operation
def info() -> LayerAbout:
    """Show this plugin, its place in Acme's tree and what it brings."""
    return about_layer(
        "heinzel-acme-payments",
        module.name,
        ["playbook: the okr asset type (the org's quarterly OKR document)"],
    )


__all__ = ["OKR_DOCUMENT", "module"]
