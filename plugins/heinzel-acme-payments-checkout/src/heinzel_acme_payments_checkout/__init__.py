"""Acme Payments Checkout, a made-up team: the team layer of the reference company (core ADR 0040).

The team layer brings the team's own work: the weekly report playbook. Its asset types are the documents and places
the report is made from and kept in (the weekly report document, the engineering tracker, the tracker project and the
code repository), each with how to find it; its template contract drafts the report by Friday 17:00 from the code
host, the tracker and the documents (`hz heinzel new weekly-report --template acme-payments-checkout:weekly-report`).
The team sits under the org `acme-payments` and at the site `acme-lisbon`; its stack is acme, acme-payments,
acme-lisbon, acme-payments-checkout.
"""

from pathlib import Path

from heinzel import AssetType, DiscoveryHint, Module
from pydantic import Field

from heinzel_acme import LayerAbout, about_layer, layers

WEEKLY_REPORT_DOCUMENT = "1AcmeCheckoutWeeklyReportReferenceId00000"
"""Acme's own rolling weekly report document: made up. A real team puts its document's id here; in a trial account
the hint reports it as not found, and you name your copy with `--asset weekly-report=<id>`."""
TRACKER_DOCUMENT = "1AcmeCheckoutEngineeringTrackerRefId00000"
"""Acme's own engineering tracker sheet: made up, like the weekly report document."""
TEMPLATES = Path(__file__).parent / "templates"
"""The template contracts, `<name>.prose.md`, read when the plugin is imported."""
DRAFT_TAGS = {
    "weekly-report": "🧝 draft: edit this week's section, then delete this line to approve",
    "engineering-tracker": "a cell note 'hz:draft' on the rows hz drafted; delete the note to approve",
}
"""How a draft is marked where it lives, per asset type (core ADR 0038): removing the tag approves. Data for the
documents adapter's `place_draft` once it can write; drafts stay local until then."""


class CheckoutAbout(LayerAbout):
    """The team plugin: its layer and its draft tag conventions."""

    draft_tags: dict[str, str] = Field(description="How a draft is marked in place, by asset type (ADR 0038).")


module = Module("acme-payments-checkout", "Acme Payments Checkout, a made-up team: its weekly report playbook.")
layers.declare(module, parent="acme-payments", site="acme-lisbon")
module.playbook(
    "Draft Checkout's weekly report by Friday 17:00 Lisbon time from the week's merged pull requests, tracker changes, "
    "the engineering tracker and the previous report.",
    assets=[
        AssetType(
            name="weekly-report",
            description="The rolling weekly report document, newest week first: the model and the home of each report.",
            hints=(
                DiscoveryHint(
                    read="documents.read",
                    args={"ref": WEEKLY_REPORT_DOCUMENT},
                    match=r"(?i)weekly report",
                    summary="Checkout's own weekly report document",
                ),
            ),
            kept_by="weekly-report",
        ),
        AssetType(
            name="engineering-tracker",
            description="The engineering tracker sheet: goals, milestones, owners, status and risks.",
            hints=(
                DiscoveryHint(
                    read="documents.read",
                    args={"ref": TRACKER_DOCUMENT},
                    match=r"(?i)tracker",
                    summary="Checkout's own engineering tracker",
                ),
            ),
        ),
        AssetType(
            name="tracker-project",
            description="The Jira project the team plans in: its key, e.g. CHK.",
        ),
        AssetType(
            name="code-repo",
            description="The team's code repository, as owner/name; add an input per further repository.",
        ),
    ],
    templates=[TEMPLATES],
)


@module.operation
def info() -> CheckoutAbout:
    """Show this plugin, its place in Acme's tree, what it brings and how drafts are marked in place."""
    base = about_layer(
        "heinzel-acme-payments-checkout",
        module.name,
        [
            "playbook: asset types weekly-report, engineering-tracker, tracker-project, code-repo",
            "template contract acme-payments-checkout:weekly-report: a draft ready by Friday 17:00 Lisbon time",
        ],
    )
    return CheckoutAbout(**base.model_dump(), draft_tags=DRAFT_TAGS)


__all__ = ["DRAFT_TAGS", "TRACKER_DOCUMENT", "WEEKLY_REPORT_DOCUMENT", "CheckoutAbout", "module"]
