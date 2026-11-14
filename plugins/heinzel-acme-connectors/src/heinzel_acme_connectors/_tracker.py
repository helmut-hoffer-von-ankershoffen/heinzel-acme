"""The `tracker` adapter (Atlassian-style issue tracker): read and write; attaching files is not supported.

The gateway offers no upload tool, so `attach` is unsupported. `claim` is NOT atomic here, unlike Core's protocol
asks: the gateway has no compare-and-set, so the adapter reads the issue, refuses if another actor holds it, then
assigns it. Two claims racing between the read and the write can both succeed; the later one wins. A company that
needs atomic claims needs a gateway tool that assigns only if unassigned. Every write records its actor in a comment.
"""

from typing import Any

from heinzel import Attachment, HeinzelError, Issue, Window

from heinzel_acme_connectors._base import ConnectorAdapter, bounded, window_arguments
from heinzel_acme_connectors._text import as_dict, as_list, line, moment, optional, text

WORKING = "In Progress"
"""The state a claim moves an issue to, in this tracker's words."""
DONE = "Done"


def _issue(value: object) -> Issue:
    entry = as_dict(value)
    key = line(entry.get("key"), 100)
    resolved = entry.get("resolved")
    return Issue(
        key=key,
        title=line(entry.get("summary")),
        url=f"https://tracker.acme.example/browse/{key}",
        state=line(entry.get("status"), 60),
        updated_at=moment(entry.get("updated"), "an issue"),
        assignee=optional(entry.get("assignee"), 200),
        labels=[line(x, 100) for x in as_list(entry.get("labels"))],
        created_at=moment(entry.get("created"), "an issue") if entry.get("created") else None,
        closed_at=moment(resolved, "an issue") if resolved else None,
        reporter=optional(entry.get("reporter"), 200),
        attachments=[
            Attachment(
                name=line(as_dict(a).get("filename"), 200),
                media_type=line(as_dict(a).get("mimeType"), 100) or "application/octet-stream",
                size=max(0, int(as_dict(a).get("size") or 0)),
                ref=line(as_dict(a).get("id"), 200),
            )
            for a in as_list(entry.get("attachments"))
        ],
    )


def _signed(body: str, actor: str) -> str:
    return f"{text(body)}\n\n(for {line(actor, 200)})"


class AcmeTracker(ConnectorAdapter):
    """An issue tracker through the gateway's `tracker` connector."""

    connector = "tracker"
    capability = "tracker"
    unsupported = frozenset({"attach"})

    def issues_updated(self, project: str, window: Window) -> list[Issue]:
        """Issues of `project` updated within `window`, oldest first. Mode: read.

        Raises:
            HeinzelError: If the window is backwards or holds too many issues.
        """
        found = [_issue(i) for i in as_list(self._call("search_issues", project=project, **window_arguments(window)))]
        return bounded(sorted(found, key=lambda i: i.updated_at), "issues")

    def create(self, project: str, title: str, body: str, reporter: str, labels: list[str]) -> Issue:
        """Open a new issue in `project`, asked for by `reporter`. Mode: write."""
        arguments: dict[str, Any] = {"project": project, "summary": title, "reporter": reporter}
        return _issue(self._call("create_issue", **arguments, description=_signed(body, reporter), labels=labels))

    def claim(self, key: str, actor: str) -> Issue:
        """Assign `key` to `actor` and mark it worked on; refuse if another actor holds it. Not atomic. Mode: write.

        Raises:
            HeinzelError: If another actor holds it, or the gateway knows no such issue.
        """
        current = _issue(self._call("get_issue", key=key))
        if current.assignee and current.assignee != actor:
            msg = f"{key} is claimed by {current.assignee}; it stays theirs."
            raise HeinzelError(msg)
        self._call("assign_issue", key=key, assignee=actor)  # check-then-set: see the module docstring
        return _issue(self._call("transition_issue", key=key, status=WORKING, comment=_signed("Claimed.", actor)))

    def transition(self, key: str, state: str, actor: str, note: str | None = None) -> Issue:
        """Move `key` to `state`, adding `note` if given. Mode: write."""
        comment = _signed(note or f"Moved to {state}.", actor)
        return _issue(self._call("transition_issue", key=key, status=state, comment=comment))

    def note(self, key: str, text: str, actor: str) -> Issue:
        """Add the comment `text` to `key`. Mode: write."""
        return _issue(self._call("add_comment", key=key, body=_signed(text, actor)))

    def attach(self, key: str, name: str, data: bytes, media_type: str, actor: str) -> Attachment:  # noqa: ARG002
        """Not supported: the gateway has no upload tool. Mode: write.

        Raises:
            NotSupportedError: Always.
        """
        self._refuse("attach", "the gateway can't upload files; attach it in the tracker")

    def close(self, key: str, actor: str, reason: str) -> Issue:
        """Close `key`, saying why in `reason`. Mode: write."""
        return _issue(self._call("transition_issue", key=key, status=DONE, comment=_signed(reason, actor)))
