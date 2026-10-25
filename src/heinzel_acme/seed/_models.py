"""What `hz acme seed` returns: the plan it shows and, after `--yes`, what it did."""

from typing import Literal

from pydantic import BaseModel, Field

NOTICE = (
    "Rehearsal only: this writes the made-up Acme world into YOUR OWN trial accounts (GitHub, Jira, Google). "
    "Never point it at a company account."
)


class StepView(BaseModel):
    """One step of the seed, as it is shown before it runs."""

    number: int = Field(description="Its place in the plan, from 1.")
    summary: str = Field(description="What it does.")
    command: str = Field(description="The command line it runs, or the file it writes.")
    remote: bool = Field(description="Whether it changes something in one of your accounts.")
    status: Literal["planned", "done", "failed", "not run"] = Field(description="Where it stands.")
    detail: str = Field(default="", description="Why it failed, if it did.")


class SeedPlan(BaseModel):
    """The Acme world to seed: every step before it runs, and with `--yes` what happened and what to run next."""

    notice: str = Field(default=NOTICE, description="What this is for, and what it is not for.")
    dry_run: bool = Field(description="True unless `--yes` was given: nothing was run.")
    parts: list[str] = Field(description="The parts seeded: github, jira, google.")
    workdir: str | None = Field(default=None, description="Where the local files and the clone were written.")
    steps: list[StepView] = Field(description="Every step, in order.")
    refs: dict[str, str] = Field(
        default_factory=dict[str, str], description="References of what was created, by asset type."
    )
    missing: list[str] = Field(default_factory=list[str], description="Options `--yes` needs that weren't given.")
    next: list[str] = Field(description="Commands to run next.")
