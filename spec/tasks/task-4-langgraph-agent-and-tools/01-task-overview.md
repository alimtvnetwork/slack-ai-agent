# Task 4: LangGraph Autonomous Agent & Tool Integration

> **Task ID:** `TASK-04`  
> **Core Technologies:** `langgraph`, `langchain_openai.ChatOpenAI` (configured for OpenRouter), `duckduckgo-search`  
> **Status:** Pending Implementation  

---

## 1. Objective

Build an autonomous LangGraph agent workflow that coordinates LLM reasoning via OpenRouter, autonomously invokes DuckDuckGo web search when real-time or external facts are needed, and maintains isolated multi-turn conversation memory keyed by `channel_id:thread_ts` using LangGraph Checkpointer.

---

## 2. Subtask Breakdown

| Subtask ID | File | Summary |
|---|---|---|
| **SUBTASK-4.1** | [`subtask-4-1-state-and-checkpointing.md`](subtask-4-1-state-and-checkpointing.md) | Define `AgentState` schema and configure thread checkpointer (`MemorySaver` or SQLite) keyed by composite `thread_id = f"{channel_id}:{thread_ts}"`. |
| **SUBTASK-4.2** | [`subtask-4-2-openrouter-llm-integration.md`](subtask-4-2-openrouter-llm-integration.md) | Initialize OpenRouter client via `ChatOpenAI` with model routing, system prompt, and token limit protection. |
| **SUBTASK-4.3** | [`subtask-4-3-duckduckgo-web-search-tool.md`](subtask-4-3-duckduckgo-web-search-tool.md) | Implement `@tool def web_search(query: str) -> str:` using `duckduckgo-search` with result sanitization, error wrapping, and timeout guards. |
| **SUBTASK-4.4** | [`subtask-4-4-agent-reasoning-node.md`](subtask-4-4-agent-reasoning-node.md) | Construct the LangGraph workflow (`StateGraph`) connecting agent reasoning node, tool executor node, and conditional routing logic. |

---

## 3. Success Criteria

1. Multi-turn conversation history is preserved within the same Slack thread.
2. Inquiries in separate channels or threads do not share state or cross-talk.
3. Web search autonomously triggers when asked about external events, regulations, or facts.
