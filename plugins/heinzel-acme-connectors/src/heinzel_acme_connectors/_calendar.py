"""The `calendar` adapter (Google-style calendar): events, free/busy, create, move, cancel; answering is not supported.

The gateway offers no tool to answer an invitation, so `respond` is unsupported: people answer in their calendar.
"""

from typing import Any, Literal

from heinzel import (
    Event,
    EventCancellation,
    EventChange,
    EventDraft,
    FreeBusy,
    Participant,
    TimeSpan,
    Window,
    free_busy_people,
)

from heinzel_acme_connectors._base import ConnectorAdapter, bounded, participant, window_arguments
from heinzel_acme_connectors._text import as_dict, as_list, line, moment, optional

RESPONSES: dict[str, Literal["accepted", "declined", "tentative", "pending"]] = {
    "accepted": "accepted",
    "declined": "declined",
    "tentative": "tentative",
    "needsAction": "pending",
}
"""The gateway's answers to an invitation, in Core's words. The gateway marks the user as `self`, as calendars do."""


def _event(value: object) -> Event:
    entry = as_dict(value)
    attendees = as_list(entry.get("attendees"))
    mine = next((as_dict(a) for a in attendees if as_dict(a).get("self") is True), None)
    conference = as_dict(entry.get("conference"))
    organizer = participant(entry.get("organizer")) if entry.get("organizer") else None
    key = line(entry.get("id"), 200)
    return Event(
        id=key,
        title=line(entry.get("summary")),
        start=moment(entry.get("start"), "an event"),
        end=moment(entry.get("end"), "an event"),
        all_day=bool(entry.get("date")),
        organizer=organizer,
        attendees=[participant(a) for a in attendees],
        status=line(entry.get("status"), 40) or "confirmed",
        conference_id=optional(conference.get("id"), 100),
        conference_url=optional(conference.get("url"), 500),
        url=f"https://calendar.acme.example/e/{key}",
        location=optional(entry.get("location")),
        response=RESPONSES.get(str(mine.get("response", "needsAction"))) if mine else None,
        organized_by_user=as_dict(entry.get("organizer")).get("self") is True,
    )


class AcmeCalendar(ConnectorAdapter):
    """The user's calendar through the gateway's `calendar` connector."""

    connector = "calendar"
    capability = "calendar"
    unsupported = frozenset({"respond"})

    def events(self, window: Window) -> list[Event]:
        """The user's events that overlap `window`, cancelled ones included, by start. Mode: read.

        Raises:
            HeinzelError: If the window is backwards or holds too many events.
        """
        found = [_event(e) for e in as_list(self._call("list_events", **window_arguments(window)))]
        return bounded(sorted(found, key=lambda e: e.start), "events")

    def free_busy(self, people: str, window: Window) -> list[FreeBusy]:
        """When the user and `people` (comma-separated addresses; empty: the user) are busy. Mode: read.

        Raises:
            HeinzelError: If the window is backwards.
            ValueError: If `people` holds something that is no plain address.
        """
        addresses = free_busy_people(people)
        answer = as_list(self._call("free_busy", people=addresses, **window_arguments(window)))
        result: list[FreeBusy] = []
        for value in answer:
            entry = as_dict(value)
            spans = [
                TimeSpan(start=moment(as_list(s)[0], "a busy span"), end=moment(as_list(s)[1], "a busy span"))
                for s in as_list(entry.get("busy"))
                if len(as_list(s)) == 2  # noqa: PLR2004 - start and end
            ]
            visible = entry.get("visible") is True
            result.append(
                FreeBusy(
                    who=Participant(email=optional(entry.get("address"), 254)),
                    busy=sorted(spans, key=lambda s: s.start) if visible else [],
                    known=visible,
                )
            )
        return result

    def create_event(self, event: EventDraft) -> Event:
        """Put `event` in the user's calendar, the user organizing it, and invite its attendees. Mode: write."""
        arguments: dict[str, Any] = event.model_dump(mode="json")
        arguments["summary"] = arguments.pop("title")
        if event.all_day:
            arguments["date"] = event.start.date().isoformat()
        return _event(self._call("create_event", **arguments))

    def update_event(self, event: str, change: EventChange) -> Event:
        """Change the event `event` as `change` says. Mode: write.

        Raises:
            HeinzelError: If the gateway knows no such event.
        """
        fields: dict[str, Any] = change.model_dump(mode="json", exclude={"notify"})
        fields["summary"] = fields.pop("title")
        if change.start is not None and change.end is None:
            current = _event(self._call("get_event", id=event))
            fields["end"] = (change.start + (current.end - current.start)).isoformat()
        return _event(self._call("update_event", id=event, change=fields, notify=change.notify))

    def cancel_event(self, event: str, notify: bool) -> EventCancellation:
        """Cancel the event `event` for everyone, telling the attendees if `notify`. Mode: write.

        Raises:
            HeinzelError: If the gateway knows no such event.
        """
        entry = as_dict(self._call("cancel_event", id=event, notify=notify))
        return EventCancellation(id=line(entry.get("id"), 200), notified=entry.get("notified") is True)

    def respond(self, event: str, response: str) -> Event:  # noqa: ARG002 - the protocol's shape; refused
        """Not supported: the gateway can't answer invitations. Mode: write.

        Raises:
            NotSupportedError: Always.
        """
        self._refuse("respond", "the gateway can't answer invitations; answer it in your calendar")
