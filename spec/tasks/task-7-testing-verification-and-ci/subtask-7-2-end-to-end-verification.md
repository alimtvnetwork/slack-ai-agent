# Subtask 7.2: End-to-End Workflow Verification

> **Task Reference:** `TASK-07` > `SUBTASK-7.2`  
> **Source Rule:** `agent_rules/04-ai-agent-instructions.md` §1.2  

---

## 1. Description

Construct an integration test in `tests/integration/test_full_workflow.py` verifying the complete 6-step lifecycle defined in the technical blueprint:
1. File upload with user prompt
2. Extraction and prompt prepending
3. Reasoning and autonomous web search
4. Write proposal trigger (`propose_file_write`)
5. Slack interactive approval card rendering
6. User approval click, ReportLab PDF rendering, and mock `files.upload_v2` dispatch.

---

## 2. Test Execution Flow

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_full_agent_write_approval_lifecycle():
    # 1. Simulate user uploading PDF file and prompt
    # 2. Assert text extraction succeeds
    # 3. Assert LangGraph agent autonomously triggers web_search
    # 4. Assert agent calls propose_file_write instead of uploading directly
    # 5. Assert Block Kit card is rendered with [Approve & Write] and [Reject]
    # 6. Simulate user clicking [Approve & Write]
    # 7. Assert ReportLab builds PDF starting with %PDF-
    # 8. Assert files.upload_v2 receives the generated PDF bytes
    # 9. Assert proposal is purged from the store
```

---

## 3. Full CI Verification Commands

```bash
# 1. Linting & Formatting Check
uv run ruff check .
uv run ruff format --check .

# 2. Strict Type Checking
uv run mypy . --strict

# 3. Full Test Suite Execution
uv run pytest -v --asyncio-mode=auto
```
