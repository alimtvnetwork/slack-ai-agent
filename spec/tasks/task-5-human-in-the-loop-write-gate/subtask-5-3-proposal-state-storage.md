# Subtask 5.3: Pending Proposal State Storage & TTL Management

> **Task Reference:** `TASK-05` > `SUBTASK-5.3`  
> **Source Rule:** `agent_rules/02-general-coding-guidelines.md` §7, `agent_rules/03-error-handling-architecture.md`  

---

## 1. Description

Implement `src/agent/proposals/store.py` to store proposed file content awaiting human approval, keyed by `proposal_id`, with automatic eviction upon approval, rejection, or TTL expiration.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/agent/proposals/store.py`
- Model Definition:
  ```python
  from dataclasses import dataclass
  import time

  @dataclass(frozen=True)
  class FileProposal:
      proposal_id: str
      file_name: str
      file_format: str
      content_summary: str
      full_content: str
      channel_id: str
      thread_ts: str
      user_id: str
      created_at: float
      ttl_seconds: int = 1800
      
      @property
      def is_expired(self) -> bool:
          return (time.time() - self.created_at) > self.ttl_seconds
  ```
- Store Operations:
  - `save_proposal(proposal: FileProposal) -> None`
  - `get_proposal(proposal_id: str) -> Result[FileProposal]`
  - `delete_proposal(proposal_id: str) -> None`
- **TTL Eviction:**
  When `get_proposal` is called:
  - If proposal is missing: return `Result.fail(ERR_PROPOSAL_NOT_FOUND)`.
  - If proposal `is_expired`: delete entry and return `Result.fail(ERR_PROPOSAL_EXPIRED)`.
  - Otherwise return `Result.ok(proposal)`.

---

## 3. Verification

Create unit test `tests/unit/test_proposal_store.py`:
1. Save and retrieve proposal: succeeds and returns data.
2. Expired proposal (mocked `time.time`): returns `ERR_PROPOSAL_EXPIRED` and purges key.
3. Deleting proposal removes it from store.
