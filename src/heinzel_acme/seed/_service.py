"""`hz acme seed`: show the plan, and on `--yes` carry it out step by step, stopping at the first failure."""

import json
import os
import shlex
import tempfile
from collections.abc import Callable
from pathlib import Path

from heinzel import HeinzelError

from heinzel_acme._world import PROJECT_KEY, REPOSITORY
from heinzel_acme.seed._models import SeedPlan, StepView
from heinzel_acme.seed._plan import EMAIL, OWNER, WORKDIR, Step, plan
from heinzel_acme.seed._runner import Subprocesses, write

PARTS = ("github", "jira", "google")
TEMPLATE = "acme-payments-checkout:weekly-report"
VALUES = {"--github-owner": OWNER, "--email": EMAIL}
"""What each option needs, as the next command shows it."""


def command_of(step: Step, workdir: str = WORKDIR) -> str:
    """The step as a command line people can read and copy, or the file it writes."""
    if step.tool == "file":
        return f"write {str(step.path).replace(WORKDIR, workdir)}"
    return shlex.join([step.tool, *(arg.replace(WORKDIR, workdir) for arg in step.args)])


def _next(refs: dict[str, str]) -> list[str]:
    assets = " ".join(
        f"--asset {asset}={shlex.quote(refs.get(asset, f'<{asset}>'))}"
        for asset in ("weekly-report", "engineering-tracker", "tracker-project", "code-repo")
    )
    return [
        f"hz workflow new weekly-report --template {TEMPLATE} {assets}",
        "hz workflow run weekly-report --dry-run",
        "hz workflow run weekly-report",
    ]


class SeedService:
    """Seeds the made-up Acme world into the person's own trial accounts, through the vendor CLIs."""

    def __init__(self, commands: Subprocesses, workdir: Callable[[], str] | None = None) -> None:
        """Use `commands` to run the CLIs; `workdir` makes the working directory (a new temporary one by default)."""
        self._commands = commands
        self._workdir = workdir or (lambda: tempfile.mkdtemp(prefix="acme-seed-"))

    def seed(self, *, owner: str | None, email: str | None, only: list[str], yes: bool) -> SeedPlan:
        """The plan for the parts in `only` (all if empty); with `yes` and every option it needs, carry it out.

        Raises:
            HeinzelError: If a part is unknown, or the real CLIs would run inside a test session.
        """
        parts = only or list(PARTS)
        if unknown := [p for p in parts if p not in PARTS]:
            msg = f"Unknown part {unknown[0]!r}; seed one or more of: {', '.join(PARTS)}."
            raise HeinzelError(msg)
        steps = plan(owner, email, frozenset(parts))
        missing = [option for option, part, value in (("--github-owner", "github", owner), ("--email", "jira", email))
                   if part in parts and not value]  # fmt: skip
        result = SeedPlan(
            dry_run=True,
            parts=[p for p in PARTS if p in parts],
            steps=[
                StepView(number=n, summary=s.summary, command=command_of(s), remote=s.remote, status="planned")
                for n, s in enumerate(steps, start=1)
            ],
            missing=missing,
            next=[
                " ".join(
                    ["hz acme seed"]
                    + [f"--only {p}" for p in only]
                    + [f"{option} {VALUES[option]}" for option in missing]
                    + ["--yes"]
                )
            ],
        )
        if not yes or missing:
            return result
        if "PYTEST_CURRENT_TEST" in os.environ and type(self._commands) is Subprocesses:
            msg = "hz acme seed never runs the real CLIs inside a test session; bind a fake Subprocesses."
            raise HeinzelError(msg)
        return self._run(result, steps, owner or "")

    def _run(self, result: SeedPlan, steps: list[Step], owner: str) -> SeedPlan:
        workdir = self._workdir()
        result.dry_run = False
        result.workdir = workdir
        failed = False
        for view, step in zip(result.steps, steps, strict=True):
            view.command = command_of(step, workdir)
            if failed:
                view.status = "not run"
                continue
            try:
                if step.tool == "file":
                    write(Path(str(step.path).replace(WORKDIR, workdir)), step.content or "")
                    out = ""
                else:
                    out = self._commands.run(step.tool, [arg.replace(WORKDIR, workdir) for arg in step.args])
                if step.captures is not None:
                    result.refs[step.captures] = _id(out, step)
            except HeinzelError as exc:
                view.status, view.detail, failed = "failed", str(exc), True
                continue
            view.status = "done"
        if not failed:
            if "github" in result.parts:
                result.refs["code-repo"] = f"{owner}/{REPOSITORY}"
            if "jira" in result.parts:
                result.refs["tracker-project"] = PROJECT_KEY
            result.next = _next(result.refs)
        else:
            result.next = ["Fix what failed (see its detail), then seed only the parts that didn't finish: --only"]
        return result


def _id(out: str, step: Step) -> str:
    """The `id` of what `step` created, from its JSON answer.

    Raises:
        HeinzelError: If the answer has no id.
    """
    try:
        found = json.loads(out).get("id")
    except (ValueError, AttributeError):
        found = None
    if not isinstance(found, str) or not found:
        msg = f"{step.tool} answered without the id of what it created ({step.summary})."
        raise HeinzelError(msg)
    return found
