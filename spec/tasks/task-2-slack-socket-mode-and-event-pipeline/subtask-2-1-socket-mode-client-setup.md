# Subtask 2.1: Socket Mode Client Initialization & Lifecycle

> **Task Reference:** `TASK-02` > `SUBTASK-2.1`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §7, `agent_rules/04-ai-agent-instructions.md` §5  

---

## 1. Description

Construct the Slack asynchronous application wrapper in `src/slack/client.py` using `slack_bolt.async_app.AsyncApp` and `AsyncSocketModeHandler`, providing clean startup, shutdown, and health verification mechanisms.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/slack/client.py`
- Initialize `AsyncApp`:
  ```python
  from slack_bolt.async_app import AsyncApp
  from slack_bolt.adapter.socket_mode.async_handler import AsyncSocketModeHandler

  app = AsyncApp(
      token=settings.slack_bot_token.get_secret_value(),
      signing_secret=settings.slack_signing_secret.get_secret_value(),
  )
  handler = AsyncSocketModeHandler(
      app=app,
      app_token=settings.slack_app_token.get_secret_value(),
  )
  ```
- Expose lifecycle functions:
  - `async def start_slack_bot() -> None:`
  - `async def stop_slack_bot() -> None:`
- Handle signal listeners (`SIGINT`, `SIGTERM`) for graceful teardown of the WebSocket connection.
- Verify authentication status on boot using `await app.client.auth_test()`. Store the bot's own `user_id` to filter out self-mentions.

---

## 3. Verification

Create an integration test in `tests/integration/test_socket_mode_client.py` with mock Socket Mode handler verifying:
1. `AsyncApp` initializes with valid secret tokens.
2. `auth_test()` retrieves bot user ID.
3. Teardown safely closes the active WebSocket session.
