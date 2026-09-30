# Subtask 6.1: Block Kit Interactive Action Listeners

> **Task Reference:** `TASK-06` > `SUBTASK-6.1`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §7, `agent_rules/02-general-coding-guidelines.md` §4  

---

## 1. Description

Register interactive button handlers in `src/slack/handlers/actions.py` to process user clicks on `[Approve & Write]` and `[Reject]`, mutate the message UI to prevent re-clicks, and coordinate file generation.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/slack/handlers/actions.py`

#### A. Approval Handler (`approve_file_write`)
```python
@app.action("approve_file_write")
async def handle_approval(ack: AsyncAck, body: dict[str, Any], client: AsyncWebClient) -> None:
    # 1. Acknowledge button interaction immediately (< 3 sec)
    await ack()
    
    proposal_id = body["actions"][0]["value"]
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    message_ts = body["message"]["ts"]
    
    # 2. Mutate Slack message to show approval status and disable buttons
    await client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=f"✅ Document generation approved by <@{user_id}>. Generating file...",
        blocks=build_approved_status_card(proposal_id, user_id),
    )
    
    # 3. Trigger async file generation worker
    asyncio.create_task(
        execute_file_generation_and_upload(
            proposal_id=proposal_id,
            approver_user_id=user_id,
            client=client,
        )
    )
```

#### B. Rejection Handler (`reject_file_write`)
```python
@app.action("reject_file_write")
async def handle_rejection(ack: AsyncAck, body: dict[str, Any], client: AsyncWebClient) -> None:
    await ack()
    
    proposal_id = body["actions"][0]["value"]
    user_id = body["user"]["id"]
    channel_id = body["channel"]["id"]
    message_ts = body["message"]["ts"]
    
    # Evict proposal from cache
    delete_proposal(proposal_id)
    
    # Update card to show rejection
    await client.chat_update(
        channel=channel_id,
        ts=message_ts,
        text=f"❌ Document generation rejected by <@{user_id}>.",
        blocks=build_rejected_status_card(proposal_id, user_id),
    )
```

---

## 3. Verification

Create unit test `tests/unit/test_action_handlers.py`:
1. Simulate `approve_file_write` action payload: calls `chat_update` and triggers background task.
2. Simulate `reject_file_write` action payload: deletes proposal and updates message to rejected state.
