"""ACME's connectors: a connector for every Core capability, shaped for a company MCP gateway, on dummy data.

A company copies this into its own private plugin repository and replaces `_backend.connect` with an MCP client of
its gateway.
Each adapter implements one Core protocol (ADR 0028) and declares the modes it really serves; what its connector
can't do is listed in its `unsupported` attribute and refused with `NotSupportedError` (ADR 0159). Each adapter
declares ACME's made-up gateway host, which is where a real plugin's data goes and what Heinzelmännchen shows people;
the dummy data itself never leaves the process.

Bind them with `hz system config set capabilities.<capability> acme-connectors`, or in the app's connector settings.
Documents has two adapters, `acme-connectors-docs` and `acme-connectors-wiki`, one per store.
"""

from typing import Any

from heinzel import Check

from heinzel_acme_connectors._ai_models import AcmeModels
from heinzel_acme_connectors._calendar import AcmeCalendar
from heinzel_acme_connectors._chat import AcmeChat
from heinzel_acme_connectors._code_host import AcmeCodeHost
from heinzel_acme_connectors._compat import HAS_AI_MODELS, HAS_MULTI_DOCS, NotSupportedError
from heinzel_acme_connectors._directory import AcmeDirectory
from heinzel_acme_connectors._documents import AcmeDocs, AcmeWiki
from heinzel_acme_connectors._mail import AcmeMail
from heinzel_acme_connectors._meetings import AcmeMeetings
from heinzel_acme_connectors._module import module
from heinzel_acme_connectors._settings import ConnectorSettings
from heinzel_acme_connectors._sign_in import GRANTS, AcmeSignIn, checks, live
from heinzel_acme_connectors._tracker import AcmeTracker

module.settings(ConnectorSettings)
module.sign_in(grants=GRANTS)(AcmeSignIn)


@module.health
def health(settings: ConnectorSettings) -> list[Check]:
    """Offline: every connector has its launcher, and the sign-in holds."""
    return checks(AcmeSignIn(settings))


@module.health(live=True)
def health_live(settings: ConnectorSettings) -> list[Check]:
    """Live, on `hz system connector test`: start every connector and check its tools."""
    return live(AcmeSignIn(settings))


GATEWAY = ("mcp-gateway.acme.example",)
"""Where a real plugin's launchers send data: the company MCP gateway. Made up; the dummy sends nothing."""

module.provides("mail", modes={"read", "write"}, hosts=GATEWAY)(AcmeMail)
module.provides("calendar", modes={"read", "write"}, hosts=GATEWAY)(AcmeCalendar)
# Two document stores, two adapters. `links` names the host of the addresses people open, which Core routes by
# (ADR 0161); `hosts` stays where data goes. On an older Core, which has no `links`, the store's host is in `hosts`.
for store, name in ((AcmeDocs, "acme-connectors-docs"), (AcmeWiki, "acme-connectors-wiki")):
    routing: dict[str, Any] = {"hosts": GATEWAY, "links": (store.host,)} if HAS_MULTI_DOCS else {}
    module.provides("documents", modes={"read"}, name=name, **(routing or {"hosts": (store.host, *GATEWAY)}))(store)
module.provides("tracker", modes={"read", "write"}, hosts=GATEWAY)(AcmeTracker)
module.provides("chat", modes={"read", "write"}, hosts=GATEWAY)(AcmeChat)
module.provides("meetings", modes={"read"}, hosts=GATEWAY)(AcmeMeetings)
module.provides("code-host", modes={"read"}, hosts=GATEWAY)(AcmeCodeHost)
module.provides("directory", modes={"read"}, hosts=GATEWAY)(AcmeDirectory)
if HAS_AI_MODELS:  # Core with ADR 0159; it lists the models as an AI access option, not on the connector page
    module.provides("ai-models", modes={"read"}, hosts=("models.acme.example",))(AcmeModels)

__all__ = [
    "AcmeCalendar",
    "AcmeChat",
    "AcmeCodeHost",
    "AcmeDirectory",
    "AcmeDocs",
    "AcmeMail",
    "AcmeMeetings",
    "AcmeModels",
    "AcmeSignIn",
    "AcmeTracker",
    "AcmeWiki",
    "NotSupportedError",
    "module",
]
