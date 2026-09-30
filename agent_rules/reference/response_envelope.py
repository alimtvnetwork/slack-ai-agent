from __future__ import annotations

from typing import Any, Generic, TypeVar
from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class StatusBlock(BaseModel):
    """Execution status block within the Universal Response Envelope."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    is_success: bool = Field(..., alias="IsSuccess")
    code: int = Field(..., alias="Code")
    message: str = Field(..., alias="Message")


class ErrorDetailBlock(BaseModel):
    """Structured error details block within the Universal Response Envelope."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    error_code: str = Field(..., alias="ErrorCode")
    error_type: str = Field(..., alias="ErrorType")
    detail: str = Field(..., alias="Detail")
    stack_trace: str = Field(default="", alias="StackTrace")


class UniversalResponseEnvelope(BaseModel, Generic[T]):
    """Standardized response envelope returned across all system and service boundaries."""

    model_config = ConfigDict(frozen=True, populate_by_name=True)

    status: StatusBlock = Field(..., alias="Status")
    attributes: dict[str, Any] = Field(default_factory=dict, alias="Attributes")
    results: list[T] = Field(default_factory=list, alias="Results")
    error: ErrorDetailBlock | None = Field(default=None, alias="Error")

    @classmethod
    def success(
        cls,
        results: list[T],
        message: str = "OK",
        code: int = 200,
        attributes: dict[str, Any] | None = None,
    ) -> UniversalResponseEnvelope[T]:
        """Construct a successful envelope with results list."""
        status_block = StatusBlock(is_success=True, code=code, message=message)

        return cls(
            status=status_block,
            attributes=dict(attributes) if attributes else {},
            results=results,
            error=None,
        )

    @classmethod
    def failure(
        cls,
        error_code: str,
        error_type: str,
        detail: str,
        code: int = 500,
        message: str = "Internal Error",
        stack_trace: str = "",
        attributes: dict[str, Any] | None = None,
    ) -> UniversalResponseEnvelope[T]:
        """Construct a failure envelope with error block."""
        status_block = StatusBlock(is_success=False, code=code, message=message)
        error_block = ErrorDetailBlock(
            error_code=error_code,
            error_type=error_type,
            detail=detail,
            stack_trace=stack_trace,
        )

        return cls(
            status=status_block,
            attributes=dict(attributes) if attributes else {},
            results=[],
            error=error_block,
        )
