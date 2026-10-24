"""The Lisbon site's calendar as data: its time zone, working hours and the rhythm of its meetings.

A site layer says when people at a site meet and work, whatever org or team they are in (core ADR 0040). Teams read
it to schedule their contracts: a draft that must be ready before Friday's report is due is scheduled against this
rhythm, in the site's time zone, whatever zone the machine running it is in.
"""

from datetime import date, datetime, time, timedelta
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

DAYS = ("MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN")


class Ritual(BaseModel):
    """A recurring meeting or deadline at the site."""

    name: str = Field(description="What it is.")
    days: list[str] = Field(description="Weekdays it happens on: MON to SUN.")
    at: time = Field(description="Local start time at the site.")
    minutes: int = Field(description="How long it takes; 0 for a deadline.")
    who: str = Field(description="Who it is for.")


class SiteCalendar(BaseModel):
    """A site's working week and rhythm."""

    site: str = Field(description="The site layer.")
    time_zone: str = Field(description="The site's IANA time zone.")
    working_days: list[str] = Field(description="Weekdays people work.")
    working_hours: tuple[time, time] = Field(description="When the working day starts and ends, local time.")
    rituals: list[Ritual] = Field(description="Recurring meetings and deadlines.")


class Occurrence(BaseModel):
    """One upcoming ritual, at the site and on this machine."""

    name: str = Field(description="The ritual.")
    site_time: datetime = Field(description="When, in the site's time zone.")
    local_time: datetime = Field(description="When, in this machine's time zone.")
    minutes: int = Field(description="How long; 0 for a deadline.")


class CalendarView(BaseModel):
    """`hz acme-lisbon calendar`: the site's rhythm and what comes next."""

    calendar: SiteCalendar = Field(description="The rhythm, as data.")
    upcoming: list[Occurrence] = Field(description="Every ritual in the window, earliest first.")


LISBON = SiteCalendar(
    site="acme-lisbon",
    time_zone="Europe/Lisbon",
    working_days=["MON", "TUE", "WED", "THU", "FRI"],
    working_hours=(time(9, 0), time(18, 0)),
    rituals=[
        Ritual(name="Stand-up", days=["MON", "TUE", "WED", "THU", "FRI"], at=time(9, 30), minutes=15, who="each team"),
        Ritual(name="Planning", days=["MON"], at=time(10, 0), minutes=60, who="each team"),
        Ritual(name="Demo", days=["FRI"], at=time(16, 0), minutes=45, who="everyone at the site"),
        Ritual(name="Weekly report draft ready", days=["FRI"], at=time(17, 0), minutes=0, who="report owners"),
        Ritual(name="OKR review", days=["MON"], at=time(14, 0), minutes=30, who="org leads, every second week"),
    ],
)


def upcoming(calendar: SiteCalendar, start: datetime, days: int) -> list[Occurrence]:
    """Every ritual from `start` (aware) for `days` days, earliest first, at the site and in `start`'s zone."""
    zone = ZoneInfo(calendar.time_zone)
    local = start.tzinfo
    first: date = start.astimezone(zone).date()
    found: list[Occurrence] = []
    for offset in range(days + 1):
        day = first + timedelta(days=offset)
        for ritual in calendar.rituals:
            if DAYS[day.weekday()] in ritual.days:
                at = datetime.combine(day, ritual.at, tzinfo=zone)
                if start <= at < start + timedelta(days=days):
                    found.append(
                        Occurrence(
                            name=ritual.name, site_time=at, local_time=at.astimezone(local), minutes=ritual.minutes
                        )
                    )
    return sorted(found, key=lambda o: o.site_time)
