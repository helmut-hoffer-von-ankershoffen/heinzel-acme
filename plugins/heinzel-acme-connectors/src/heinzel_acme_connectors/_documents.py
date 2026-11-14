"""Two `documents` adapters, one per store: a Google-style drive and an Atlassian-style wiki, each with its own host.

ACME keeps documents in two stores, so it brings two adapters, simple and independent: each reads only links to its
own host and its own kind of bare id, declares that host as its `links`, and searches its own store. A Core with
ADR 0161 binds both (`[capabilities] documents = ["acme-connectors-docs", "acme-connectors-wiki"]`), routes each
link to the adapter whose `links` name its host, and fans a search out to both; on an older Core, bind one of them.

Both read only. Neither connector can write a section, so `replace_section`, the capability's only write, is
unsupported and the adapters declare read mode alone. The method still exists and refuses, for Core versions that
check that every method of the capability is there.
"""

import re
from typing import ClassVar
from urllib.parse import urlparse

from heinzel import Document, HeinzelError, SectionReplacement

from heinzel_acme_connectors._base import ConnectorAdapter
from heinzel_acme_connectors._compat import DocumentHit
from heinzel_acme_connectors._text import as_dict, as_list, line, text

MAX_TEXT = 500_000
"""Characters of one document kept."""


class _Store(ConnectorAdapter):
    """One document store: its host and path, how its bare ids look, and the tool and fields it answers with."""

    capability = "documents"
    unsupported = frozenset({"replace_section"})
    host: ClassVar[str]
    prefix: ClassVar[str]
    ids: ClassVar[re.Pattern[str]]
    tool: ClassVar[str]
    search_tool: ClassVar[str]
    title_field: ClassVar[str]
    body_field: ClassVar[str]

    def _key(self, ref: str) -> str:
        ref = ref.strip()
        if "://" in ref:
            link = urlparse(ref)
            if link.scheme == "https" and link.hostname == self.host and link.path.startswith(self.prefix):
                return link.path.removeprefix(self.prefix).strip("/")
        elif self.ids.fullmatch(ref):
            return ref
        msg = f"{ref[:200]!r} is no document of https://{self.host}; give a link to https://{self.host}{self.prefix}…"
        raise HeinzelError(msg)

    def read(self, ref: str) -> Document:
        """The text of the document `ref`, a link to this store or one of its ids. Mode: read.

        Raises:
            HeinzelError: If `ref` belongs to another store (never fetched) or the store knows no such document.
        """
        key = self._key(ref)
        entry = as_dict(self._call(self.tool, id=key))
        found = line(entry.get("id"), 200) or key
        version = entry.get("version")
        return Document(
            ref=ref,
            title=line(entry.get(self.title_field)),
            text=text(entry.get(self.body_field), MAX_TEXT),
            url=f"https://{self.host}{self.prefix}{found}",
            revision=str(version) if isinstance(version, str | int) and str(version) else None,
        )

    def search(self, query: str, limit: int) -> list[DocumentHit]:
        """Documents of this store that match `query`, best first, at most `limit` (1 to 50). Mode: read.

        Core (ADR 0161) asks every bound documents adapter and labels each hit with its source; `source` stays empty.

        Raises:
            HeinzelError: If `limit` is out of range.
        """
        if not 1 <= limit <= 50:  # noqa: PLR2004 - Core's bound
            msg = f"Ask for 1 to 50 documents, not {limit}."
            raise HeinzelError(msg)
        hits: list[DocumentHit] = []
        for value in as_list(self._call(self.search_tool, query=query, limit=limit))[:limit]:
            entry = as_dict(value)
            key = line(entry.get("id"), 200)
            hits.append(
                DocumentHit(
                    ref=f"https://{self.host}{self.prefix}{key}",
                    title=line(entry.get(self.title_field)),
                    url=f"https://{self.host}{self.prefix}{key}",
                    snippet=line(entry.get(self.body_field), 200) or None,
                )
            )
        return hits

    def replace_section(self, ref: str, marker: str, text: str) -> SectionReplacement:  # noqa: ARG002
        """Not supported: the store can't write a section. Mode: write.

        Raises:
            NotSupportedError: Always.
        """
        self._refuse("replace_section", "the gateway reads documents but can't write them")


class AcmeDocs(_Store):
    """Files in ACME's Google-style drive (`docs` connector): `https://docs.acme.example/d/<id>` or a `doc-…` id."""

    connector = "docs"
    host = "docs.acme.example"
    prefix = "/d/"
    ids = re.compile(r"doc-[a-z0-9-]{1,80}")
    tool = "get_document"
    search_tool = "search_documents"
    title_field = "name"
    body_field = "body"


class AcmeWiki(_Store):
    """Pages in ACME's Atlassian-style wiki (`wiki` connector): `https://wiki.acme.example/pages/<id>` or a page id."""

    connector = "wiki"
    host = "wiki.acme.example"
    prefix = "/pages/"
    ids = re.compile(r"[0-9]{1,20}")
    tool = "get_page"
    search_tool = "search_pages"
    title_field = "title"
    body_field = "storage"
