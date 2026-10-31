"""`hz acme seed`: REHEARSAL ONLY. Writes the made-up ACME world into the person's own trial accounts.

A dry run by default: it lists every command it would run, and changes nothing. With `--yes` it creates, through the
vendor CLIs logged in as the person, a private demo repository with a few pull requests (`gh`), the Jira project
`CHK` with its items (`acli`), and the weekly report, OKR and engineering tracker documents (`gws`), then prints the
`hz heinzel new` command that names them. Never point it at a company account; never run it in tests (it refuses).
"""

from typing import Annotated

from heinzel import Module
from pydantic import Field

from heinzel_acme.seed._models import SeedPlan
from heinzel_acme.seed._render import render
from heinzel_acme.seed._runner import Subprocesses
from heinzel_acme.seed._service import SeedService

module = Module("seed", "Rehearsal only: seed the made-up ACME world into your own trial accounts.")
module.service(Subprocesses)
module.service(SeedService)


@module.operation(read_only=False, render=render, heads={"cli"})
def seed(
    service: SeedService,
    github_owner: Annotated[
        str | None, Field(description="Your own GitHub login (or a trial org): the demo repository goes there.")
    ] = None,
    email: Annotated[
        str | None, Field(description="The e-mail of your Atlassian trial account: it leads the Jira project.")
    ] = None,
    only: Annotated[
        list[str] | None, Field(description="Seed only these parts: github, jira, google; repeat it. All if omitted.")
    ] = None,
    yes: Annotated[bool, Field(description="Carry out the plan; without it nothing runs.")] = False,
) -> SeedPlan:
    """Rehearsal only: show, then with --yes create, the made-up ACME world in your own trial accounts."""
    return service.seed(owner=github_owner, email=email, only=only or [], yes=yes)


__all__ = ["SeedPlan", "SeedService", "Subprocesses", "module"]
