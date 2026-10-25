"""The seed runner keeps vendor authentication but never inherits another Git repository or config injection."""

import importlib.util
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

# Load this boundary alone: environment checks need no plugin declarations or layer discovery.
_SOURCE = Path(__file__).parents[2] / "src" / "heinzel_acme" / "seed" / "_runner.py"
_spec = importlib.util.spec_from_file_location("acme_seed_runner_environment", _SOURCE)
assert _spec is not None
assert _spec.loader is not None
runner = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(runner)


def test_git_storage_and_config_injection_are_removed_but_host_authentication_survives(monkeypatch):
    unsafe = (
        "GIT_DIR",
        "GIT_WORK_TREE",
        "GIT_COMMON_DIR",
        "GIT_INDEX_FILE",
        "GIT_OBJECT_DIRECTORY",
        "GIT_ALTERNATE_OBJECT_DIRECTORIES",
        "GIT_NAMESPACE",
        "GIT_CONFIG_PARAMETERS",
        "GIT_CONFIG_COUNT",
        "GIT_CONFIG_KEY_0",
        "GIT_CONFIG_VALUE_0",
    )
    for key in unsafe:
        monkeypatch.setenv(key, "unwanted")
    expected = {"GH_TOKEN": "example-gh-auth", "GITHUB_TOKEN": "example-github-auth", "SSH_AUTH_SOCK": "/example/agent"}
    for key, value in expected.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setenv("HZ_CREDENTIAL_PRIVATE", "unwanted")

    environment = runner.environment()

    assert not set(unsafe) & environment.keys()
    assert "HZ_CREDENTIAL_PRIVATE" not in environment
    assert {key: environment[key] for key in expected} == expected
