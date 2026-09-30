from __future__ import annotations

import pytest

from slack_agent.core.errors import (
    ERR_CONFIG_INVALID,
    ERR_SLACK_AUTH_FAILED,
    AppError,
    ErrorCategoryType,
)
from slack_agent.core.result import Result


def test_result_ok_behavior() -> None:
    result: Result[str] = Result.ok("test-value")

    assert result.is_success is True
    assert result.has_error is False
    assert result.value() == "test-value"
    assert result.unwrap_or("fallback") == "test-value"

    with pytest.raises(RuntimeError, match="Attempted to access error on successful Result"):
        result.error()


def test_result_fail_behavior() -> None:
    error = AppError(
        code=ERR_SLACK_AUTH_FAILED,
        message="Authentication token rejected",
        category=ErrorCategoryType.Authentication,
        context={"token_prefix": "xoxb-invalid"},
    )
    result: Result[str] = Result.fail(error)

    assert result.is_success is False
    assert result.has_error is True
    assert result.error() == error
    assert result.unwrap_or("fallback") == "fallback"

    with pytest.raises(RuntimeError, match="Attempted to access value on failed Result"):
        result.value()


def test_app_error_wrap() -> None:
    original_exc = ValueError("Invalid integer value")
    wrapped = AppError.wrap(
        original_exc,
        code=ERR_CONFIG_INVALID,
        message="Config loading failed",
        category=ErrorCategoryType.Configuration,
        context={"field": "proposal_ttl_seconds"},
    )

    assert wrapped.code == ERR_CONFIG_INVALID
    assert wrapped.category == ErrorCategoryType.Configuration
    assert wrapped.cause is original_exc
    assert "field=proposal_ttl_seconds" in str(wrapped)

    dict_repr = wrapped.to_dict()
    assert dict_repr["code"] == ERR_CONFIG_INVALID
    assert dict_repr["cause"] == "Invalid integer value"
    assert dict_repr["category"] == "Configuration"
