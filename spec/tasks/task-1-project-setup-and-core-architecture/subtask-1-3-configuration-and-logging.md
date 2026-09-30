# Subtask 1.3: Configuration Loading & Session-Based Logging

> **Task Reference:** `TASK-01` > `SUBTASK-1.3`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §6.5, `agent_rules/03-error-handling-architecture.md` §6  

---

## 1. Description

Implement environment configuration management in `src/core/config.py` using `pydantic-settings`, guaranteeing secret protection, and set up structured session-based logging in `src/core/logger.py` with unique request tracing.

---

## 2. Requirements & Architecture

### 2.1 File: `src/core/config.py`
- Inherit from `pydantic_settings.BaseSettings`.
- Read from `.env` file with UTF-8 encoding.
- Fields:
  - `slack_bot_token: SecretStr` (starts with `xoxb-`)
  - `slack_app_token: SecretStr` (starts with `xapp-`)
  - `slack_signing_secret: SecretStr`
  - `openrouter_api_key: SecretStr`
  - `openrouter_model: str = "anthropic/claude-3.5-sonnet"`
  - `openrouter_base_url: str = "https://openrouter.ai/api/v1"`
  - `agent_name: str = "AIAssistant"`
  - `proposal_ttl_seconds: int = 1800` (30 minutes default)
  - `max_file_size_bytes: int = 10 * 1024 * 1024` (10 MB cap)
  - `log_level: str = "INFO"`
- Field Validators:
  - Verify `slack_bot_token` starts with `xoxb-`.
  - Verify `slack_app_token` starts with `xapp-`.
  - Verify `max_file_size_bytes` is greater than 0.

### 2.2 File: `src/core/logger.py`
- Standardized JSON or structured key-value logger.
- Support `contextvars` to propagate `request_id` / `session_id` throughout async execution chains.
- Provide helper: `get_logger(name: str) -> logging.Logger`.
- Provide filter to sanitize secret tokens (`xoxb-`, `xapp-`, `sk-or-`) from output logs.

---

## 3. Verification

Create unit test `tests/unit/test_config.py` verifying:
1. Valid `.env` fields load cleanly into `Settings`.
2. Invalid token prefix raises `ValidationError`.
3. Secret values are masked in `str(settings)`.
