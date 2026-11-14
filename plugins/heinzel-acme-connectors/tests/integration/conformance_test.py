"""Core's conformance kit (ADR 0159) on every adapter, with sample arguments for every read method. Offline.

This is the check a company's own CI copies: it runs against the Core the plugin pins and checks what Core relies on
(shapes, modes, hosts, read calls that don't write, AI models, sign-in and health). A Core without the kit skips it.
"""

from datetime import UTC, datetime

import pytest
from heinzel import Window
from heinzel_acme_connectors import AcmeDocs, AcmeWiki, module

pytestmark = pytest.mark.integration

WEEK = Window(since=datetime(2026, 11, 1, tzinfo=UTC), until=datetime(2026, 11, 8, tzinfo=UTC))
SAMPLES = {
    "mail": {
        "messages": {"query": "label:inbox", "window": WEEK},
        "read": {"message": "m-1001"},
        "thread": {"thread": "t-100"},
    },
    "calendar": {
        "events": {"window": WEEK},
        "free_busy": {"people": "tomas@acme.example", "window": WEEK},
    },
    "documents": {"search": {"query": "roadmap", "limit": 5}},  # `read` per store, below: each reads its own refs
    "tracker": {"issues_updated": {"project": "CHK", "window": WEEK}},
    "chat": {"messages": {"channel": "#release", "window": WEEK}},
    "meetings": {
        "ended": {"window": WEEK},
        "transcripts": {"window": WEEK},
        "transcript": {"meeting": "mt-1"},
    },
    "code-host": {"merged_pull_requests": {"repository": "acme/acme-checkout", "window": WEEK}},
    "directory": {"person": {"person": "nadia"}, "reports": {"person": "nadia"}},
}


def test_every_adapter_conforms_with_every_read_method_called(request):
    pytest.importorskip("heinzel.conformance", reason="this Core has no conformance kit (ADR 0159)")
    hz_conformance = request.getfixturevalue("hz_conformance")  # from heinzel.testing, on a Core with the kit
    report = hz_conformance(module, samples=SAMPLES)
    # Not called here: mail.draft (no draft exists until one is made, a write) and documents.read (each store below).
    assert set(report.skipped) == {"mail.draft", "documents.read"}, report.skipped
    for store, ref in ((AcmeDocs(), "doc-roadmap"), (AcmeWiki(), "10001")):
        hz_conformance(store, "documents", modes={"read"}, samples={"read": {"ref": ref}})
