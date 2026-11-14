"""Every adapter against its Core protocol: methods, signatures, honest modes, `unsupported`, hosts.

The conformance kit of ADR 0159 Head B will replace the shape checks here; the behaviour tests stay.
"""

import inspect

import pytest
from heinzel import HeinzelError, ProviderLet
from heinzel.kernel import CAPABILITIES
from heinzel_acme_connectors import NotSupportedError, module
from heinzel_acme_connectors._compat import HAS_MULTI_DOCS

pytestmark = pytest.mark.unit

PROVIDERS = {let.name: let for let in module.lets if isinstance(let, ProviderLet)}


def test_the_plugin_provides_every_connector_capability_and_documents_twice():
    assert sorted(PROVIDERS) == [
        "acme-connectors-docs:documents",
        "acme-connectors-wiki:documents",
        "acme-connectors:calendar",
        "acme-connectors:chat",
        "acme-connectors:code-host",
        "acme-connectors:directory",
        "acme-connectors:mail",
        "acme-connectors:meetings",
        "acme-connectors:tracker",
    ]
    core_served = {"agent-runner", "ai-access", "team-graph"}  # Core's own adapters; ai-models comes with ADR 0159
    assert {p.capability for p in PROVIDERS.values()} == set(CAPABILITIES) - core_served


def test_every_adapter_names_acmes_gateway_and_each_document_store_its_own_host():
    gateway = "mcp-gateway.acme.example"
    hosts = {name: p.hosts for name, p in PROVIDERS.items()}
    for name, host in (
        ("acme-connectors-docs:documents", "docs.acme.example"),
        ("acme-connectors-wiki:documents", "wiki.acme.example"),
    ):
        if HAS_MULTI_DOCS:  # Core routes by `links`; `hosts` is where data goes
            assert (hosts.pop(name), PROVIDERS[name].links) == ((gateway,), (host,))
        else:
            assert hosts.pop(name) == (host, gateway)
    assert set(hosts.values()) == {(gateway,)}
    assert all(p.configured_hosts is None for p in PROVIDERS.values())


@pytest.mark.parametrize("name", sorted(PROVIDERS))
def test_every_method_of_the_capability_has_the_protocols_signature(name):
    provider = PROVIDERS[name]
    capability = CAPABILITIES[provider.capability]
    assert provider.factory.capability == provider.capability
    for method in capability.methods:
        implemented = inspect.signature(getattr(provider.factory, method), eval_str=True)
        declared = inspect.signature(getattr(capability.protocol, method), eval_str=True)
        assert implemented == declared, method


@pytest.mark.parametrize("name", sorted(PROVIDERS))
def test_modes_are_honest_write_only_when_a_write_method_works(name):
    provider = PROVIDERS[name]
    capability = CAPABILITIES[provider.capability]
    unsupported = provider.factory.unsupported
    assert unsupported <= set(capability.methods), "unsupported names only methods of the capability"
    working_writes = {m for m, mode in capability.methods.items() if mode == "write" and m not in unsupported}
    assert ("write" in provider.modes) == bool(working_writes)
    assert "read" in provider.modes
    assert not {m for m, mode in capability.methods.items() if mode == "read"} & unsupported


UNSUPPORTED = {
    ("acme-connectors:mail", "send_draft"),
    ("acme-connectors:calendar", "respond"),
    ("acme-connectors-docs:documents", "replace_section"),
    ("acme-connectors-wiki:documents", "replace_section"),
    ("acme-connectors:tracker", "attach"),
}


def test_the_unsupported_methods_are_the_ones_the_real_gateway_lacks():
    declared = {(name, m) for name, p in PROVIDERS.items() for m in p.factory.unsupported}
    assert declared == UNSUPPORTED


@pytest.mark.parametrize(("name", "method"), sorted(UNSUPPORTED))
def test_an_unsupported_method_refuses_with_not_supported_error_before_reaching_the_gateway(name, method):
    provider = PROVIDERS[name]
    adapter = provider.factory(backend=_Untouchable())
    arity = len(inspect.signature(getattr(provider.factory, method)).parameters) - 1  # without self
    with pytest.raises(NotSupportedError) as refused:
        getattr(adapter, method)(*["x"] * arity)
    assert isinstance(refused.value, HeinzelError)
    assert str(refused.value).startswith(f"This {provider.capability} connector can't {method.replace('_', ' ')}: ")


class _Untouchable:
    def call(self, tool, arguments):
        msg = f"{tool} reached the gateway"
        raise AssertionError(msg)
