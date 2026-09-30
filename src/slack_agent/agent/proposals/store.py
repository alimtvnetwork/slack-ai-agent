from __future__ import annotations

import time
from dataclasses import dataclass

from slack_agent.core.errors import (
    ERR_PROPOSAL_EXPIRED,
    ERR_PROPOSAL_NOT_FOUND,
    AppError,
    ErrorCategoryType,
)
from slack_agent.core.result import Result


@dataclass(frozen=True)
class FileProposal:
    """Represents a proposed document generation awaiting interactive user approval."""

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
        """Check if proposal has exceeded its Time-To-Live window."""
        return (time.time() - self.created_at) > self.ttl_seconds


_proposals_cache: dict[str, FileProposal] = {}


def save_proposal(proposal: FileProposal) -> None:
    """Store a proposed file generation entry."""
    _proposals_cache[proposal.proposal_id] = proposal


def get_proposal(proposal_id: str) -> Result[FileProposal]:
    """Retrieve a proposal, verifying it exists and has not expired."""
    proposal = _proposals_cache.get(proposal_id)
    if proposal is None:
        return Result.fail(
            AppError(
                code=ERR_PROPOSAL_NOT_FOUND,
                message=f"Proposal '{proposal_id}' was not found or was already processed",
                category=ErrorCategoryType.Validation,
                context={"ProposalId": proposal_id},
            )
        )

    if proposal.is_expired:
        delete_proposal(proposal_id)
        return Result.fail(
            AppError(
                code=ERR_PROPOSAL_EXPIRED,
                message=f"Proposal '{proposal_id}' has expired after {proposal.ttl_seconds}s",
                category=ErrorCategoryType.Validation,
                context={"ProposalId": proposal_id},
            )
        )

    return Result.ok(proposal)


def delete_proposal(proposal_id: str) -> None:
    """Remove a proposal from the cache."""
    _proposals_cache.pop(proposal_id, None)


def reset_proposal_store() -> None:
    """Clear all proposals (useful for testing)."""
    _proposals_cache.clear()
