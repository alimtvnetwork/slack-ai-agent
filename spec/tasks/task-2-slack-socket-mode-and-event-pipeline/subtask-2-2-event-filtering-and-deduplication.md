# Subtask 2.2: Event Filtering & Deduplication Middleware

> **Task Reference:** `TASK-02` > `SUBTASK-2.2`  
> **Source Rule:** `agent_rules/02-general-coding-guidelines.md` §3, `agent_rules/04-ai-agent-instructions.md` §5.2  

---

## 1. Description

Implement middleware in `src/slack/middleware/dedup.py` to prevent processing duplicate Slack event deliveries and filter out bot loopbacks (self-generated messages).

---

## 2. Requirements & Implementation Details

### 2.1 Deduplication Cache
- Slack retries unacknowledged event deliveries after 3 seconds. To avoid running the AI agent multiple times for the same user prompt:
- Maintain an LRU/TTL cache or expiring dictionary of processed IDs:
  - Cache key: `event_id` (fallback to `client_msg_id`).
  - Cache entry TTL: 600 seconds (10 minutes).
- When an event arrives:
  1. Check if `event_id` is present in cache.
  2. If present, immediately acknowledge (`await ack()`) and skip downstream processing.
  3. If not present, record `event_id` and proceed.

### 2.2 Bot Loopback Guard
- In `src/slack/middleware/filter.py`:
  - Check if the event's `user` equals the bot's own `user_id`.
  - Check if `subtype == "bot_message"`.
  - If either condition is true, skip processing to prevent infinite bot conversation loops.

---

## 3. Verification

Create unit test `tests/unit/test_dedup_middleware.py`:
1. Send 2 events with identical `event_id`: the first executes, the second is skipped.
2. Send an event where `user == bot_user_id`: event is filtered out immediately.
