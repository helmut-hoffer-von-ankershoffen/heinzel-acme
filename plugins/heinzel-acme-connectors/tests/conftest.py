"""Shared fixtures: ACME's dummy week, and kernels that bind these adapters. Offline.

Every person, company and address here is made up. heinzel.testing (a pytest plugin, loaded automatically) gives
every test its own HZ_* directories and its level's timeout.
"""

from collections.abc import Callable
from datetime import UTC, datetime

import pytest
from heinzel import Config, Kernel, Module, ModuleRecord, Settings, Window
from heinzel.kernel import Origin, discover

WEEK = Window(since=datetime(2026, 11, 1, tzinfo=UTC), until=datetime(2026, 11, 8, tzinfo=UTC))
"""The week the dummy data lives in."""
TEST_ORIGIN = Origin(distribution="heinzel-test", version="0", builtin=False)


@pytest.fixture
def week() -> Window:
    return WEEK


@pytest.fixture
def connectors_kernel() -> Callable[..., Kernel]:
    """A kernel with every installed plugin, the given bindings, and extra test-only modules."""

    def make(bindings: dict[str, str], **modules: Module) -> Kernel:
        records, errors = discover()
        records += [ModuleRecord(qualname=name, module=module, origin=TEST_ORIGIN) for name, module in modules.items()]
        return Kernel(Settings(), records, errors, Config(files=(), data={"capabilities": bindings}))

    return make


@pytest.fixture
def configured_kernel():
    """A kernel with every installed plugin, the given configuration data, and extra test-only modules."""

    def make(data: dict[str, object], **modules: Module) -> Kernel:
        records, errors = discover()
        records += [ModuleRecord(qualname=name, module=module, origin=TEST_ORIGIN) for name, module in modules.items()]
        return Kernel(Settings(), records, errors, Config(files=(), data=data))

    return make
