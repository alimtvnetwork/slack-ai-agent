# Error Handling Architecture & Standards

> **File:** `agent_rules/03-error-handling-architecture.md`  
> **Source Specs:** `guidelines/02-spec/03-error-manage/`, `guidelines/02-spec/17-consolidated-guidelines/06-error-management.md`, `guidelines/02-spec/17-consolidated-guidelines/34-compiled-simple-coding-guidelines.md`  
> **Authority:** 🔴 **#1 PRIORITY** — Error management is the highest priority specification across the entire repository.  

---

## 1. Core Principles (Zero Tolerance)

1. **🔴 Never Swallow an Error:** Empty `except:`, `except Exception: pass`, or unhandled promise/task rejections are **instant build/PR rejections**. Every exception must be either:
   - Handled explicitly with full contextual logging, OR
   - Wrapped in a structured domain `AppError` and propagated.
2. **🔴 Catch Specific Exceptions Only:** Never write bare `except:` or catch generic `Exception` without immediately re-wrapping into an `AppError`. Always catch the specific exception class (e.g. `SlackApiError`, `pydantic.ValidationError`, `TimeoutError`, `FileNotFoundError`).
3. **🔴 Context on Every Error:** Generic error messages (e.g. `"Failed to process"`, `"File not found"`) without path, entity ID, channel ID, or operation name are **strictly prohibited**.
4. **🔴 No Direct Tuple Multi-Returns:** Do not return `(value, error)` or `(data, bool)`. Return a single monadic container: `Result[T]`.
5. **🔴 Never Cache Errors as Success:** If an operation fails, delete or invalidate the cache entry. Never store an empty result or fallback as a cached success.

---

## 2. Structured Domain Error: `AppError`

All internal, third-party, and network errors must be wrapped in an `AppError` instance. An `AppError` preserves the full root cause, captures stack frames, assigns a registered error code, and attaches structured metadata.

### 2.1 Error Representation

```python
from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class AppError(Exception):
    """Canonical structured domain error representing an operation failure."""

    code: str
    message: str
    cause: Exception | None = None
    stack_trace: str = field(default_factory=lambda: "".join(traceback.format_stack()[:-1]))
    context: dict[str, Any] = field(default_factory=dict)

    def __str__(self) -> str:
        base = f"[{self.code}] {self.message}"
        if self.context:
            context_str = ", ".join(f"{k}={v}" for k, v in self.context.items())
            base = f"{base} | Context: ({context_str})"
        if self.cause:
            base = f"{base} | Caused by: {type(self.cause).__name__}: {self.cause}"
        return base

    def with_context(self, key: str, value: Any) -> AppError:
        """Create a new AppError copy containing the additional context entry."""
        new_context = {**self.context, key: value}
        return AppError(
            code=self.code,
            message=self.message,
            cause=self.cause,
            stack_trace=self.stack_trace,
            context=new_context,
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
        context: dict[str, Any] | None = None,
    ) -> AppError:
        """Wrap an external or stdlib exception into a structured AppError."""
        captured_trace = "".join(
            traceback.format_exception(type(cause), cause, cause.__traceback__)
        ) if cause.__traceback__ else "".join(traceback.format_stack()[:-1])

        return cls(
            code=code,
            message=message,
            cause=cause,
            stack_trace=captured_trace,
            context=dict(context) if context else {},
        )
```

---

## 3. The `Result[T]` Monad Pattern

All service methods, database queries, external Slack API calls, and LLM requests must return a single `Result[T]` object.

### 3.1 `Result[T]` Specification

```python
from __future__ import annotations

from typing import Generic, TypeVar, NoReturn

T = TypeVar("T")


class Result(Generic[T]):
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
        
        GUARD RULE: Caller MUST verify `if result.has_error:` before calling value().
        """
        if self.has_error or self._value is None:
            raise RuntimeError(
                f"Attempted to access value on failed Result: {self._error}"
            )
        return self._value

    def error(self) -> AppError:
        """Return the AppError instance. Only valid if has_error is True."""
        if self._error is None:
            raise RuntimeError("Attempted to access error on successful Result")
        return self._error

    def unwrap_or(self, default: T) -> T:
        """Return value if successful, otherwise return the provided default."""
        return self._value if self._is_success and self._value is not None else default
```

### 3.2 Result Guard Rule (CODE RED 🔴)

