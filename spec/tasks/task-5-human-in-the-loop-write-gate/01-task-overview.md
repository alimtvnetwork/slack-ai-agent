# Task 5: Mandatory Human-in-the-Loop Write Gate

> **Task ID:** `TASK-05`  
> **Core Requirement:** The agent is strictly prohibited from creating, modifying, or uploading any files or documents without explicit interactive button approval in Slack.  
> **Status:** Pending Implementation  

---

## 1. Objective

Implement the mandatory write approval architecture:
1. Provide the agent with the `propose_file_write` tool.
2. Intercept document generation requests and build interactive Slack Block Kit cards containing `[Approve & Write]` and `[Reject]` buttons.
3. Cache pending proposals in thread-isolated memory with Time-To-Live (TTL).

---

## 2. Subtask Breakdown

| Subtask ID | File | Summary |
|---|---|---|
| **SUBTASK-5.1** | [`subtask-5-1-propose-file-write-tool.md`](subtask-5-1-propose-file-write-tool.md) | Implement `@tool def propose_file_write(file_name, file_format, content_summary, full_content)` as the sole gatekeeper for document generation. |
| **SUBTASK-5.2** | [`subtask-5-2-block-kit-approval-cards.md`](subtask-5-2-block-kit-approval-cards.md) | Design and construct Slack Block Kit UI cards displaying file metadata, executive preview snippet, and interactive action buttons. |
| **SUBTASK-5.3** | [`subtask-5-3-proposal-state-storage.md`](subtask-5-3-proposal-state-storage.md) | Build an in-memory/SQLite proposal store with TTL expiration (1800s) mapping `proposal_id` to proposed document payloads. |

---

## 3. Success Criteria

1. Agent never uploads a file directly without first calling `propose_file_write`.
2. Interactive Block Kit card displays cleanly in Slack with `proposal_id` encoded in button `value`.
3. Proposals expire automatically after 30 minutes if neither approved nor rejected.
