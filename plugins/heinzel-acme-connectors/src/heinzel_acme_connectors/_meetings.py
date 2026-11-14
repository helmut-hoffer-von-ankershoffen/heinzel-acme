"""The `meetings` adapter: ended meetings, and transcripts of the recorded ones only.

The gateway transcribes only meetings that were recorded. `transcripts` lists those, and `transcript` of a meeting
that wasn't recorded raises `NotSupportedError` for that call (a partial gap, so the method isn't in `unsupported`).
"""

from heinzel import HeinzelError, Meeting, Transcript, TranscriptSegment, Window

from heinzel_acme_connectors._base import ConnectorAdapter, bounded, participant, window_arguments
from heinzel_acme_connectors._text import as_dict, as_list, line, moment, optional, text


def _meeting(entry: dict[str, object]) -> Meeting:
    key = line(entry.get("uuid"), 200)
    return Meeting(
        id=key,
        title=line(entry.get("topic")),
        started_at=moment(entry.get("start"), "a meeting"),
        ended_at=moment(entry.get("end"), "a meeting"),
        participants=[participant(p) for p in as_list(entry.get("participants"))],
        conference_id=optional(entry.get("number"), 100),
        url=f"https://meet.acme.example/recordings/{key}" if entry.get("recorded") is True else None,
        has_transcript=entry.get("recorded") is True,
    )


def _transcript(entry: dict[str, object]) -> Transcript:
    segments = [
        TranscriptSegment(
            speaker=optional(as_dict(s).get("speaker"), 200),
            offset_seconds=max(0.0, float(as_dict(s).get("offset") or 0)),
            text=text(as_dict(s).get("text")),
        )
        for s in as_list(entry.get("segments"))
    ]
    return Transcript(meeting=_meeting(entry), language=optional(entry.get("language"), 35), segments=segments)


class AcmeMeetings(ConnectorAdapter):
    """Meetings through the gateway's `meetings` connector."""

    connector = "meetings"
    capability = "meetings"

    def _ended(self, window: Window) -> list[dict[str, object]]:
        found = [as_dict(m) for m in as_list(self._call("list_meetings", **window_arguments(window)))]
        return bounded(sorted(found, key=lambda m: str(m.get("end"))), "meetings")

    def ended(self, window: Window) -> list[Meeting]:
        """The user's meetings that ended within `window`, oldest first. Mode: read.

        Raises:
            HeinzelError: If the window is backwards or holds too many meetings.
        """
        return [_meeting(m) for m in self._ended(window)]

    def transcripts(self, window: Window) -> list[Transcript]:
        """Transcripts of the recorded meetings that ended within `window`, oldest first. Mode: read.

        Raises:
            HeinzelError: As `ended`.
        """
        recorded = [m for m in self._ended(window) if m.get("recorded") is True]
        return [_transcript(as_dict(self._call("get_transcript", id=m.get("uuid")))) for m in recorded]

    def transcript(self, meeting: str) -> Transcript:
        """The transcript of the meeting `meeting` (a `Meeting.id`), if it was recorded. Mode: read.

        Raises:
            HeinzelError: If the gateway knows no such meeting.
            NotSupportedError: If the meeting wasn't recorded.
        """
        entry = as_dict(self._call("get_transcript", id=meeting))
        if not entry:
            msg = f"No meeting {meeting[:200]!r}; take Meeting.id from `ended`."
            raise HeinzelError(msg)
        if entry.get("recorded") is not True:
            self._refuse("transcript", "only recorded meetings have a transcript, and this one wasn't recorded")
        return _transcript(entry)
