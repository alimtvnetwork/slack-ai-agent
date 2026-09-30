# Subtask 5.1: `propose_file_write` Gatekeeper Tool

> **Task Reference:** `TASK-05` > `SUBTASK-5.1`  
> **Source Rule:** `agent_rules/01-python-guidelines.md` §3, `agent_rules/02-general-coding-guidelines.md` §7  

---

## 1. Description

Implement `propose_file_write` in `src/agent/tools/write_gate.py`. This tool is the only mechanism the LLM is permitted to call when requested to create, draft, synthesize, or modify documents.

---

## 2. Requirements & Implementation Details

### 2.1 File: `src/agent/tools/write_gate.py`
```python
from langchain_core.tools import tool
from pydantic import BaseModel, Field
import uuid

class ProposeFileWriteInput(BaseModel):
    file_name: str = Field(..., description="Target file name, e.g. 'compliance_report.pdf'")
    file_format: str = Field(..., description="Format: 'pdf', 'docx', 'csv', or 'txt'")
    content_summary: str = Field(..., description="A 1-2 sentence executive summary of the file content")
    full_content: str = Field(..., description="The complete text or markdown content to render into the file")

@tool("propose_file_write", args_schema=ProposeFileWriteInput)
def propose_file_write(
    file_name: str,
    file_format: str,
    content_summary: str,
    full_content: str,
) -> str:
    """
    MANDATORY WRITE GATE: Call this tool whenever asked to write, generate, modify,
    or upload a file or report. Proposes the document for human interactive approval.
    """
    # 1. Generate unique proposal ID
    proposal_id = f"prop_{uuid.uuid4().hex[:10]}"
    
    # 2. Register proposal in the thread-isolated proposal store
    store_proposal(
        proposal_id=proposal_id,
        file_name=file_name,
        file_format=file_format.lower(),
        content_summary=content_summary,
        full_content=full_content,
    )
    
    # 3. Return notice to the agent
    return (
        f"Proposal {proposal_id} created successfully for '{file_name}'. "
        f"Interactive approval card has been prepared for the user in Slack. "
        f"Waiting for human approval."
    )
```

---

## 3. Verification

Create unit test `tests/unit/test_write_gate_tool.py`:
1. Call tool with valid inputs: creates entry in proposal store with unique ID.
2. Verify returned message clearly indicates proposal was queued for human review.
