"""ACME Lisbon, a made-up site of ACME: the site layer of the reference company (core ADR 0040).

A site sits beside the org tree, under the company: people at Lisbon are in different orgs and teams but share a
time zone, working hours and a weekly rhythm. This plugin brings that rhythm as data (`hz acme-lisbon calendar`) and
recommends its time zone as a setting of its own. A team at Lisbon names it as its site.
"""

from datetime import UTC, datetime
from typing import Annotated

from heinzel import Module, ModuleSettings
from pydantic import Field
from rich.console import Group
from rich.table import Table
from rich.text import Text

from heinzel_acme import LayerAbout, about_layer, layers
from heinzel_acme_lisbon._calendar import LISBON, CalendarView, Occurrence, Ritual, SiteCalendar, upcoming


class LisbonSettings(ModuleSettings):
    """Settings of the site: its table `[acme-lisbon]` in the `hz` config files."""

    time_zone: str = Field(default=LISBON.time_zone, description="The site's IANA time zone.")


module = Module("acme-lisbon", "ACME Lisbon, a made-up site: its time zone, working hours and meeting rhythm.")
layers.declare(module, parent="acme")
module.settings(LisbonSettings)
module.playbook(
    "How ACME Lisbon works: its time zone, working week and the rhythm teams there schedule against.",
    defaults={"acme-lisbon.time_zone": LISBON.time_zone},
)


@module.operation
def info() -> LayerAbout:
    """Show this plugin, its place in ACME's tree and what it brings."""
    return about_layer(
        "heinzel-acme-lisbon",
        module.name,
        [
            (
                "the site calendar (hz acme-lisbon calendar): time zone, working hours, stand-up, planning, demo, "
                "the weekly report deadline"
            )
        ],
    )


def _render_calendar(view: CalendarView) -> Group:
    site = view.calendar
    rhythm = Table(title="Lisbon's weekly rhythm")
    for column in ("Ritual", "Days", "Site time", "Who"):
        rhythm.add_column(column, no_wrap=column in {"Ritual", "Site time"})
    for ritual in site.rituals:
        rhythm.add_row(ritual.name, ", ".join(ritual.days), ritual.at.strftime("%H:%M"), ritual.who)
    upcoming_table = Table(title="Coming up")
    for column in ("Ritual", site.time_zone, "On this computer"):
        upcoming_table.add_column(column)
    for occurrence in view.upcoming:
        upcoming_table.add_row(
            occurrence.name,
            occurrence.site_time.strftime("%a %d %b %H:%M"),
            occurrence.local_time.strftime("%a %d %b %H:%M %Z"),
        )
    start, end = site.working_hours
    return Group(
        Text(f"{site.time_zone} · {', '.join(site.working_days)} · {start:%H:%M}-{end:%H:%M}"),
        rhythm,
        upcoming_table,
    )


@module.operation(render=_render_calendar)
def calendar(
    settings: LisbonSettings,
    days: Annotated[int, Field(ge=1, le=31, description="How many days ahead to show, 1 to 31.")] = 7,
) -> CalendarView:
    """Show the Lisbon site's rhythm and its next meetings and deadlines, at the site and on this machine."""
    site = LISBON.model_copy(update={"time_zone": settings.time_zone})
    now = datetime.now(UTC).astimezone()
    return CalendarView(calendar=site, upcoming=upcoming(site, now, days))


__all__ = ["LISBON", "CalendarView", "LisbonSettings", "Occurrence", "Ritual", "SiteCalendar", "module", "upcoming"]
