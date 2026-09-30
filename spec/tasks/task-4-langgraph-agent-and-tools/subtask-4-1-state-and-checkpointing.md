# Subtask 4.1: Agent State & Thread-Keyed Checkpointing

> **Task Reference:** `TASK-04` > `SUBTASK-4.1`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §3, `agent_rules/02-general-coding-guidelines.md` §6  

---

## 1. Description

Define the typed agent state in `src/agent/state.py` and configure the LangGraph state checkpointer in `src/agent/checkpointer.py` to maintain multi-turn context keyed strictly by `channel_id:thread_ts`.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/agent/state.py`
```python
from typing import Annotated, Sequence
from typing_extensions import TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """Canonical LangGraph state container for Slack AI Agent."""
    
    messages: Annotated[Sequence[BaseMessage], add_messages]
    channel_id: str
    thread_ts: str
    user_id: str
    is_write_approved: bool
    pending_proposal_id: str | None
```

### 2.2 File: `src/agent/checkpointer.py`
- LangGraph provides `MemorySaver` (in-memory) or `SqliteSaver` (persistent).
- Configure checkpointer with thread configuration:
  ```python
  def make_thread_config(channel_id: str, thread_ts: str) -> dict[str, Any]:
      """Construct checkpointer thread configuration dictionary."""
      thread_key = f"{channel_id}:{thread_ts}"
      return {"configurable": {"thread_id": thread_key}}
  ```
- **Isolation Guarantee:** Conversations across different channels or different thread timestamps have distinct `thread_id` keys, preventing cross-talk.

---

## 3. Verification

Create unit test `tests/unit/test_checkpointer.py`:
1. Invoke state graph with thread key `C1:T1`: state is saved.
2. Invoke with thread key `C2:T2`: state is isolated and does not contain `C1:T1` messages.
3. Second turn in `C1:T1` recalls previous turn messages.
