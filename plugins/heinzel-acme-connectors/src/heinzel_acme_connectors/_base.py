"""What every adapter here shares: its backend, the tool call, and how the gateway's people become `Participant`s."""

from typing import Any, ClassVar, NoReturn

from heinzel import HeinzelError, Participant, Window

from heinzel_acme_connectors._backend import Backend, connect
from heinzel_acme_connectors._compat import NotSupportedError
from heinzel_acme_connectors._text import as_dict, optional

MAX_ITEMS = 500
"""Items one window read returns before it asks for a narrower window: results are never cut (Core, ADR 0028)."""


class ConnectorAdapter:
    """An adapter of one capability over one gateway connector.

    `connector` names the connector in `_backend.CONNECTORS`; `capability` the Core capability served. `unsupported`
    lists the capability's methods this connector can't do (ADR 0159): with a Core that knows the attribute the
    kernel refuses them before the call; until then the methods exist and raise `NotSupportedError` themselves. An
    adapter whose backend is chosen by a setting may set it per instance (the chat adapter does).
    """

    connector: ClassVar[str]
    capability: ClassVar[str]
    unsupported: frozenset[str] = frozenset()

    def __init__(self, backend: Backend | None = None) -> None:
        """Build the adapter on `backend`; the kernel passes nothing, so it connects to its own connector."""
        self._backend = backend if backend is not None else connect(self.connector)

    def _call(self, tool: str, **arguments: Any) -> Any:  # noqa: ANN401 - a tool answers JSON
        return self._backend.call(tool, arguments).data

    def _refuse(self, method: str, reason: str) -> NoReturn:
        """Refuse `method` of this adapter's capability, saying why.

        Raises:
            NotSupportedError: Always.
        """
        raise NotSupportedError(self.capability, method, reason)


def window_arguments(window: Window) -> dict[str, str]:
    """`window` as the gateway's `since` and `until` arguments.

    Raises:
        HeinzelError: If the window ends before it starts.
    """
    if window.until < window.since:
        msg = f"The window starts ({window.since.isoformat()}) after it ends ({window.until.isoformat()})."
        raise HeinzelError(msg)
    return {"since": window.since.isoformat(), "until": window.until.isoformat()}


def bounded[T](items: list[T], what: str) -> list[T]:
    """`items`, or an error asking for a narrower window when there are more than `MAX_ITEMS`.

    Raises:
        HeinzelError: If there are more than `MAX_ITEMS`.
    """
    if len(items) > MAX_ITEMS:
        msg = f"More than {MAX_ITEMS} {what} in this window; ask for a narrower window."
        raise HeinzelError(msg)
    return items


def participant(value: object) -> Participant:
    """A gateway person (`{"name", "address"}`) as a `Participant`; the address in lower case."""
    person = as_dict(value)
    address = optional(person.get("address"), 254)
    return Participant(name=optional(person.get("name"), 200), email=address.lower() if address else None)
