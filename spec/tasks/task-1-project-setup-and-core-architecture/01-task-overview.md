# Task 1: Project Setup & Core Architecture

> **Task ID:** `TASK-01`  
> **Package Tooling:** `uv`  
> **Status:** Pending Implementation  

---

## 1. Objective

Initialize the Python project repository using `uv`, configure production-grade linters and type checkers (Ruff & Mypy), establish the domain-driven error handling foundation (`AppError` & `Result[T]`), and set up environment configuration with `pydantic-settings`.

---

## 2. Subtask Breakdown

| Subtask ID | File | Summary |
|---|---|---|
| **SUBTASK-1.1** | [`subtask-1-1-environment-and-tooling.md`](subtask-1-1-environment-and-tooling.md) | Initialize project with `uv init`, add dependencies (`slack_bolt`, `langgraph`, `langchain-core`, `pydantic`, `pydantic-settings`, `reportlab`, `pypdf`, `python-docx`, `duckduckgo-search`, `httpx`), and configure `pyproject.toml`. |
| **SUBTASK-1.2** | [`subtask-1-2-error-handling-and-result-types.md`](subtask-1-2-error-handling-and-result-types.md) | Implement `src/core/errors.py` and `src/core/result.py` with full type annotations, registered error code constants, and mandatory guard checks per `agent_rules/03-error-handling-architecture.md`. |
| **SUBTASK-1.3** | [`subtask-1-3-configuration-and-logging.md`](subtask-1-3-configuration-and-logging.md) | Create `src/core/config.py` using `pydantic-settings` with secret shielding, and configure structured two-tier session logging in `src/core/logger.py`. |

---

## 3. Success Criteria

1. Project virtual environment managed cleanly by `uv`.
2. `uv run ruff check .` and `uv run mypy . --strict` pass with zero errors.
3. Configuration loads safely from `.env` and validates all required Slack and OpenRouter credentials.
