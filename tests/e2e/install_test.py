"""Install Heinzelmännchen with `uv tool install`, develop the team plugin, use its stack. Needs network.

Set HZ_SPEC to test against another Heinzelmännchen, e.g. `HZ_SPEC=git+https://github.com/helmut-hoffer-von-ankershoffen/heinzel@main`.
"""

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

pytestmark = [pytest.mark.e2e, pytest.mark.timeout(300)]

REPO = Path(__file__).resolve().parents[2]
HZ_SPEC = os.environ.get("HZ_SPEC", "git+https://github.com/helmut-hoffer-von-ankershoffen/heinzel@v0.7.2")


@pytest.fixture(scope="module")
def hz(tmp_path_factory):
    root = tmp_path_factory.mktemp("uv-tools")
    env = {**os.environ, "UV_TOOL_DIR": str(root / "tools"), "UV_TOOL_BIN_DIR": str(root / "bin")}
    env.pop("VIRTUAL_ENV", None)
    uv = shutil.which("uv")
    assert uv, "uv is not on PATH: https://docs.astral.sh/uv/"
    subprocess.run([uv, "tool", "install", HZ_SPEC], check=True, env=env, timeout=240)

    def run(*args: str) -> str:
        result = subprocess.run(
            [str(root / "bin" / "hz"), *args], capture_output=True, text=True, check=False, env=env, timeout=240
        )
        assert result.returncode == 0, f"hz {' '.join(args)} failed:\n{result.stdout}\n{result.stderr}"
        return result.stdout

    # One plugin, the team's: its stack (org, site, company) comes with it as dependencies (core ADR 0040).
    run("system", "plugin", "develop", str(REPO / "plugins" / "heinzel-acme-payments-checkout"))
    return run


def test_adding_the_team_plugin_installs_its_stack(hz):
    plugins = {p["distribution"] for p in json.loads(hz("system", "plugin", "list", "--json"))}
    assert {"heinzel-acme", "heinzel-acme-payments", "heinzel-acme-lisbon", "heinzel-acme-payments-checkout"} <= plugins


def test_layers(hz):
    tree = json.loads(hz("acme", "layers", "--json"))
    assert tree["missing"] == []
    team = next(layer for layer in tree["layers"] if layer["name"] == "acme-payments-checkout")
    assert team["stack"] == ["acme", "acme-payments", "acme-lisbon", "acme-payments-checkout"]


def test_the_weekly_report_template_is_offered(hz):
    playbooks = json.loads(hz("heinzel", "playbooks", "--json"))["playbooks"]
    templates = [t["template"] for p in playbooks for t in p["templates"]]
    assert "acme-payments-checkout:weekly-report" in templates
