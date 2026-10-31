"""The plan `hz acme seed` shows and, on `--yes`, carries out: every command, in order, before anything runs.

Pure: building a plan runs nothing. Each step is an argument list for a vendor CLI (`gh`, `git`, `acli`, `gws`) or a
local file to write into the seed's own working directory, which `{workdir}` stands for until the run creates it.
"""

import json
from dataclasses import dataclass

from heinzel_acme._world import (
    CHANGES,
    ITEMS,
    OKR_DOC,
    PROJECT_KEY,
    PROJECT_NAME,
    REPOSITORY,
    TRACKER_SHEET,
    WEEKLY_REPORT_DOC,
)

WORKDIR = "{workdir}"
"""Stands for the seed's temporary working directory in arguments and paths."""
OWNER = "<your-github-login>"
"""Shown in a dry run without `--github-owner`."""
EMAIL = "<your-atlassian-email>"
"""Shown in a dry run without `--email`."""
DOCUMENT = "application/vnd.google-apps.document"
SPREADSHEET = "application/vnd.google-apps.spreadsheet"
PROJECT_TEMPLATE = "com.pyxis.greenhopper.jira:gh-simplified-kanban-classic"
"""A team-managed-style Kanban board; unverified on every Jira Cloud plan, see docs/REHEARSAL.md."""


@dataclass(frozen=True, kw_only=True, slots=True)
class Step:
    """One thing the seed does: run a command, or write a file into its working directory."""

    summary: str
    """What it does, in words."""
    tool: str
    """`gh`, `git`, `acli`, `gws`, or `file` for a local file."""
    args: tuple[str, ...] = ()
    """The command's arguments after the tool, `{workdir}` standing for the working directory."""
    path: str | None = None
    """For `file`: where it is written, under `{workdir}`."""
    content: str | None = None
    """For `file`: what is written."""
    remote: bool = True
    """Whether it changes something in one of the person's accounts."""
    captures: str | None = None
    """The asset whose reference is the `id` in the command's JSON answer, e.g. `weekly-report`."""


def _file(summary: str, name: str, content: str) -> Step:
    return Step(summary=summary, tool="file", path=f"{WORKDIR}/{name}", content=content, remote=False)


def github(owner: str) -> list[Step]:
    """Create the demo repository under `owner` and open its pull requests, merging the ones the world merged."""
    repo = f"{owner}/{REPOSITORY}"
    clone = f"{WORKDIR}/{REPOSITORY}"
    steps = [
        Step(
            summary=f"Create the private demo repository {repo} with a README",
            tool="gh",
            args=("repo", "create", repo, "--private", "--add-readme", "--description",
                  "ACME Checkout: a made-up repository for a Heinzelmännchen rehearsal"),
        ),
        Step(summary="Clone it into the working directory", tool="gh", args=("repo", "clone", repo, clone),
             remote=False),
    ]  # fmt: skip
    for change in CHANGES:
        steps += [
            Step(summary=f"Branch {change.branch}", tool="git", args=("-C", clone, "switch", "-c", change.branch),
                 remote=False),
            _file(f"Write {change.path}", f"{REPOSITORY}/{change.path}", change.content),
            Step(summary="Stage it", tool="git", args=("-C", clone, "add", "--all"), remote=False),
            Step(summary=f"Commit {change.title!r}", tool="git", args=("-C", clone, "commit", "-m", change.title),
                 remote=False),
            Step(summary=f"Push {change.branch}", tool="git", args=("-C", clone, "push", "-u", "origin",
                 change.branch)),
            Step(summary=f"Open the pull request {change.title!r}", tool="gh",
                 args=("pr", "create", "--repo", repo, "--base", "main", "--head", change.branch, "--title",
                       change.title, "--body", change.body)),
        ]  # fmt: skip
        if change.merge:
            steps.append(
                Step(summary=f"Squash-merge {change.branch}", tool="gh",
                     args=("pr", "merge", change.branch, "--repo", repo, "--squash", "--delete-branch")),
            )  # fmt: skip
        steps += [
            Step(summary="Back to main", tool="git", args=("-C", clone, "switch", "main"), remote=False),
            Step(summary="Bring main up to date", tool="git", args=("-C", clone, "pull", "--ff-only"),
                 remote=False),
        ]  # fmt: skip
    return steps


def jira(email: str) -> list[Step]:
    """Create the Checkout project, led by `email`, and its items, moved to the states the world has them in."""
    project = {
        "key": PROJECT_KEY,
        "name": PROJECT_NAME,
        "description": "ACME Checkout: a made-up project for a Heinzelmännchen rehearsal.",
        "leadAccountEmail": email,
        "projectTypeKey": "software",
        "projectTemplateKey": PROJECT_TEMPLATE,
        "assigneeType": "PROJECT_LEAD",
    }
    steps = [
        _file("Write the project definition", "project.json", json.dumps(project, indent=2) + "\n"),
        Step(summary=f"Create the Jira project {PROJECT_KEY} ({PROJECT_NAME})", tool="acli",
             args=("jira", "project", "create", "--from-json", f"{WORKDIR}/project.json")),
    ]  # fmt: skip
    steps += [
        Step(summary=f"Create {item.kind.lower()} {item.summary!r}", tool="acli",
             args=("jira", "workitem", "create", "--project", PROJECT_KEY, "--type", item.kind, "--summary",
                   item.summary, "--assignee", "@me", "--label", f"owner-{item.owner},goal-{item.goal}", "--json"))
        for item in ITEMS
    ]  # fmt: skip
    steps += [
        Step(summary=f"Move {item.summary!r} to {status}", tool="acli",
             args=("jira", "workitem", "transition", "--jql",
                   f'project = {PROJECT_KEY} AND summary ~ "{item.summary}"', "--status", status, "--yes"))
        for status in ("In Progress", "Done")
        for item in ITEMS
        if item.status == status
    ]  # fmt: skip
    return steps


def google() -> list[Step]:
    """Create the weekly report and OKR documents and the engineering tracker sheet, by uploading converted files."""
    files = (
        ("weekly-report", "weekly-report.html", "Checkout weekly report", DOCUMENT, "text/html", WEEKLY_REPORT_DOC),
        ("okr", "okr.html", "ACME Payments OKRs Q4", DOCUMENT, "text/html", OKR_DOC),
        ("engineering-tracker", "tracker.csv", "Checkout engineering tracker", SPREADSHEET, "text/csv",
         TRACKER_SHEET),
    )  # fmt: skip
    steps: list[Step] = []
    for asset, name, title, kind, upload_type, content in files:
        steps += [
            _file(f"Write the {title} content", name, content),
            Step(summary=f"Create the Google {'Sheet' if kind == SPREADSHEET else 'Doc'} {title!r}", tool="gws",
                 args=("drive", "files", "create", "--json", json.dumps({"name": title, "mimeType": kind}),
                       "--upload", f"{WORKDIR}/{name}", "--upload-content-type", upload_type),
                 captures=asset),
        ]  # fmt: skip
    return steps


def plan(owner: str | None, email: str | None, only: frozenset[str]) -> list[Step]:
    """Every step for the parts in `only` (`github`, `jira`, `google`), in that order."""
    steps: list[Step] = []
    if "github" in only:
        steps += github(owner or OWNER)
    if "jira" in only:
        steps += jira(email or EMAIL)
    if "google" in only:
        steps += google()
    return steps
