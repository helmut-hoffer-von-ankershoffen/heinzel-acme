"""Heinzelmännchen's CLI head with Acme's four layers discovered through their real entry points. Offline."""

import tomllib

import pytest
from heinzel.kernel import user_config_dir

from heinzel_acme.seed._runner import Subprocesses

pytestmark = pytest.mark.integration

LAYERS = ["acme", "acme-payments", "acme-lisbon", "acme-payments-checkout"]


class NeverRun(Subprocesses):
    def run(self, tool, args):
        msg = f"{tool} ran in a test"
        raise AssertionError(msg)


def test_all_four_layers_are_discovered(hz_kernel):
    qualnames = {record.qualname for record in hz_kernel.modules}
    assert {*LAYERS, "acme.seed"} <= qualnames


def test_layers_shows_the_tree_and_each_stack(hz):
    tree = hz("acme", "layers").json
    assert tree["missing"] == []
    by_name = {layer["name"]: layer for layer in tree["layers"]}
    assert set(by_name) == set(LAYERS)
    assert by_name["acme-payments-checkout"]["stack"] == [*LAYERS[:2], "acme-lisbon", "acme-payments-checkout"]
    assert {name: layer["label"] for name, layer in by_name.items()} == {
        "acme": "company",
        "acme-payments": "org",
        "acme-lisbon": "site",
        "acme-payments-checkout": "team",
    }


def test_every_layer_has_info(hz):
    for name in LAYERS:
        about = hz(name, "info").json
        assert about["layer"]["name"] == name
        assert about["plugin"] == f"heinzel-{name}"


def test_doctor_says_which_adapter_plugins_acme_needs(hz):
    checks = {c["name"]: c for c in hz("system", "doctor").json["checks"]["acme"]}
    assert checks["acme binding code-host"]["fix"].startswith("hz system plugin add github")


def test_playbooks_of_every_layer_are_listed(hz):
    listed = {p["module"]: p for p in hz("workflow", "playbooks").json["playbooks"]}
    assert set(LAYERS) <= set(listed)
    team = listed["acme-payments-checkout"]
    assert [t["template"] for t in team["templates"]] == ["acme-payments-checkout:weekly-report"]
    assert {a["name"] for a in team["assets"]} == {
        "weekly-report",
        "engineering-tracker",
        "tracker-project",
        "code-repo",
    }
    assert [a["name"] for a in listed["acme-payments"]["assets"]] == ["okr"]


def test_the_weekly_report_template_becomes_a_valid_contract(hz):
    made = hz(
        "workflow", "new", "weekly-report", "--template", "acme-payments-checkout:weekly-report",
        "--asset", "weekly-report=1AbCdEfGhIjKlMnOpQrStUv", "--asset", "engineering-tracker=1ZyXwVuTsRqPoNmLkJiH",
        "--asset", "tracker-project=CHK", "--asset", "code-repo=ada-example/acme-checkout",
    )  # fmt: skip
    assert made.exit_code == 0, made.output
    checked = hz("workflow", "check")
    assert checked.exit_code == 0, checked.output
    assert checked.json["diagnostics"] == []


def test_a_template_without_its_assets_is_not_ready(hz):
    hz("workflow", "new", "weekly-report", "--template", "acme-payments-checkout:weekly-report")
    codes = {problem["code"] for problem in hz("workflow", "check").json["diagnostics"]}
    assert "HZC025" in codes


def test_setup_writes_only_the_bindings_accepted(hz, hz_prompter):
    hz_prompter.answers += ["y", "n", "n", "n", "n", "n"]
    result = hz("setup", "acme", json=False)
    assert result.exit_code == 0, result.output
    saved = tomllib.loads((user_config_dir() / "config.toml").read_text(encoding="utf-8"))
    assert saved == {"capabilities": {"code_host": "github"}}


def test_seed_is_a_dry_run_unless_told_otherwise(hz, hz_kernel):
    hz_kernel.bind(Subprocesses, NeverRun())
    plan = hz("acme", "seed", "--github-owner", "ada-example", "--email", "ada@example.com").json
    assert plan["dry_run"]
    assert "Rehearsal only" in plan["notice"]
    assert plan["steps"][0]["command"].startswith("gh repo create ada-example/acme-checkout --private")


def test_the_lisbon_calendar_shows_the_report_deadline(hz):
    view = hz("acme-lisbon", "calendar", "--days", "7").json
    assert view["calendar"]["time_zone"] == "Europe/Lisbon"
    assert "Weekly report draft ready" in {o["name"] for o in view["upcoming"]}


def test_the_core_stacks_the_layers_as_acme_declares_them(hz):
    shown = hz("system", "layer", "show").json
    assert shown["layer"] == "acme-payments-checkout"
    assert [layer["name"] for layer in shown["layers"]] == hz("acme-payments-checkout", "info").json["layer"]["stack"]
    assert {layer["name"]: layer["label"] for layer in hz("system", "layer", "list").json["layers"]} == {
        "acme": "company",
        "acme-payments": "org",
        "acme-lisbon": "site",
        "acme-payments-checkout": "team",
    }