Never call `result.value()` without an explicit `if result.has_error:` guard first.

```python
# ❌ CODE RED: Unchecked value access
result = await slack_service.fetch_user_profile(user_id)
user = result.value()  # Crashes or returns None if the API call failed!

# ✅ REQUIRED: Early return on error
result = await slack_service.fetch_user_profile(user_id)
if result.has_error:
    logger.error("Failed to fetch user profile", extra={"Error": str(result.error())})
    return Result.fail(result.error())

user = result.value()
```

---

## 4. Universal Response Envelope

Whenever this Slack bot exposes a REST endpoint (health checks, webhooks, management API) or outputs structured task results, the response **MUST follow the Universal Response Envelope** with PascalCase keys:

### 4.1 Wire Format

```json
{
  "Status": {
    "IsSuccess": true,
    "Code": 200,
    "Message": "OK"
  },
  "Attributes": {
    "RequestedAt": "/slack/events",
    "Duration": "42ms",
    "RequestId": "req_8f14c0a1b2",
    "TeamId": "T12345678"
  },
  "Results": [
    {
      "MessageId": "msg_001",
      "Status": "Processed"
    }
  ]
}
```

### 4.2 Error Envelope Wire Format

```json
{
  "Status": {
    "IsSuccess": false,
    "Code": 500,
    "Message": "Slack API rate limit exceeded"
  },
  "Error": {
    "ErrorCode": "E7002",
    "ErrorType": "SLACK_API_RATE_LIMIT",
    "Detail": "HTTP 429 received from conversations.history",
    "StackTrace": "Traceback (most recent call last):\n  File 'slack_client.py', line 45..."
  },
  "Attributes": {
    "RequestedAt": "/slack/events",
    "RequestId": "req_8f14c0a1b2",
    "ChannelId": "C98765432"
  },
  "Results": []
}
```

---

## 5. Error Code Registry

To prevent collision and establish unambiguous telemetry, error codes are partitioned into domain ranges:

| Code Range | Subsystem / Domain | Description & Examples |
|---|---|---|
| `E1000–E1999` | **Configuration & Startup** | Missing Slack tokens, invalid `.env`, bad config parameters. |
| `E2000–E2999` | **Validation** | Pydantic validation failure, malformed Slack webhook signature. |
| `E3000–E3999` | **Authentication & Security** | Invalid signature hash, expired token, unauthorized user. |
| `E4000–E4999` | **Database & Storage** | SQLite locked, migration failed, query error. |
| `E5000–E5999` | **File System & IO** | File missing, permission denied, atomic write failed. |
| `E6000–E6999` | **Network & HTTP Client** | Connection timeout, DNS failure, unhandled HTTP status. |
| `E7000–E7499` | **Slack API Integration** | Rate limited (`E7002`), channel not found, bot not in channel. |
| `E7500–E7999` | **LLM & AI Services** | Model timeout, token limit exceeded, refusal, provider 5xx. |
| `E8000–E8999` | **Business Logic / Agent** | Agent loop limit reached, unrecognized tool, invalid state. |
| `E9000–E9999` | **Concurrency & Queues** | Queue full, lock acquisition timeout, task cancellation. |
| `E10000–E10999`| **Cache Management** | Cache connection dropped, invalid key format. |

---

## 6. Two-Tier & Session-Based Logging

1. **Request / Session ID:**
   Every incoming Slack event or HTTP request must be tagged with a unique `RequestId` (e.g. `uuid4().hex[:12]`). This ID must be attached to every log line produced while handling that event.
2. **Structured Logging:**
   Log entries must use structured key-value dictionaries, never bare string concatenations:
   ```python
   # ❌ FORBIDDEN: String interpolation in logs
   logger.error(f"Error handling event {event_id}: {err}")

   # ✅ REQUIRED: Structured logging with context and RequestId
   logger.error(
       "Failed to process Slack event",
       extra={
           "RequestId": request_id,
           "EventId": event_id,
           "ChannelId": channel_id,
           "ErrorCode": err.code,
           "ErrorMessage": err.message,
       },
   )
   ```
3. **🔴 Zero Token/Secret Logging:**
   Never log `SLACK_BOT_TOKEN`, `SLACK_SIGNING_SECRET`, user credentials, or raw bearer tokens. Sanitize payloads before writing to disk.
