from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class ErrorCategoryType(str, Enum):
    """Domain category classifications for structured errors."""

    Configuration = "Configuration"
    Validation = "Validation"
    Authentication = "Authentication"
    Database = "Database"
    FileSystem = "FileSystem"
    Network = "Network"
    SlackApi = "SlackApi"
    LlmService = "LlmService"
    BusinessLogic = "BusinessLogic"
    Concurrency = "Concurrency"
    Cache = "Cache"


@dataclass(frozen=True)
class AppError(Exception):
    """Canonical structured domain error representing an operation failure."""

    code: str
    message: str
    category: ErrorCategoryType = ErrorCategoryType.BusinessLogic
    cause: Exception | None = None
    stack_trace: str = field(default_factory=lambda: "".join(traceback.format_stack()[:-1]))
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        base_message = f"[{self.code}][{self.category.value}] {self.message}"

        if self.context:
            context_items = [f"{k}={v}" for k, v in sorted(self.context.items())]
            base_message = f"{base_message} | Context: ({', '.join(context_items)})"

        if self.cause:
            cause_type = type(self.cause).__name__
            base_message = f"{base_message} | Caused by: {cause_type}: {self.cause}"

        return base_message

    def with_context(self, key: str, value: Any) -> AppError:
        """Create a new immutable AppError with the appended context key-value pair."""
        updated_context = {**self.context, key: value}

        return AppError(
            code=self.code,
            message=self.message,
            category=self.category,
            cause=self.cause,
            stack_trace=self.stack_trace,
            context=updated_context,
        )

    def with_path(self, path: str) -> AppError:
        """Convenience method to attach a file or URI path to the context."""
        return self.with_context("Path", path)

    @classmethod
    def wrap(
        cls,
        cause: Exception,
        code: str,
        message: str,
        category: ErrorCategoryType = ErrorCategoryType.BusinessLogic,
        context: dict[str, Any] | None = None,
    ) -> AppError:
        """Wrap an underlying exception into an AppError with captured trace."""
        captured_trace = "".join(
            traceback.format_exception(type(cause), cause, cause.__traceback__)
        ) if cause.__traceback__ else "".join(traceback.format_stack()[:-1])

        return cls(
            code=code,
            message=message,
            category=category,
            cause=cause,
            stack_trace=captured_trace,
            context=dict(context) if context else {},
        )
