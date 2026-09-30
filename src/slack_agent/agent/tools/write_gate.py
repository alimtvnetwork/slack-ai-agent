from __future__ import annotations

import time
import uuid

from langchain_core.tools import tool
from pydantic import BaseModel, Field

from slack_agent.agent.proposals.store import FileProposal, save_proposal
from slack_agent.core.logger import get_logger

logger = get_logger(__name__)


class ProposeFileWriteInput(BaseModel):
    """Input parameters for the propose_file_write write gate tool."""

    file_name: str = Field(..., description="Target file name, e.g. 'compliance_report.pdf'")
    file_format: str = Field(..., description="Format: 'pdf', 'docx', 'csv', or 'txt'")
    content_summary: str = Field(
        ...,
        description="A 1-2 sentence executive summary of the file content",
    )
    full_content: str = Field(
        ...,
        description="The complete text or markdown content to render into the file",
    )


@tool("propose_file_write", args_schema=ProposeFileWriteInput)
def propose_file_write(
    file_name: str,
    file_format: str,
    content_summary: str,
    full_content: str,
) -> str:
    """
    MANDATORY WRITE GATE: Propose creating, modifying, or uploading a file or report.

    You MUST call this tool whenever asked to write or upload documents.
    An interactive approval card will be sent to the user in Slack for confirmation.
    """
    proposal_id = f"prop_{uuid.uuid4().hex[:10]}"

    proposal = FileProposal(
        proposal_id=proposal_id,
        file_name=file_name,
        file_format=file_format.lower().strip("."),
        content_summary=content_summary,
        full_content=full_content,
        channel_id="",  # Injected during invocation context
        thread_ts="",  # Injected during invocation context
        user_id="",
        created_at=time.time(),
    )

    save_proposal(proposal)

    logger.info(
        "Created pending file write proposal",
        extra={"ProposalId": proposal_id, "FileName": file_name, "Format": file_format},
    )

    fmt = file_format.upper()
    return (
        f"Proposal '{proposal_id}' successfully created for file '{file_name}' ({fmt}). "
        "An interactive [Approve & Write] / [Reject] card has been presented to the user. "
        "The file will only be generated and uploaded once the user clicks Approve."
    )
