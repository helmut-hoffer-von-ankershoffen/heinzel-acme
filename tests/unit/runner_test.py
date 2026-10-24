import pytest
from heinzel import HeinzelError

from heinzel_acme.seed import _runner

pytestmark = pytest.mark.unit


def test_the_clis_get_only_the_variables_they_need(monkeypatch):
    monkeypatch.setenv("GH_HOST", "github.com")
    monkeypatch.setenv("HZ_CREDENTIAL_X", "secret")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "secret")
    env = _runner.environment()
    assert env["GH_HOST"] == "github.com"
    assert "HZ_CREDENTIAL_X" not in env
    assert "AWS_SECRET_ACCESS_KEY" not in env


def test_a_missing_cli_says_how_to_get_it(monkeypatch):
    monkeypatch.setattr(_runner.shutil, "which", lambda _: None)
    with pytest.raises(HeinzelError, match="not installed"):
        _runner.Subprocesses().run("acli", ["jira"])


def test_write_creates_the_directory(tmp_path):
    _runner.write(tmp_path / "a" / "b.txt", "x")
    assert (tmp_path / "a" / "b.txt").read_text(encoding="utf-8") == "x"
