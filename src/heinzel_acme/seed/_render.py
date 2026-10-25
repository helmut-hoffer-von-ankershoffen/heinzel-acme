"""How `hz acme seed` looks in a terminal: the notice, every step with its command, and what to run next."""

from rich.console import Group, RenderableType
from rich.table import Table
from rich.text import Text

from heinzel_acme.seed._models import SeedPlan

MARKS = {"planned": "·", "done": "✓", "failed": "✗", "not run": "-"}


def render(plan: SeedPlan) -> RenderableType:
    """The plan as people read it: what runs where, and what happened."""
    parts: list[RenderableType] = [Text(plan.notice, style="bold yellow")]
    head = "Dry run: nothing was run." if plan.dry_run else f"Seeded into your accounts; files in {plan.workdir}."
    parts.append(Text(head))
    table = Table(show_header=True, header_style="bold", box=None, pad_edge=False)
    for column in ("", "#", "what", "command"):
        table.add_column(column, overflow="fold")
    for step in plan.steps:
        where = "remote" if step.remote else "local"
        what = f"{step.summary} ({where})" + (f"\n  {step.detail}" if step.detail else "")
        table.add_row(MARKS[step.status], str(step.number), what, step.command)
    parts.append(table)
    if plan.missing:
        parts.append(Text(f"--yes also needs: {', '.join(plan.missing)}", style="yellow"))
    for name, ref in plan.refs.items():
        parts.append(Text(f"{name}: {ref}"))
    parts += [Text("Next:", style="bold"), *(Text(f"  {command}") for command in plan.next)]
    return Group(*parts)
