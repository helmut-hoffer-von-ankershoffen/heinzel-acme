"""Installed acceptance rejects an SDK artifact before executing it when its digest is wrong."""

import importlib.util
import io
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit


def test_tampered_sdk_is_rejected_before_tool_install(tmp_path_factory, monkeypatch):
    path = Path(__file__).resolve().parents[1] / "e2e/install_test.py"
    spec = importlib.util.spec_from_file_location("acme_sdk_acceptance", path)
    assert spec
    assert spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    monkeypatch.setattr(module, "HZ_SPEC", module.DEFAULT_SDK)
    monkeypatch.setattr(module.shutil, "which", lambda name: "/fictional/uv")
    monkeypatch.setattr(module, "urlopen", lambda *args, **kwargs: io.BytesIO(b"tampered wheel"))

    def must_not_install(*args, **kwargs):
        pytest.fail("tampered SDK reached a subprocess")

    monkeypatch.setattr(module.subprocess, "run", must_not_install)
    with pytest.raises(ValueError, match="checksum mismatch"):
        module.hz.__wrapped__(tmp_path_factory)
