"""Stand-ins for what Core ships with the 0.9.43 release (ADR 0159, 0160, 0161): exact copies of Core's classes.

`_compat` uses Core's own class wherever the installed Core has it and these only where it doesn't, so moving the
minimum to that release makes this file a pure delete. Each class here is copied from Core, behaviour and messages
included; keep it that way, or the plugin behaves differently on an older Core than on the one it targets.
"""

import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, Self, cast

from heinzel import HeinzelError, clean_text
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, StringConstraints, ValidationError, model_validator

# ADR 0159: refusing what a connector can't do (heinzel.kernel._capabilities).


class NotSupportedError(HeinzelError):
    """A capability method this connector can't do, as Core's `NotSupportedError`."""

    def __init__(self, capability: str, method: str, reason: str = "") -> None:
        """Say which method of which capability this connector can't do, and why if `reason` says."""
        self.capability = capability
        self.method = method
        self.reason = reason
        why = f": {reason}" if reason else ""
        super().__init__(f"This {capability} connector can't {method.replace('_', ' ')}{why}.")


# ADR 0159: AI models (heinzel.kernel._ai_models).

MODEL_ID_PATTERN = r"^[A-Za-z0-9][A-Za-z0-9._:/@+-]{0,199}$"
ModelId = Annotated[str, StringConstraints(pattern=MODEL_ID_PATTERN)]
Effort = Literal["low", "medium", "high", "xhigh", "max"]
Thinking = Literal["adaptive", "budget"]


class ModelOffer(BaseModel):
    """One model a plugin offers, as Core's `ModelOffer`: only `id` is required; frozen; unknown fields ignored."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: ModelId
    title: str = Field(default="", max_length=200)
    description: str = Field(default="", max_length=500)
    aliases: list[ModelId] = Field(default_factory=list[str])
    context_window: int | None = Field(default=None, ge=1)
    efforts: list[Effort] = Field(default_factory=list[Effort])
    tools: bool = True
    thinking: Thinking | None = None
    available: bool = True

    @property
    def label(self) -> str:
        """What people see: its title, else its id."""
        return self.title or self.id


class ModelUnavailableError(HeinzelError):
    """A model isn't offered or doesn't answer now; the message names models to pick instead, as Core's."""

    def __init__(self, model_id: str, others: list[str] | None = None, reason: str = "") -> None:
        """Say which model is unavailable, why in a few words, and which to pick instead."""
        self.model_id = model_id
        self.others = list(others or [])
        why = f" ({reason})" if reason else ""
        if self.others:
            also = f" (also offered: {', '.join(self.others[1:5])})" if len(self.others) > 1 else ""
            instead = f" Pick another: hz system config set ai.access.plugin_model {self.others[0]}{also}"
        else:
            instead = " No other model is offered now."
        super().__init__(f"The model {model_id} is unavailable{why}.{instead}")


# ADR 0160: the chat self channel (heinzel.kernel._protocols).


class SelfMessage(BaseModel):
    """What `Chat.notify_self` sent to the user's own direct messages, as Core's."""

    id: str
    thread: str
    url: str | None = None


class SelfAnswer(BaseModel):
    """How the user answered a `Chat.ask_self` question, or that nobody did in time, as Core's."""

    model_config = ConfigDict(frozen=True)

    thread: str | None = None
    text: str = ""
    option: str | None = None
    timed_out: bool = False

    @model_validator(mode="after")
    def _consistent(self) -> Self:
        if self.timed_out and (self.text or self.option is not None):
            msg = "A timed-out answer carries no text and no option"
            raise ValueError(msg)
        if not self.timed_out and not self.text.strip() and self.option is None:
            msg = "An answer carries text or an option"
            raise ValueError(msg)
        return self

    @property
    def answered_by_option(self) -> bool:
        """Whether the user chose one of the offered options rather than typing a reply."""
        return self.option is not None


# ADR 0161: several document sources (heinzel.kernel._protocols).


class DocumentHit(BaseModel):
    """A document a search found, as Core's: enough to show it and to read it, not its text."""

    ref: str
    title: str
    url: str | None = None
    snippet: str | None = None
    updated_at: AwareDatetime | None = None
    source: str | None = None


# ADR 0159: MCP-backed connectors (heinzel.connectors.mcp).

DETAIL_LIMIT = 300


class McpConnectorError(HeinzelError):
    """The MCP server didn't start, didn't answer in time, or answered with an error; as Core's."""


