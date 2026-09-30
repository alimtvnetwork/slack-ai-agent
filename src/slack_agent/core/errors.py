from __future__ import annotations

import traceback
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

# Error Code Registry Constants
ERR_CONFIG_INVALID = "E1001"
ERR_VALIDATION_FAILED = "E2001"
ERR_SLACK_AUTH_FAILED = "E3001"
ERR_SIGNATURE_MISMATCH = "E3002"
ERR_STORAGE_LOCKED = "E4001"
ERR_FILE_DOWNLOAD_FAILED = "E5001"
ERR_FILE_PARSE_FAILED = "E5002"
ERR_PDF_RENDER_FAILED = "E5003"
ERR_HTTP_REQUEST_FAILED = "E6001"
ERR_SLACK_RATE_LIMITED = "E7002"
ERR_SLACK_API_ERROR = "E7003"
ERR_SLACK_UPLOAD_FAILED = "E7004"
ERR_LLM_TIMEOUT = "E7501"
ERR_LLM_PROVIDER_ERROR = "E7502"
ERR_PROPOSAL_NOT_FOUND = "E8001"
ERR_PROPOSAL_EXPIRED = "E8002"
ERR_CONCURRENCY_TIMEOUT = "E9001"


class ErrorCategoryType(StrEnum):
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
        """Attach a file or URI path to the context."""
        return self.with_context("Path", path)

    def to_dict(self) -> dict[str, Any]:
        """Serialize AppError to a dictionary for logging and debugging."""
        return {
            "code": self.code,
            "message": self.message,
            "category": self.category.value,
            "cause": str(self.cause) if self.cause else None,
            "context": self.context,
        }

    @classmethod
    def wrap(
        cls,
        cause: Exception,
        code: str,
        message: str,
        *,
        category: ErrorCategoryType = ErrorCategoryType.BusinessLogic,
        context: dict[str, Any] | None = None,
    ) -> AppError:
        """Wrap an underlying exception into an AppError with captured trace."""
        captured_trace = (
            "".join(traceback.format_exception(type(cause), cause, cause.__traceback__))
            if cause.__traceback__
            else "".join(traceback.format_stack()[:-1])
        )

        return cls(
            code=code,
            message=message,
            category=category,
            cause=cause,
            stack_trace=captured_trace,
            context=dict(context) if context else {},
        )
