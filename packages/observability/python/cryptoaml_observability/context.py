"""W3C Trace Context helpers and request-local correlation state."""

from __future__ import annotations

import contextlib
import contextvars
import re
import secrets
from dataclasses import dataclass
from collections.abc import Iterator, Mapping

_TRACEPARENT_PATTERN = re.compile(
    r"^00-([0-9a-f]{32})-([0-9a-f]{16})-([0-9a-f]{2})$"
)
_current_context: contextvars.ContextVar[TraceContext | None] = contextvars.ContextVar(
    "cryptoaml_trace_context", default=None
)


def _new_trace_id() -> str:
    return secrets.token_hex(16)


def _new_span_id() -> str:
    return secrets.token_hex(8)


@dataclass(frozen=True, slots=True)
class TraceContext:
    """The minimum trace state propagated across service boundaries."""

    trace_id: str
    span_id: str
    trace_flags: str = "01"

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[0-9a-f]{32}", self.trace_id) or set(self.trace_id) == {"0"}:
            raise ValueError("trace_id must be 32 non-zero lowercase hex characters")
        if not re.fullmatch(r"[0-9a-f]{16}", self.span_id) or set(self.span_id) == {"0"}:
            raise ValueError("span_id must be 16 non-zero lowercase hex characters")
        if not re.fullmatch(r"[0-9a-f]{2}", self.trace_flags):
            raise ValueError("trace_flags must be two lowercase hex characters")

    @classmethod
    def new(cls) -> "TraceContext":
        return cls(trace_id=_new_trace_id(), span_id=_new_span_id())

    @property
    def correlation_id(self) -> str:
        """Use the trace ID as the stable cross-service correlation key."""

        return self.trace_id

    @property
    def traceparent(self) -> str:
        return f"00-{self.trace_id}-{self.span_id}-{self.trace_flags}"

    def child(self) -> "TraceContext":
        return TraceContext(self.trace_id, _new_span_id(), self.trace_flags)


def parse_traceparent(value: str | None) -> TraceContext | None:
    """Parse a W3C traceparent value; invalid input is rejected safely."""

    if not value:
        return None
    match = _TRACEPARENT_PATTERN.fullmatch(value.strip().lower())
    if match is None:
        return None
    trace_id, span_id, trace_flags = match.groups()
    if set(trace_id) == {"0"} or set(span_id) == {"0"}:
        return None
    return TraceContext(trace_id, span_id, trace_flags)


def resolve_trace_context(headers: Mapping[str, str] | None = None) -> TraceContext:
    """Continue a valid traceparent or create a new root context."""

    headers = headers or {}
    traceparent = next(
        (value for key, value in headers.items() if key.lower() == "traceparent"), None
    )
    return parse_traceparent(traceparent) or TraceContext.new()


def get_current_context() -> TraceContext | None:
    return _current_context.get()


@contextlib.contextmanager
def context_scope(context: TraceContext) -> Iterator[TraceContext]:
    token = _current_context.set(context)
    try:
        yield context
    finally:
        _current_context.reset(token)
