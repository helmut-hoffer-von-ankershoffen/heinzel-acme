"""The seed runner keeps vendor authentication but never inherits another Git repository or config injection."""

import importlib.util
import subprocess
from pathlib import Path

import pytest

pytestmark = pytest.mark.integration

# Load this boundary alone: environment checks need no plugin declarations or layer discovery.
_SOURCE = Path(__file__).parents[2] / "src" / "heinzel_acme" / "seed" / "_runner.py"
_spec = importlib.util.spec_from_file_location("acme_seed_runner_environment", _SOURCE)
assert _spec is not None
assert _spec.loader is not None
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)


def test_git_c_cannot_be_redirected_by_inherited_repository_variables(tmp_path, monkeypatch):
    for key in list(runner.os.environ):
        if key.startswith("GIT_"):
            monkeypatch.delenv(key)
    monkeypatch.setenv("GIT_CONFIG_GLOBAL", "/dev/null")
    intended = tmp_path / "intended"
    other = tmp_path / "other"
    for directory in (intended, other):
        subprocess.run(["git", "init", "-q", str(directory)], check=True, capture_output=True, timeout=5)
    monkeypatch.setenv("GIT_DIR", str(other / ".git"))
    monkeypatch.setenv("GIT_WORK_TREE", str(other))

    actual = runner.Subprocesses().run("git", ["-C", str(intended), "rev-parse", "--show-toplevel"])

    assert Path(actual.strip()).resolve() == intended.resolve()
