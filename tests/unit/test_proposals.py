from __future__ import annotations

import time

from slack_agent.agent.proposals.store import (
    FileProposal,
    delete_proposal,
    get_proposal,
    reset_proposal_store,
    save_proposal,
)
from slack_agent.core.errors import ERR_PROPOSAL_EXPIRED, ERR_PROPOSAL_NOT_FOUND


def setup_function() -> None:
    reset_proposal_store()


def teardown_function() -> None:
    reset_proposal_store()


def test_save_and_get_proposal_success() -> None:
    proposal = FileProposal(
        proposal_id="prop-12345",
        file_name="report.pdf",
        file_format="pdf",
        content_summary="Quarterly financial summary",
        full_content="# Summary\n\nAll metrics up 15%.",
        channel_id="C12345",
        thread_ts="1234567.89",
        user_id="U99999",
        created_at=time.time(),
        ttl_seconds=1800,
    )

    save_proposal(proposal)
    retrieved_res = get_proposal("prop-12345")

    assert retrieved_res.is_success is True
    retrieved = retrieved_res.value()
    assert retrieved.file_name == "report.pdf"
    assert retrieved.content_summary == "Quarterly financial summary"


def test_get_nonexistent_proposal_fails() -> None:
    result = get_proposal("non-existent-id")

    assert result.has_error is True
    assert result.error().code == ERR_PROPOSAL_NOT_FOUND


def test_expired_proposal_eviction() -> None:
    expired_proposal = FileProposal(
        proposal_id="prop-expired",
        file_name="old_data.docx",
        file_format="docx",
        content_summary="Old report",
        full_content="Old content",
        channel_id="C12345",
        thread_ts="1234567.89",
        user_id="U99999",
        created_at=time.time() - 3600,  # 1 hour ago
        ttl_seconds=1800,  # 30 min TTL
    )

    save_proposal(expired_proposal)
    result = get_proposal("prop-expired")

    assert result.has_error is True
    assert result.error().code == ERR_PROPOSAL_EXPIRED

    # Next attempt should be ERR_PROPOSAL_NOT_FOUND because it was evicted
    second_result = get_proposal("prop-expired")
    assert second_result.has_error is True
    assert second_result.error().code == ERR_PROPOSAL_NOT_FOUND


def test_delete_proposal() -> None:
    proposal = FileProposal(
        proposal_id="prop-to-delete",
        file_name="temp.pdf",
        file_format="pdf",
        content_summary="Temp",
        full_content="Content",
        channel_id="C123",
        thread_ts="123.45",
        user_id="U1",
        created_at=time.time(),
        ttl_seconds=300,
    )

    save_proposal(proposal)
    delete_proposal("prop-to-delete")
    result = get_proposal("prop-to-delete")

    assert result.has_error is True
    assert result.error().code == ERR_PROPOSAL_NOT_FOUND
