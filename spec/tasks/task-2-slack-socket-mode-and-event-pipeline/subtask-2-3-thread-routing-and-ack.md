# Subtask 2.3: Thread-Aware Event Routing & Rapid Acknowledgment

> **Task Reference:** `TASK-02` > `SUBTASK-2.3`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §7, `agent_rules/03-error-handling-architecture.md`  

---

## 1. Description

Implement event routing for `app_mention` and direct message (`message.im`) events in `src/slack/handlers/messages.py`, ensuring immediate acknowledgement to Slack within 3 seconds, followed by asynchronous handoff to the agent worker pipeline.

---

## 2. Requirements & Implementation Details

### 2.1 Rapid Acknowledgment Pattern
Slack requires an HTTP/Socket ACK within 3 seconds:
```python
@app.event("app_mention")
async def handle_mention(event: dict[str, Any], say: AsyncSay, ack: AsyncAck) -> None:
    # 1. Acknowledge Slack immediately
    await ack()
    
    # 2. Extract conversation coordinates
    channel_id = event.get("channel", "")
    # If already in a thread, reply in that thread; otherwise reply in a new thread
    thread_ts = event.get("thread_ts") or event.get("ts", "")
    user_id = event.get("user", "")
    text = event.get("text", "")
    files = event.get("files", [])
    
    # 3. Schedule async processing in background task to not block socket handler
    asyncio.create_task(
        process_incoming_message(
            channel_id=channel_id,
            thread_ts=thread_ts,
            user_id=user_id,
            raw_text=text,
            raw_files=files,
        )
    )
```

### 2.2 Thread Key Normalization
All downstream state management relies on a consistent composite thread key:
```python
def make_thread_key(channel_id: str, thread_ts: str) -> str:
    """Format canonical composite thread key: channel_id:thread_ts."""
    return f"{channel_id}:{thread_ts}"
```

---

## 3. Verification

Create unit test `tests/unit/test_message_routing.py`:
1. Verify `ack()` is invoked before background task execution begins.
2. Verify top-level messages automatically establish their own `ts` as the `thread_ts`.
3. Verify existing thread replies preserve the parent `thread_ts`.
