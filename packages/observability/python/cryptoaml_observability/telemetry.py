"""OpenTelemetry API seam with a safe no-op fallback for local bootstrap."""

from __future__ import annotations

from contextlib import nullcontext
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TelemetryConfig:
    service_name: str
    enabled: bool = True


class Telemetry:
    def __init__(self, tracer: Any = None, enabled: bool = False):
        self._tracer = tracer
        self.enabled = enabled and tracer is not None

    def span(self, name: str, attributes: dict[str, object] | None = None):
        if not self.enabled:
            return nullcontext()
        span = self._tracer.start_as_current_span(name)
        if attributes:
            # The SDK applies attributes when the context manager is entered.
            return _SpanWithAttributes(span, attributes)
        return span


class _SpanWithAttributes:
    def __init__(self, span_context: Any, attributes: dict[str, object]):
        self._span_context = span_context
        self._attributes = attributes
        self._span = None

    def __enter__(self):
        self._span = self._span_context.__enter__()
        for key, value in self._attributes.items():
            self._span.set_attribute(key, value)
        return self._span

    def __exit__(self, *args):
        return self._span_context.__exit__(*args)


def configure_telemetry(config: TelemetryConfig) -> Telemetry:
    """Use an installed OpenTelemetry tracer, otherwise remain dependency-light."""

    if not config.enabled:
        return Telemetry()
    try:
        from opentelemetry import trace
    except ImportError:
        return Telemetry()
    return Telemetry(trace.get_tracer(config.service_name), enabled=True)
