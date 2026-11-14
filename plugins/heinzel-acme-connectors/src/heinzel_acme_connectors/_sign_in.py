"""How the connectors say they are connected and signed in: a dummy sign-in (ADR 0136) and health checks (ADR 0055).

A real company's gateway launcher holds the sign-in: `status` asks it who is signed in, `sign_in` starts its consent
flow and reports the consent page, `sign_out` asks it to forget the sign-in. Here the state is a setting,
`acme-connectors.sign_in_state` (`signed-in`, `signed-out` or `expired`), so every state can be shown and tested;
`sign_in` and `sign_out` change it for the running process only. Nothing reaches a network: the consent page is a
made-up address at acme.example.
"""

import threading
from collections.abc import Callable
from typing import ClassVar

from heinzel import (
    Check,
    Grant,
    GrantStatus,
    HeinzelError,
    Login,
    SignInOutcome,
    SignInProgress,
    SignInStatus,
    Status,
)

from heinzel_acme_connectors._backend import CONNECTORS, connect
from heinzel_acme_connectors._settings import ConnectorSettings

ACCOUNT = "nadia@acme.example"
"""The made-up account the dummy is signed in as."""
CONSENT = "https://login.acme.example/consent"
"""The made-up consent page of ACME's gateway."""
GRANTS = (
    Grant(
        id="read",
        title="Read your work tools",
        explanation="Read mail, calendar, documents, issues, chat, meetings, code and the directory.",
        scopes=["acme.read"],
        default=True,
    ),
    Grant(
        id="write",
        title="Change things for you",
        explanation="Keep mail drafts, change calendar events, update issues and post in chat, each after you confirm.",
        scopes=["acme.write"],
    ),
)
"""What ACME's sign-in can be allowed to do."""


class AcmeSignIn:
    """The gateway's sign-in, as a dummy whose state comes from `acme-connectors.sign_in_state`."""

    state: ClassVar[dict[str, str]] = {}
    """The state after a `sign_in` or `sign_out` in this process; the setting until then. Dummy only: a real plugin
    keeps no sign-in state of its own and asks its gateway launcher every time."""

    def __init__(self, settings: ConnectorSettings) -> None:
        """Read the starting state from the plugin's settings; the kernel passes them."""
        self._settings = settings

    @property
    def current(self) -> str:
        """`signed-in`, `signed-out` or `expired`."""
        return self.state.get("now", self._settings.sign_in_state)

    def status(self, *, live: bool) -> SignInStatus:
        """Who is signed in and which grants hold; `live` would ask the gateway once (the dummy asks nobody)."""
        held = {"signed-in": "granted", "signed-out": "missing", "expired": "unknown"}[self.current]
        grants = [GrantStatus(grant=grant, state=held, needed=grant.default) for grant in GRANTS]  # type: ignore[arg-type]
        if self.current == "signed-out":
            return SignInStatus(signed_in=False, grants=grants, live=live)
        problem = "The ACME sign-in expired on 2026-11-13; sign in again." if self.current == "expired" else ""
        return SignInStatus(signed_in=True, account=ACCOUNT, grants=grants, problem=problem, live=live)

    def sign_in(
        self, grants: frozenset[str], progress: Callable[[SignInProgress], None], stop: threading.Event
    ) -> SignInOutcome:
        """Report the gateway's consent page, then succeed at once unless `stop` is already set (a dummy)."""
        progress(SignInProgress(url=f"{CONSENT}?grants={'+'.join(sorted(grants))}", finish_on="anywhere"))
        if stop.is_set():
            return SignInOutcome(state="cancelled", message="The ACME sign-in was cancelled; nothing changed.")
        self.state["now"] = "signed-in"
        return SignInOutcome(state="succeeded", message="Signed in to ACME's gateway.", account=ACCOUNT)

    def sign_out(self) -> str:
        """Forget the sign-in, as the gateway launcher would; what happened."""
        self.state["now"] = "signed-out"
        return "Signed out of ACME's gateway; reading through it stops until you sign in again."


def checks(sign_in: AcmeSignIn) -> list[Check]:
    """Offline: every connector has its launcher, and the sign-in holds; nothing is called."""
    launchers = [name for name, spec in CONNECTORS.items() if not spec.launcher]
    found: list[Check] = [
        Check(
            name="launchers",
            status=Status.DOWN if launchers else Status.UP,
            detail=f"no launcher for {', '.join(launchers)}" if launchers else f"{len(CONNECTORS)} connectors",
        )
    ]
    status = sign_in.status(live=False)
    login = Login(signed_in=status.signed_in, account=status.account)
    if not status.signed_in:
        found.append(
            Check(
                name="sign-in",
                status=Status.DOWN,
                detail="not signed in",
                fix="hz system connector connect acme-connectors",
                login=login,
            )
        )
    elif status.problem:
        found.append(
            Check(
                name="sign-in",
                status=Status.DEGRADED,
                detail=status.problem,
                fix="hz system connector connect acme-connectors",
                login=login,
            )
        )
    else:
        found.append(Check(name="sign-in", status=Status.UP, detail=f"signed in as {status.account}", login=login))
    return found


def live(sign_in: AcmeSignIn) -> list[Check]:
    """Live: start each connector, which checks that its server has every tool; here against the dummy servers."""
    if sign_in.current != "signed-in":
        return [
            Check(
                name="gateway",
                status=Status.DOWN,
                detail=f"not tested: {sign_in.current}",
                fix="hz system connector connect acme-connectors",
            )
        ]
    found: list[Check] = []
    for name in CONNECTORS:
        try:
            connect(name)
        except HeinzelError as exc:
            found.append(Check(name=f"connector {name}", status=Status.DOWN, detail=str(exc)[:200]))
        else:
            found.append(Check(name=f"connector {name}", status=Status.UP, detail="every tool there"))
    return found
