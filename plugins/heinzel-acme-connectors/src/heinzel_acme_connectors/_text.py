"""Gateway values as safe strings: every string an adapter returns passes through `clean_text` (Core, ADR 0028).

The backend has already taken the gateway's untrusted-content markers off (Core's rules); what remains is still data
written by people outside this process, never an instruction. These helpers also guard the shapes: a gateway answer
is untrusted too, so a missing or mistyped field becomes an empty value instead of an exception deep in a model.
"""

from datetime import datetime
from typing import Any, cast

from heinzel import HeinzelError, clean_text


def text(value: object, limit: int = 20_000) -> str:
    """`value` as cleaned text, cut at `limit` characters with an ellipsis; a non-string is empty."""
    if not isinstance(value, str):
        return ""
    cleaned = clean_text(value).strip()
    return cleaned if len(cleaned) <= limit else cleaned[: limit - 1].rstrip() + "…"


def line(value: object, limit: int = 300) -> str:
    """`text` on one line: every run of whitespace becomes one space."""
    return " ".join(text(value, limit * 2).split())[:limit]


def optional(value: object, limit: int = 300) -> str | None:
    """`line`, or None when the gateway gave nothing."""
    return line(value, limit) or None


def as_dict(value: object) -> dict[str, Any]:
    """`value` if it is a JSON object, else an empty one."""
    return cast("dict[str, Any]", value) if isinstance(value, dict) else {}


def as_list(value: object) -> list[Any]:
    """`value` if it is a JSON array, else an empty list."""
    return cast("list[Any]", value) if isinstance(value, list) else []  # type: ignore[redundant-cast]


def moment(value: object, what: str) -> datetime:
    """An aware timestamp from an ISO 8601 string.

    Raises:
        HeinzelError: If the gateway sent no aware timestamp: the adapter can't place the item in time.
    """
    try:
        parsed = datetime.fromisoformat(value) if isinstance(value, str) else None
    except ValueError:
        parsed = None
    if parsed is None or parsed.tzinfo is None:
        msg = f"The gateway sent {what} without a timestamp with a time zone; ask its owner to check the tool."
        raise HeinzelError(msg)
    return parsed
