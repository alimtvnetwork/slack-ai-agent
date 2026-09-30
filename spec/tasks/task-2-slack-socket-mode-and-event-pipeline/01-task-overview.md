# Task 2: Slack Socket Mode & Event Pipeline

> **Task ID:** `TASK-02`  
> **Framework:** `slack_bolt.async_app.AsyncApp`, `slack_bolt.adapter.socket_mode.async_handler.AsyncSocketModeHandler`  
> **Status:** Pending Implementation  

---

## 1. Objective

Set up the asynchronous Slack Socket Mode listener, implement event routing for `@mention` events and 1-on-1 direct messages, enforce event deduplication (`event_id` / `client_msg_id`), and establish thread-aware conversation boundaries.

---

## 2. Subtask Breakdown

| Subtask ID | File | Summary |
|---|---|---|
| **SUBTASK-2.1** | [`subtask-2-1-socket-mode-client-setup.md`](subtask-2-1-socket-mode-client-setup.md) | Initialize `AsyncApp` and `AsyncSocketModeHandler` with `slack_app_token` and `slack_bot_token`, implementing lifecycle start/stop routines. |
| **SUBTASK-2.2** | [`subtask-2-2-event-filtering-and-deduplication.md`](subtask-2-2-event-filtering-and-deduplication.md) | Build middleware for event deduplication using an in-memory TTL set or SQLite cache, discarding bot self-messages and duplicate webhook retries. |
| **SUBTASK-2.3** | [`subtask-2-3-thread-routing-and-ack.md`](subtask-2-3-thread-routing-and-ack.md) | Route `app_mention` and `message.im` events, ensure immediate Slack `ack()` within 3 seconds, and extract thread conversation context (`channel_id`, `thread_ts`). |

---

## 3. Success Criteria

1. Bot connects to Slack over WebSocket in Socket Mode without requiring open inbound firewall ports.
2. Bot acknowledges incoming events in under 3 seconds to prevent Slack webhook retries.
3. Multiple duplicate events with the same `event_id` are processed exactly once.
