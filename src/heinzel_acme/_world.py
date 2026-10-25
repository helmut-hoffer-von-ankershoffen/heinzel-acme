"""The made-up Acme world: its people, its Checkout team's tracker items, pull requests and documents.

Everything here is fiction (company Acme at acme.example, org Payments, team Checkout, site Lisbon). `hz acme seed`
writes it into the person's own trial accounts for a dress rehearsal of the weekly report; tests read it to check the
playbook against a world that has every asset the template contract needs.
"""

from dataclasses import dataclass

COMPANY = "Acme"
DOMAIN = "acme.example"
ORG = "Payments"
TEAM = "Checkout"
SITE = "Lisbon"
PROJECT_KEY = "CHK"
"""The Checkout team's tracker project key; fixed, so the playbook's hints and the seeded world agree."""
PROJECT_NAME = "Acme Checkout"
REPOSITORY = "acme-checkout"
"""The demo repository's name; it is created under the person's own GitHub account."""


@dataclass(frozen=True, kw_only=True, slots=True)
class Person:
    """A made-up member of the Checkout team; roles are the core's vocabulary."""

    handle: str
    name: str
    role: str

    @property
    def email(self) -> str:
        """Their made-up address at acme.example, which no mail server answers."""
        return f"{self.handle}@{DOMAIN}"


PEOPLE: tuple[Person, ...] = (
    Person(handle="nadia", name="Nadia Moreira", role="engineering-manager"),
    Person(handle="tomas", name="Tomas Leal", role="engineer"),
    Person(handle="priya", name="Priya Raman", role="engineer"),
    Person(handle="mara", name="Mara Okafor", role="principal"),
    Person(handle="jonas", name="Jonas Berg", role="product-manager"),
)


@dataclass(frozen=True, kw_only=True, slots=True)
class Item:
    """A tracker item of the Checkout project; owners appear as labels, since made-up people have no accounts."""

    summary: str
    kind: str
    status: str
    owner: str
    goal: str


ITEMS: tuple[Item, ...] = (
    Item(summary="Saved cards: list and delete stored cards", kind="Story", status="In Progress", owner="tomas",
         goal="saved-cards"),
    Item(summary="Saved cards: 3-D Secure challenge on first use", kind="Story", status="To Do", owner="priya",
         goal="saved-cards"),
    Item(summary="Show the delivery cost before the payment step", kind="Story", status="Done", owner="tomas",
         goal="conversion"),
    Item(summary="Retry a declined payment once with a fresh session", kind="Task", status="In Progress",
         owner="priya", goal="no-surprises"),
    Item(summary="Flaky test in the address form", kind="Bug", status="Done", owner="mara", goal="conversion"),
    Item(summary="Payment page loads in under one second at p95", kind="Story", status="To Do", owner="mara",
         goal="fast-pages"),
    Item(summary="Move the Friday demo to 16:00 Lisbon time", kind="Task", status="Done", owner="nadia",
         goal="team"),
)  # fmt: skip


@dataclass(frozen=True, kw_only=True, slots=True)
class Change:
    """A pull request on the demo repository: one file, merged or left open."""

    branch: str
    title: str
    body: str
    path: str
    content: str
    merge: bool


CHANGES: tuple[Change, ...] = (
    Change(
        branch="feat/saved-cards-list",
        title="feat(cards): list saved cards",
        body="Lists the cards a shopper saved, newest first. Part of CHK saved cards.",
        path="src/cards/list.md",
        content="# Saved cards\n\nShoppers see their saved cards, newest first, and can delete one.\n",
        merge=True,
    ),
    Change(
        branch="fix/address-form-flake",
        title="fix(address): wait for the postcode lookup in the test",
        body="The address form test raced the postcode lookup; it now waits for it.",
        path="src/address/README.md",
        content="# Address form\n\nThe postcode lookup finishes before the form is checked.\n",
        merge=True,
    ),
    Change(
        branch="feat/delivery-cost",
        title="feat(checkout): show the delivery cost before payment",
        body="Shoppers see the delivery cost on the basket page, before the payment step.",
        path="src/checkout/delivery.md",
        content="# Delivery cost\n\nShown on the basket page, before the payment step.\n",
        merge=True,
    ),
    Change(
        branch="feat/payment-retry",
        title="feat(payments): retry a declined payment once",
        body="A declined payment is retried once with a fresh session. Open for review.",
        path="src/payments/retry.md",
        content="# Payment retry\n\nA declined payment is retried once, with a fresh session.\n",
        merge=False,
    ),
)

OKR_DOC = """\
<h1>Acme Payments OKRs, Q4</h1>
<p>Owner: the Payments org. Teams: Checkout, Payouts. Reviewed every second Monday.</p>
<h2>O1: Paying is effortless</h2>
<ul>
<li>KR1 (saved-cards): saved cards are used in 30% of checkouts. Now: 0%, launch planned for week 46.</li>
<li>KR2 (conversion): checkout conversion up by 2 points. Now: +0.4.</li>
</ul>
<h2>O2: Payments never surprise anyone</h2>
<ul>
<li>KR3 (fast-pages): the payment page loads in under one second at p95. Now: 1.6 s.</li>
<li>KR4 (no-surprises): no declined payment without a clear next step for the shopper. Now: 3 open cases.</li>
</ul>
"""

WEEKLY_REPORT_DOC = """\
<h1>Checkout weekly report</h1>
<p>The Checkout team's weekly report, newest week first. Drafted on Fridays, sent by Nadia to Payments.</p>
<h2>Week 42</h2>
<h3>Highlights</h3>
<ul><li>Saved cards: the card list works behind a flag in staging.</li></ul>
<h3>Progress on goals</h3>
<ul>
<li>Saved cards (KR1): list done in staging; deleting a card is next.</li>
<li>Conversion (KR2): the delivery cost moves to the basket page; design agreed.</li>
</ul>
<h3>Risks</h3>
<ul><li>The 3-D Secure challenge needs the payment provider's sandbox, not yet available.</li></ul>
<h3>Next week</h3>
<ul><li>Delete a saved card. Start the payment retry.</li></ul>
<p>Thanks, the Checkout team</p>
<h2>Week 41</h2>
<h3>Highlights</h3>
<ul><li>The address form no longer loses the postcode when the page reloads.</li></ul>
<h3>Progress on goals</h3>
<ul><li>Saved cards (KR1): storage agreed with Payments security.</li></ul>
<h3>Risks</h3>
<ul><li>None new.</li></ul>
<h3>Next week</h3>
<ul><li>Card list behind a flag.</li></ul>
<p>Thanks, the Checkout team</p>
"""

TRACKER_SHEET = """\
Goal,Milestone,Owner,Status,Due,Risk
saved-cards,List and delete saved cards,tomas,in progress,week 44,
saved-cards,3-D Secure challenge on first use,priya,not started,week 46,provider sandbox not available
conversion,Delivery cost before payment,tomas,done,week 43,
no-surprises,Retry a declined payment once,priya,in progress,week 45,
fast-pages,Payment page under one second at p95,mara,not started,week 47,needs a performance budget
"""
