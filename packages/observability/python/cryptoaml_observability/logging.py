"""Dependency-light JSON logging with request-local trace fields."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import TextIO

from .context import get_current_context

_STANDARD_RECORD_FIELDS = set(logging.LogRecord(None, 0, "", 0, "", (), None).__dict__)


class JsonFormatter(logging.Formatter):
    """Emit stable JSON fields while preserving explicitly supplied extras."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        context = get_current_context()
        if context is not None:
            payload.update(
                {
                    "trace_id": context.trace_id,
                    "span_id": context.span_id,
                    "correlation_id": context.correlation_id,
                }
            )
        for key, value in record.__dict__.items():
            if key not in _STANDARD_RECORD_FIELDS and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False, default=str, sort_keys=True)


def configure_logging(
    level: int = logging.INFO,
    stream: TextIO | None = None,
) -> logging.Logger:
    """Configure the root logger once and return it for application startup."""

    root = logging.getLogger()
    root.setLevel(level)
    handler = next((item for item in root.handlers if getattr(item, "_cryptoaml_json", False)), None)
    if handler is None:
        handler = logging.StreamHandler(stream or sys.stdout)
        handler._cryptoaml_json = True  # type: ignore[attr-defined]
        handler.setFormatter(JsonFormatter())
        root.addHandler(handler)
    return root


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
