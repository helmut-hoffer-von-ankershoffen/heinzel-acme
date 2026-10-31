"""The compatibility build rejects modified source before running a build backend."""

import os
import subprocess
import tomllib
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration
ROOT = Path(__file__).resolve().parents[2]
SCRIPT = ROOT / "scripts/bootstrap-pyyaml.sh"


def test_bootstrap_uses_the_locked_pyyaml_source():
    lock = tomllib.loads((ROOT / "uv.lock").read_text())
    package = next(item for item in lock["package"] if item["name"] == "pyyaml")
    script = SCRIPT.read_text()
    assert f"source_url={package['sdist']['url']}\n" in script
    assert f"source_sha={package['sdist']['hash'].removeprefix('sha256:')}\n" in script
    assert f"pyyaml-{package['version']}.tar.gz" in script


def test_tampered_source_never_reaches_build_backend(tmp_path):
    tools = tmp_path / "bin"
    tools.mkdir()
    marker = tmp_path / "backend-started"
    curl = tools / "curl"
    curl.write_text('#!/bin/sh\nfor last do :; done\nprintf tampered > "$last"\n')
    curl.chmod(0o755)
    uv = tools / "uv"
    uv.write_text(f'#!/bin/sh\ntouch "{marker}"\nexit 99\n')
    uv.chmod(0o755)
    result = subprocess.run(
        ["bash", str(SCRIPT)],
        env={**os.environ, "PATH": f"{tools}{os.pathsep}{os.environ['PATH']}"},
        capture_output=True,
        text=True,
        check=False,
        timeout=10,
    )
    assert result.returncode != 0
    assert not marker.exists()
