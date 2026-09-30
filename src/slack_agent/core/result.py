from __future__ import annotations

from .errors import AppError


class Result[T]:
    """Monadic container holding either a successful value or a structured AppError."""

    __slots__ = ("_value", "_error", "_is_success")

    def __init__(self, value: T | None, error: AppError | None, is_success: bool) -> None:
        self._value = value
        self._error = error
        self._is_success = is_success

    @classmethod
    def ok(cls, value: T) -> Result[T]:
        """Construct a successful Result containing a value."""
        return cls(value=value, error=None, is_success=True)

    @classmethod
    def fail(cls, error: AppError) -> Result[T]:
        """Construct a failed Result containing an AppError."""
        return cls(value=None, error=error, is_success=False)

    @property
    def is_success(self) -> bool:
        """Return True if the operation succeeded."""
        return self._is_success

    @property
    def has_error(self) -> bool:
        """Return True if the operation failed with an error."""
        return not self._is_success

    def value(self) -> T:
        """
        Unwrap the success value.

        GUARD RULE: The caller MUST verify `if result.has_error:` before calling value().
        """
        if self.has_error or self._value is None:
            error_details = str(self._error) if self._error is not None else "Unknown error"
            raise RuntimeError(f"Attempted to access value on failed Result: {error_details}")

        return self._value

    def error(self) -> AppError:
        """Return the AppError instance. Only valid when has_error is True."""
        if self._error is None:
            raise RuntimeError("Attempted to access error on successful Result")

        return self._error

    def unwrap_or(self, default: T) -> T:
        """Return value if successful, otherwise return the provided default."""
        if self._is_success and self._value is not None:
            return self._value

        return default
