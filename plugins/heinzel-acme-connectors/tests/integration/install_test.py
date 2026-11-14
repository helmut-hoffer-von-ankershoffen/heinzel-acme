"""`python -m heinzel` in a subprocess, outside the source directory: it discovers every ACME connector."""

import os
import subprocess
import sys

import pytest

pytestmark = pytest.mark.integration

ADAPTERS = {
    "mail": ["acme-connectors"],
    "calendar": ["acme-connectors"],
    "documents": ["acme-connectors-docs", "acme-connectors-wiki"],
    "tracker": ["acme-connectors"],
    "chat": ["acme-connectors"],
    "meetings": ["acme-connectors"],
    "code-host": ["acme-connectors"],
    "directory": ["acme-connectors"],
}


def test_the_installed_plugin_offers_an_adapter_for_every_connector_capability(tmp_path):
    environment = {key: value for key, value in os.environ.items() if not key.startswith("HZ_")}
    environment["HZ_PLUGINS_ENABLED"] = "true"
    environment.pop("PYTHONPATH", None)
    for key in ("CONFIG_HOME", "DATA_DIR", "CACHE_DIR", "STATE_DIR", "LOG_DIR"):
        environment[f"HZ_{key}"] = str(tmp_path / key.lower())
    result = subprocess.run(
        [sys.executable, "-m", "heinzel", "system", "info", "--json"],
        cwd=tmp_path,
        env=environment,
        check=False,
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert result.returncode == 0, result.stderr
    text = result.stdout
    for capability, names in ADAPTERS.items():
        for name in names:
            assert name in text, (capability, name)
