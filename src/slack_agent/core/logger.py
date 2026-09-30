from __future__ import annotations

import contextvars
import logging
import re

current_request_id: contextvars.ContextVar[str] = contextvars.ContextVar(
    "current_request_id", default=""
)

_SECRET_PATTERN = re.compile(r"(xoxb-[a-zA-Z0-9-]+|xapp-[a-zA-Z0-9-]+|sk-or-[a-zA-Z0-9-]+)")


class SecretMaskingFilter(logging.Filter):
    """Logging filter that redacts Slack tokens and LLM API keys from log records."""

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            record.msg = _SECRET_PATTERN.sub("[REDACTED_SECRET]", record.msg)

        req_id = current_request_id.get()
        if req_id and not hasattr(record, "request_id"):
            record.request_id = req_id

        return True


def setup_logging(log_level: str = "INFO") -> None:
    """Configure root logger with structured formatting and secret masking."""
    formatter = logging.Formatter("[%(asctime)s][%(levelname)s][%(name)s] %(message)s")

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    handler.addFilter(SecretMaskingFilter())

    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper(), logging.INFO))
    root_logger.handlers = [handler]


def get_logger(name: str) -> logging.Logger:
    """Obtain a namespaced logger instance."""
    logger = logging.getLogger(name)
    logger.addFilter(SecretMaskingFilter())

    return logger
