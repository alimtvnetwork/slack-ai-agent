# Subtask 1.2: Error Handling & Result[T] Monad Architecture

> **Task Reference:** `TASK-01` > `SUBTASK-1.2`  
> **Source Rule:** `agent_rules/03-error-handling-architecture.md`  

---

## 1. Description

Implement the core error handling types and monadic result containers in `src/core/errors.py` and `src/core/result.py`. This ensures zero swallowed errors, structured diagnostic wrapping, and typed single-return value contracts across the entire Slack bot application.

---

## 2. Requirements & Architecture

### 2.1 File: `src/core/errors.py`
- Define `ErrorCategoryType` enum:
  - `Configuration`, `Validation`, `Authentication`, `Database`, `FileSystem`, `Network`, `SlackApi`, `LlmService`, `BusinessLogic`, `Concurrency`, `Cache`.
- Define registered error code constants (`ErrorCodeType` or string constants):
  - `ERR_CONFIG_INVALID = "E1001"`
  - `ERR_SLACK_AUTH_FAILED = "E3001"`
  - `ERR_FILE_DOWNLOAD_FAILED = "E5001"`
  - `ERR_FILE_PARSE_FAILED = "E5002"`
  - `ERR_SLACK_RATE_LIMITED = "E7002"`
  - `ERR_SLACK_API_ERROR = "E7003"`
  - `ERR_LLM_TIMEOUT = "E7501"`
  - `ERR_LLM_PROVIDER_ERROR = "E7502"`
  - `ERR_PROPOSAL_NOT_FOUND = "E8001"`
  - `ERR_PROPOSAL_EXPIRED = "E8002"`
- Define `AppError(Exception)` class:
  - Frozen dataclass holding `code: str`, `message: str`, `category: ErrorCategoryType`, `cause: Exception | None`, `stack_trace: str`, `context: dict[str, Any]`.
  - Fluent helper methods: `with_context(key, value)`, `with_path(path)`.
  - Class method: `wrap(cause, code, message, category, context)`.

### 2.2 File: `src/core/result.py`
- Define `Result[T]` generic class:
  - `__slots__ = ("_value", "_error", "_is_success")`
  - Methods:
    - `Result.ok(value: T) -> Result[T]`
    - `Result.fail(error: AppError) -> Result[T]`
    - Property: `is_success -> bool`
    - Property: `has_error -> bool`
    - Method: `value() -> T` (Raises `RuntimeError` if accessed when `has_error` is True)
    - Method: `error() -> AppError`
    - Method: `unwrap_or(default: T) -> T`

---

## 3. Verification

Create a unit test `tests/unit/test_result_and_errors.py` verifying:
1. `Result.ok(42).value()` returns `42`.
2. Accessing `Result.fail(err).value()` raises `RuntimeError`.
3. `AppError.wrap()` captures the underlying stack trace and preserves context.
