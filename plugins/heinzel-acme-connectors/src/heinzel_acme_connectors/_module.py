"""The module declaration, apart from `__init__.py` so the adapters can import it without a cycle."""

from heinzel import Module

module = Module(
    "acme-connectors",
    "ACME's connectors for every capability, shaped for a company MCP gateway, on dummy data.",
)
