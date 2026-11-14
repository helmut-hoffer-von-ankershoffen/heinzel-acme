"""The `code-host` adapter: merged pull requests, fully dummy (no company gateway connector exists for it yet)."""

from heinzel import PullRequest, Window

from heinzel_acme_connectors._base import ConnectorAdapter, bounded, window_arguments
from heinzel_acme_connectors._text import as_dict, as_list, line, moment, optional


class AcmeCodeHost(ConnectorAdapter):
    """Pull requests through the `code-host` connector; `repository` is `owner/name`."""

    connector = "code-host"
    capability = "code-host"

    def merged_pull_requests(self, repository: str, window: Window) -> list[PullRequest]:
        """Pull requests of `repository` merged within `window`, oldest first. Mode: read.

        Raises:
            HeinzelError: If the window is backwards or holds too many pull requests.
        """
        found: list[PullRequest] = []
        for value in as_list(self._call("list_merged_pull_requests", repo=repository, **window_arguments(window))):
            entry = as_dict(value)
            repo, number = line(entry.get("repo"), 200), int(entry.get("number") or 0)
            found.append(
                PullRequest(
                    repository=repo,
                    number=number,
                    title=line(entry.get("title")),
                    url=f"https://code.acme.example/{repo}/pull/{number}",
                    author=optional(entry.get("author"), 100),
                    merged_at=moment(entry.get("merged"), "a pull request"),
                    labels=[line(x, 100) for x in as_list(entry.get("labels"))],
                )
            )
        return bounded(sorted(found, key=lambda p: p.merged_at), "pull requests")
