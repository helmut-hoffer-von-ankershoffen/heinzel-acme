"""The `directory` adapter: who people are and who reports to whom, from a directory of record (read only)."""

from heinzel import Person, Relation

from heinzel_acme_connectors._base import ConnectorAdapter, participant
from heinzel_acme_connectors._text import as_dict, as_list, optional


def _relation(value: object) -> Relation:
    entry = as_dict(value)
    return Relation(who=participant(entry), login=optional(entry.get("login"), 100))


def _person(value: object) -> Person:
    entry = as_dict(value)
    manager = entry.get("manager")
    return Person(
        who=participant(entry),
        login=optional(entry.get("login"), 100),
        title=optional(entry.get("title"), 200),
        department=optional(entry.get("department"), 200),
        team=optional(entry.get("team"), 200),
        manager=_relation(as_dict(manager)) if as_dict(manager) else None,
        reports=[_relation(r) for r in as_list(entry.get("reports"))],
    )


class AcmeDirectory(ConnectorAdapter):
    """People through the gateway's `directory` connector; `person` is a login or an email address."""

    connector = "directory"
    capability = "directory"

    def person(self, person: str) -> Person | None:
        """The person whose login or email is `person`, or None if the directory doesn't know them. Mode: read."""
        found = as_dict(self._call("get_person", person=person))
        return _person(found) if found else None

    def reports(self, person: str) -> list[Person]:
        """The direct reports of `person`, by name; empty if none. Mode: read."""
        found = [_person(p) for p in as_list(self._call("list_reports", person=person))]
        return sorted(found, key=lambda p: p.who.name or "")
