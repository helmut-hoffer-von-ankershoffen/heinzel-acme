"""Untrusted-content markers a company MCP gateway puts around text people wrote, and how they come off.

A gateway marks what it could not vouch for: a short field inline (`«untrusted-data»…«/untrusted-data»`), a mail body
in an envelope whose tag carries a fresh UUID (`<untrusted-mail-data-UUID>…</untrusted-mail-data-UUID>`), so text
inside can't close it without guessing the UUID. A connector takes the markers off, notes that the answer held
untrusted content, and removes any stray or forged marker that is left, so nothing downstream mistakes one for a
boundary. What was inside stays data: adapters still pass every string through `clean_text`.

This is the local stand-in for ADR 0159 Head B's public helper (`UntrustedMarker`, `INLINE_UNTRUSTED`,
`ENVELOPE_UNTRUSTED` in `heinzel.connectors.mcp`, not released yet); when the minimum Core has it, `_backend` uses
Core's and this file goes.
"""

import re
from dataclasses import dataclass, field
from typing import Any, cast


@dataclass(frozen=True)
class UntrustedMarker:
    """One kind of marker: regexes for its start and its end; `(?P=…)` in `end` may refer to a group in `start`."""

    start: str
    end: str
    _pair: re.Pattern[str] = field(init=False, repr=False, compare=False)
    _stray: re.Pattern[str] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        """Compile the pair (shortest body, across lines) and the pattern of a lone start or end."""
        object.__setattr__(self, "_pair", re.compile(f"{self.start}(?P<body>.*?){self.end}", re.DOTALL))
        lone_end = re.sub(r"\(\?P=\w+\)", r"[^>]*", self.end)  # a lone end tag has no start to refer to
        object.__setattr__(self, "_stray", re.compile(f"{_ungrouped(self.start)}|{_ungrouped(lone_end)}"))

    def unwrap(self, value: str) -> tuple[str, tuple[str, ...]]:
        """`value` with each marked span replaced by its body, and the bodies, in order."""
        found: list[str] = []

        def body(match: re.Match[str]) -> str:
            found.append(match.group("body"))
            return match.group("body")

        return self._pair.sub(body, value), tuple(found)

    def strip(self, value: str) -> str:
        """`value` without any start or end of this marker that is still there."""
        return self._stray.sub("", value)


def _ungrouped(pattern: str) -> str:
    return re.sub(r"\(\?P<\w+>", "(?:", pattern)


INLINE_UNTRUSTED = UntrustedMarker(start="«untrusted-data»", end="«/untrusted-data»")
"""A short field, marked inline."""
ENVELOPE_UNTRUSTED = UntrustedMarker(
    start=r"<untrusted-mail-data-(?P<envelope>[0-9a-fA-F-]{8,64})>",
    end=r"</untrusted-mail-data-(?P=envelope)>",
)
"""A mail body in an envelope; the closing tag must repeat the opening tag's UUID."""


def unwrap(value: object, markers: tuple[UntrustedMarker, ...]) -> tuple[Any, tuple[str, ...]]:
    """`value` (any JSON) with every string unwrapped and stripped of strays, and the marked segments, in order.

    The segments are what `McpResult.untrusted` holds in Head B: they are stripped of stray markers too.
    """
    if isinstance(value, str):
        segments: list[str] = []
        for marker in markers:
            value, found = marker.unwrap(value)
            segments.extend(found)
        for marker in markers:
            value = marker.strip(value)
            segments = [marker.strip(segment) for segment in segments]
        return value, tuple(segments)
    if isinstance(value, list):
        items = [unwrap(item, markers) for item in cast("list[Any]", value)]  # type: ignore[redundant-cast]
        return [item for item, _ in items], tuple(s for _, found in items for s in found)
    if isinstance(value, dict):
        pairs = {key: unwrap(item, markers) for key, item in cast("dict[str, Any]", value).items()}
        return {key: item for key, (item, _) in pairs.items()}, tuple(s for _, found in pairs.values() for s in found)
    return value, ()
