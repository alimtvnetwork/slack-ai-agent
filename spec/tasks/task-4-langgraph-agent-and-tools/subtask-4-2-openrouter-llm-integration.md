# Subtask 4.2: OpenRouter LLM Integration

> **Task Reference:** `TASK-04` > `SUBTASK-4.2`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §3, `agent_rules/03-error-handling-architecture.md`  

---

## 1. Description

Integrate OpenRouter as the primary LLM provider in `src/agent/llm.py` using `langchain_openai.ChatOpenAI`, configured with base URL, headers, and temperature settings.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/agent/llm.py`
- Initialize `ChatOpenAI` configured for OpenRouter:
  ```python
  from langchain_openai import ChatOpenAI
  from src.core.config import Settings

  def create_llm_client(settings: Settings) -> ChatOpenAI:
      return ChatOpenAI(
          model=settings.openrouter_model,
          api_key=settings.openrouter_api_key.get_secret_value(),
          base_url=settings.openrouter_base_url,
          temperature=0.2,
          default_headers={
              "HTTP-Referer": "https://github.com/slack-agent",
              "X-Title": settings.agent_name,
          },
      )
  ```
- **System Prompt:**
  Define the system instructions in `src/agent/prompts.py`:
  - Enforce professional, concise tone.
  - Instruct the model to cite sources when performing web search.
  - **CRITICAL WRITE GATE DIRECTIVE:** Instruct the model that whenever the user requests generating, modifying, drafting, or uploading a document or file (PDF, report, summary, script), it **MUST NOT output raw file content directly**. It **MUST invoke the `propose_file_write` tool**.

---

## 3. Verification

Create unit test `tests/unit/test_llm_client.py`:
1. Verify `ChatOpenAI` initializes with OpenRouter base URL and headers.
2. Verify system prompt includes mandatory `propose_file_write` constraint.
