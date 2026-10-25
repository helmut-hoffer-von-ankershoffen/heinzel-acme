import json

import pytest
from heinzel import HeinzelError

from heinzel_acme.seed._plan import Step
from heinzel_acme.seed._runner import Subprocesses
from heinzel_acme.seed._service import SeedService, command_of

pytestmark = pytest.mark.unit


class Fake(Subprocesses):
    """Answers like the CLIs would, records every command and never runs one."""

    def __init__(self, fail_on: str | None = None):
        self.calls: list[list[str]] = []
        self.fail_on = fail_on

    def run(self, tool, args):
        self.calls.append([tool, *args])
        if self.fail_on and self.fail_on in args:
            msg = f"{tool} failed"
            raise HeinzelError(msg)
        if tool == "gws":
            name = json.loads(args[args.index("--json") + 1])["name"]
            return json.dumps({"id": f"id-{name.split()[-1].lower()}"})
        return "{}"


def service(tmp_path, commands=None):
    return SeedService(commands or Fake(), workdir=lambda: str(tmp_path))


def test_a_dry_run_runs_nothing_and_shows_every_step(tmp_path):
    fake = Fake()
    result = service(tmp_path, fake).seed(owner="ada-example", email="ada@example.com", only=[], yes=False)
    assert result.dry_run
    assert fake.calls == []
    assert {step.status for step in result.steps} == {"planned"}
    assert result.next == ["hz acme seed --yes"]
    assert list(tmp_path.iterdir()) == []


def test_yes_without_the_options_it_needs_stays_a_dry_run(tmp_path):
    fake = Fake()
    result = service(tmp_path, fake).seed(owner=None, email=None, only=["github", "jira"], yes=True)
    assert result.dry_run
    assert fake.calls == []
    assert result.missing == ["--github-owner", "--email"]
    assert result.next == [
        "hz acme seed --only github --only jira --github-owner <your-github-login> --email <your-atlassian-email> --yes"
    ]


def test_yes_carries_out_the_plan_in_order_and_names_what_it_made(tmp_path):
    fake = Fake()
    result = service(tmp_path, fake).seed(owner="ada-example", email="ada@example.com", only=[], yes=True)
    assert not result.dry_run
    assert {step.status for step in result.steps} == {"done"}
    assert fake.calls[0][:4] == ["gh", "repo", "create", "ada-example/acme-checkout"]
    assert (tmp_path / "project.json").is_file()
    assert (tmp_path / "acme-checkout" / "src" / "cards" / "list.md").is_file()
    assert result.refs == {
        "weekly-report": "id-report",
        "okr": "id-q4",
        "engineering-tracker": "id-tracker",
        "code-repo": "ada-example/acme-checkout",
        "tracker-project": "CHK",
    }
    assert "--asset tracker-project=CHK" in result.next[0]
    assert "{workdir}" not in json.dumps([step.command for step in result.steps])


def test_the_first_failure_stops_the_rest(tmp_path):
    fake = Fake(fail_on="clone")
    result = service(tmp_path, fake).seed(owner="ada-example", email=None, only=["github"], yes=True)
    statuses = [step.status for step in result.steps]
    assert statuses[:3] == ["done", "failed", "not run"]
    assert set(statuses[2:]) == {"not run"}
    assert "failed" in result.steps[1].detail
    assert len(fake.calls) == 2
    assert result.next[0].startswith("Fix what failed")


def test_an_answer_without_an_id_fails_that_step(tmp_path):
    class NoIds(Fake):
        def run(self, tool, args):
            return "[]"

    result = service(tmp_path, NoIds()).seed(owner=None, email=None, only=["google"], yes=True)
    assert [s.status for s in result.steps][:2] == ["done", "failed"]


def test_an_unknown_part_is_refused(tmp_path):
    with pytest.raises(HeinzelError, match="slack"):
        service(tmp_path).seed(owner=None, email=None, only=["slack"], yes=False)


def test_the_real_clis_never_run_in_a_test_session(tmp_path):
    with pytest.raises(HeinzelError, match="never runs the real CLIs"):
        service(tmp_path, Subprocesses()).seed(owner="o", email=None, only=["github"], yes=True)


def test_commands_read_like_a_shell_line():
    step = Step(summary="s", tool="git", args=("-C", "{workdir}/x y", "status"))
    assert command_of(step, "/work") == "git -C '/work/x y' status"
    assert command_of(Step(summary="s", tool="file", path="{workdir}/a.json", content="")) == "write {workdir}/a.json"
