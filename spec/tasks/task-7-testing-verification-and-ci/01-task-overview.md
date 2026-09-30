# Task 7: Testing, Verification & CI Suite

> **Task ID:** `TASK-07`  
> **Testing Tools:** `pytest`, `pytest-asyncio`, `ruff`, `mypy`, `uv`  
> **Status:** Pending Implementation  

---

## 1. Objective

Establish comprehensive unit and end-to-end integration test suites using `pytest` and `pytest-asyncio`, verifying complete behavior with mocked Slack and OpenRouter APIs, and enforcing lint and type-checking quality gates via `uv run`.

---

## 2. Subtask Breakdown

| Subtask ID | File | Summary |
|---|---|---|
| **SUBTASK-7.1** | [`subtask-7-1-mocking-and-unit-tests.md`](subtask-7-1-mocking-and-unit-tests.md) | Unit test suite covering error wrappers, Result monad, config loading, file parsers, Block Kit builders, and proposal store TTL. |
| **SUBTASK-7.2** | [`subtask-7-2-end-to-end-verification.md`](subtask-7-2-end-to-end-verification.md) | Async integration tests covering full end-to-end flow: file upload -> text extraction -> autonomous search -> write gate proposal -> button click approval -> PDF generation and mock upload. |

---

## 3. Success Criteria

1. All tests execute via `uv run pytest`.
2. 100% of unit tests pass with zero network dependencies (all external Slack and LLM endpoints mocked).
3. `uv run ruff check .` and `uv run mypy . --strict` exit with code 0.