@dataclass(frozen=True, slots=True)
class McpTool:
    """A tool the connector expects: its name, the mode it acts in, and other names the server may give it."""

    name: str
    mode: Literal["read", "write"] = "read"
    aliases: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Refuse a mode other than read or write.

        Raises:
            ValueError: If `mode` is neither.
        """
        if self.mode not in {"read", "write"}:
            msg = f"McpTool {self.name!r}: mode must be 'read' or 'write', not {self.mode!r}"
            raise ValueError(msg)


@dataclass(frozen=True, slots=True)
class UntrustedMarker:
    """How a server marks untrusted content, as Core's: a start, an end and `stray`, regular expressions.

    Read conservatively: everything from a marker's first start or end to its last one is untrusted, and an end before
    any start makes everything before it untrusted. Only a `unique` marker, whose end refers to a random id in its
    start, pairs each start with its own end. `stray` matches every start or end; each one is removed.
    """

    start: str
    end: str
    stray: str
    unique: bool = False

    @classmethod
    def literal(cls, start: str, end: str) -> "UntrustedMarker":
        """A marker of two fixed strings, such as `«untrusted-data»` and `«/untrusted-data»`."""
        return cls(re.escape(start), re.escape(end), f"{re.escape(start)}|{re.escape(end)}")


INLINE_UNTRUSTED = UntrustedMarker.literal("«untrusted-data»", "«/untrusted-data»")
ENVELOPE_UNTRUSTED = UntrustedMarker(
    r"<untrusted-(?P<kind>[a-z][a-z0-9-]{0,40})-data-(?P<id>[0-9A-Fa-f-]{8,64})>",
    r"</untrusted-(?P=kind)-data-(?P=id)>",
    r"</?untrusted-[a-z][a-z0-9-]{0,40}-data-[0-9A-Fa-f-]{8,64}>",
    unique=True,
)


@dataclass(frozen=True, slots=True)
class McpResult:
    """A tool's answer, as Core's: its text and data with markers removed and every string cleaned."""

    text: str
    data: Any = None
    untrusted: tuple[str, ...] = ()
    cut: bool = False

    def parse[M: BaseModel](self, model: type[M]) -> M:
        """`data` validated as `model`.

        Raises:
            McpConnectorError: If there is no data, or it doesn't match `model`.
        """
        if self.data is None:
            msg = f"The MCP tool answered no JSON data to read as {model.__name__}."
            raise McpConnectorError(msg)
        try:
            return model.model_validate(self.data)
        except ValidationError as exc:
            msg = f"The MCP tool's answer doesn't match {model.__name__}: {exc.error_count()} problems, first: "
            msg += clean_text(str(exc.errors()[0].get("msg", "")))[:DETAIL_LIMIT]
            raise McpConnectorError(msg) from exc


@dataclass
class _Compiled:
    start: re.Pattern[str]
    pair: re.Pattern[str]
    stray: re.Pattern[str]
    unique: bool

    def spans(self, text: str) -> list[tuple[int, int]]:
        """Where `text` is untrusted by this marker, as (start, end) offsets."""
        if self.unique:
            spans: list[tuple[int, int]] = []
            position = 0
            while (opened := self.start.search(text, position)) is not None:
                paired = self.pair.match(text, opened.start())
                if paired is None:  # never closed: the rest is untrusted
                    return [*spans, (opened.start(), len(text))]
                spans.append((opened.start(), paired.end()))
                position = paired.end()
            return spans
        tokens = list(self.stray.finditer(text))
        if not tokens:
            return []
        first, last = tokens[0], tokens[-1]
        begin = first.start() if self.start.fullmatch(first.group()) else 0
        finish = len(text) if self.start.fullmatch(last.group()) else last.end()
        return [(begin, finish)]


@dataclass
class Unmarker:
    """Removes markers from text and collects what they marked; Core's `_Unmarker`, which `McpConnector` uses.

    Core keeps it private, so the stand-in connector (`_backend.StandInConnector`) uses this copy on any Core.
    """

    markers: Sequence[Any]
    found: list[str] = field(default_factory=list[str])
    _compiled: list[_Compiled] = field(default_factory=list[_Compiled])

    def __post_init__(self) -> None:
        """Compile every marker."""
        self._compiled = [
            _Compiled(
                re.compile(m.start),
                re.compile(f"(?:{m.start}).*?(?:{m.end})", re.DOTALL),
                re.compile(m.stray),
                m.unique,
            )
            for m in self.markers
        ]

    def text(self, text: str) -> str:
        """`text` with every marker removed and cleaned; the regions they mark are kept and recorded as untrusted."""
        spans = sorted(span for marker in self._compiled for span in marker.spans(text))
        merged: list[list[int]] = []
        for begin, finish in spans:
            if merged and begin <= merged[-1][1]:
                merged[-1][1] = max(merged[-1][1], finish)
            else:
                merged.append([begin, finish])
        out: list[str] = []
        position = 0
        for begin, finish in merged:
            out.append(text[position:begin])
            body = self._strip(text[begin:finish])
            self.found.append(clean_text(body))
            out.append(body)
            position = finish
        out.append(text[position:])
        return clean_text(self._strip("".join(out)))

    def _strip(self, text: str) -> str:
        for marker in self._compiled:
            text = marker.stray.sub("", text)
        return text

    def value(self, value: object) -> object:
        """`value` with every string in it unmarked and cleaned, keys too."""
        if isinstance(value, str):
            return self.text(value)
        if isinstance(value, list):
            return [self.value(item) for item in cast("list[object]", value)]
        if isinstance(value, dict):
            return {self.text(str(k)): self.value(v) for k, v in cast("dict[object, object]", value).items()}
        return value
