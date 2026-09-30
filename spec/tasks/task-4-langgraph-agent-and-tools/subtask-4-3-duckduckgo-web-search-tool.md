# Subtask 4.3: DuckDuckGo Web Search Tool

> **Task Reference:** `TASK-04` > `SUBTASK-4.3`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §3, `agent_rules/03-error-handling-architecture.md`  

---

## 1. Description

Implement an autonomous web search tool in `src/agent/tools/search.py` using `duckduckgo-search` (`DDGS`), formatted as a LangChain `@tool` for LangGraph agent invocation.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/agent/tools/search.py`
- LangChain Tool Definition:
  ```python
  from langchain_core.tools import tool
  from duckduckgo_search import DDGS
  from src.core.errors import AppError, ErrorCategoryType

  @tool
  def web_search(query: str, max_results: int = 5) -> str:
      """
      Search the web for up-to-date facts, regulations, news, or external data.
      Use this tool when external factual knowledge is needed to answer the user inquiry.
      """
      try:
          with DDGS() as ddgs:
              raw_results = list(ddgs.text(query, max_results=max_results))
          
          if not raw_results:
              return "No relevant web search results found for this query."
          
          formatted = []
          for item in raw_results:
              title = item.get("title", "")
              href = item.get("href", "")
              body = item.get("body", "")
              formatted.append(f"• **{title}** ({href})\n  {body}")
              
          return "\n\n".join(formatted)
      except Exception as exc:
          # Catch specific network/search errors and return safe failure message to LLM
          return f"Web search encountered a temporary error: {exc}"
  ```
- **Safety Controls:**
  - Cap `max_results` at 5 to prevent LLM context exhaustion.
  - Timeout after 8 seconds.

---

## 3. Verification

Create unit test `tests/unit/test_search_tool.py`:
1. Mock `DDGS.text` returning sample search hits: correctly formats markdown bullets.
2. Mock empty search results: returns clean `"No relevant web search results found"`.
3. Mock network failure: returns safe fallback string without throwing uncaught exceptions.
