"""Heinzelmännchen's CLI head with this plugin discovered through its real entry point. Offline."""

import json
import tomllib

import pytest
from heinzel import Prompter
from heinzel.heads.cli import build
from heinzel.kernel import ScriptedPrompter, user_config_dir
from typer.testing import CliRunner

pytestmark = pytest.mark.integration

runner = CliRunner()


def invoke(kernel, *args: str):
    result = runner.invoke(build(kernel), list(args))
    assert result.exit_code == 0, result.output
    return result.output


def test_plugin_modules_are_discovered(boot):
    qualnames = [record.qualname for record in boot().modules]
    assert "acme" in qualnames
    assert "acme.hello" in qualnames


def test_info(boot):
    about = json.loads(invoke(boot(), "acme", "info", "--json"))
    assert about["plugin"] == "heinzel-acme"
    assert about["modules"] == ["acme", "acme.hello"]


def test_hello_submodule_collapses_into_a_command(boot):
    assert json.loads(invoke(boot(), "acme", "hello", "--name", "Ada", "--json")) == {"text": "Hello, Ada!"}


def test_contributes_to_system_info(boot):
    sections = json.loads(invoke(boot(), "system", "info", "--json"))["sections"]
    assert sections["acme"]["plugin"] == "heinzel-acme"


def test_plugin_can_be_disabled(boot):
    kernel = boot(disabled_modules=frozenset({"acme"}))
    assert not [r for r in kernel.modules if r.qualname.startswith("acme")]


def test_greeting_is_configurable_through_the_environment(boot, monkeypatch):
    monkeypatch.setenv("HZ_ACME__GREETING", "Hi")
    assert json.loads(invoke(boot(), "acme", "hello", "--name", "Ada", "--json")) == {"text": "Hi, Ada!"}


def test_greeting_is_configurable_through_a_config_file(monkeypatch, tmp_path):
    from heinzel import Config, Kernel
    from heinzel.kernel import discover

    (tmp_path / "hz.toml").write_text('[acme]\ngreeting = "Moin"\n', encoding="utf-8")
    kernel = Kernel(records=discover()[0], config=Config.load(tmp_path))
    assert json.loads(invoke(kernel, "acme", "hello", "--name", "Ada", "--json")) == {"text": "Moin, Ada!"}


def test_setup_asks_for_the_greeting_and_saves_it(boot):
    kernel = boot()
    prompter = ScriptedPrompter(["Moin"])
    kernel.bind(Prompter, prompter)
    invoke(kernel, "setup", "acme")
    assert "How should `hello` greet? [Hello]: Moin" in prompter.transcript
    saved = tomllib.loads((user_config_dir() / "config.toml").read_text(encoding="utf-8"))
    assert saved == {"acme": {"greeting": "Moin"}}


def test_the_acme_theme_is_listed_and_can_be_used(boot):
    listed = json.loads(invoke(boot(), "system", "theme", "list", "--json"))
    (acme,) = [theme for theme in listed["themes"] if theme["name"] == "acme"]
    assert (acme["plugin"], acme["module"], acme["light"]["primary"]) == ("heinzel-acme", "acme", "#0f766e")
    used = json.loads(invoke(boot(), "system", "theme", "use", "acme", "--json"))
    assert used["selected"] == "acme"
    config = tomllib.loads((user_config_dir() / "config.toml").read_text(encoding="utf-8"))
    assert config["system"]["theme"]["name"] == "acme"
