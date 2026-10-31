import json

import pytest

from heinzel_acme._world import CHANGES, ITEMS, PEOPLE, PROJECT_KEY
from heinzel_acme.seed._plan import EMAIL, OWNER, WORKDIR, plan

pytestmark = pytest.mark.unit

ALL = frozenset({"github", "jira", "google"})


def test_a_plan_for_every_part_runs_only_the_vendor_clis_and_local_files():
    steps = plan("ada-example", "ada@example.com", ALL)
    assert {step.tool for step in steps} == {"gh", "git", "acli", "gws", "file"}
    assert all(step.content is not None for step in steps if step.tool == "file")
    assert all(str(step.path).startswith(WORKDIR) for step in steps if step.tool == "file")


def test_parts_can_be_seeded_alone_in_a_fixed_order():
    assert {step.tool for step in plan("o", None, frozenset({"jira"}))} == {"acli", "file"}
    tools = [step.tool for step in plan("o", "e@example.com", ALL)]
    assert tools.index("acli") > tools.index("gh")
    assert tools.index("gws") > max(i for i, tool in enumerate(tools) if tool == "acli")


def test_without_owner_and_email_the_plan_shows_what_to_fill_in():
    text = json.dumps([step.args for step in plan(None, None, ALL)])
    assert OWNER in text
    contents = [step.content or "" for step in plan(None, None, ALL)]
    assert any(EMAIL in content for content in contents)


def test_github_opens_a_pull_request_per_change_and_merges_the_merged_ones():
    steps = plan("ada-example", None, frozenset({"github"}))
    creates = [s for s in steps if s.args[:2] == ("pr", "create")]
    merges = [s for s in steps if s.args[:2] == ("pr", "merge")]
    assert len(creates) == len(CHANGES)
    assert len(merges) == len([c for c in CHANGES if c.merge]) >= 3
    assert steps[0].args[:3] == ("repo", "create", "ada-example/acme-checkout")
    assert "--private" in steps[0].args


def test_jira_creates_the_project_its_items_and_moves_them():
    steps = plan(None, "ada@example.com", frozenset({"jira"}))
    project = json.loads(steps[0].content or "")
    assert project["key"] == PROJECT_KEY
    assert project["leadAccountEmail"] == "ada@example.com"
    created = [s for s in steps if s.args[:3] == ("jira", "workitem", "create")]
    assert len(created) == len(ITEMS)
    moved = [s for s in steps if s.args[:3] == ("jira", "workitem", "transition")]
    assert len(moved) == len([i for i in ITEMS if i.status != "To Do"])


def test_google_creates_three_documents_and_captures_their_ids():
    steps = plan(None, None, frozenset({"google"}))
    captured = [s.captures for s in steps if s.captures]
    assert captured == ["weekly-report", "okr", "engineering-tracker"]
    assert all(s.remote for s in steps if s.tool == "gws")


def test_the_world_is_made_up():
    assert all(person.email.endswith("@acme.example") for person in PEOPLE)
    assert {person.role for person in PEOPLE} <= {
        "engineer",
        "engineering-manager",
        "product-manager",
        "program-manager",
    }
