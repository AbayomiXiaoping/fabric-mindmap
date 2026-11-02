"""Structured JSON logging with sensitive data redaction."""

from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone
from typing import Any, Mapping

SENSITIVE_KEYWORDS = ("token", "secret", "password", "key", "authorization", "bearer")


def _redact_value(val: Any) -> Any:
    if isinstance(val, str):
        return "***REDACTED***"
    if isinstance(val, dict):
        return {k: (_redact_value(v) if any(kw in k.lower() for kw in SENSITIVE_KEYWORDS) else _redact_value(v)) for k, v in val.items()}
    if isinstance(val, list):
        return [_redact_value(v) for v in val]
    return val


def redact_sensitive(data: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively redacts values for keys matching sensitive keywords."""
    clean: dict[str, Any] = {}
    for k, v in data.items():
        if any(kw in k.lower() for kw in SENSITIVE_KEYWORDS):
            clean[k] = "***REDACTED***"
        elif isinstance(v, dict):
            clean[k] = redact_sensitive(v)
        elif isinstance(v, list):
            clean[k] = [_redact_value(item) for item in v]
        else:
            clean[k] = v
    return clean


class JSONFormatter(logging.Formatter):
    """Custom logging formatter that renders records as single-line JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "line": record.lineno,
        }

        # Add any extra contextual properties
        extras = {
            k: v
            for k, v in record.__dict__.items()
            if k not in logging.LogRecord.__dict__ and not k.startswith("_")
        }
        if extras:
            payload["extra"] = redact_sensitive(extras)

        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)

        return json.dumps(payload, default=str)


def get_logger(name: str) -> logging.Logger:
    """Returns a logger instance configured with JSONFormatter."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JSONFormatter())
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False
    return logger
