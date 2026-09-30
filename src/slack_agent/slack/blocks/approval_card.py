from __future__ import annotations

from dataclasses import dataclass
from typing import Any

MAX_PREVIEW_LENGTH = 280


@dataclass(frozen=True)
class ApprovalCardParams:
    """Parameters required to build an interactive Block Kit approval card."""

    proposal_id: str
    file_name: str
    file_format: str
    content_summary: str
    preview_snippet: str


def build_approval_card(params: ApprovalCardParams) -> list[dict[str, Any]]:
    """Construct an interactive Block Kit card requesting approval for file generation."""
    snippet_len = len(params.preview_snippet)
    has_ellipsis = snippet_len > MAX_PREVIEW_LENGTH
    snippet = params.preview_snippet[:MAX_PREVIEW_LENGTH] + ("..." if has_ellipsis else "")

    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📝 Document Generation Request",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*File Name:*\n`{params.file_name}`"},
                {"type": "mrkdwn", "text": f"*Format:*\n`{params.file_format.upper()}`"},
            ],
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"*Summary:*\n{params.content_summary}\n\n*Preview:*\n> {snippet}",
            },
        },
        {
            "type": "actions",
            "block_id": f"write_approval_block_{params.proposal_id}",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve & Write", "emoji": True},
                    "style": "primary",
                    "action_id": "approve_file_write",
                    "value": params.proposal_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "✏️ Edit / Refine", "emoji": True},
                    "action_id": "edit_file_write_proposal",
                    "value": params.proposal_id,
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject", "emoji": True},
                    "style": "danger",
                    "action_id": "reject_file_write",
                    "value": params.proposal_id,
                },
            ],
        },
    ]


@dataclass(frozen=True)
class EditProposalModalParams:
    """Parameters to populate the edit proposal modal view."""

    proposal_id: str
    file_name: str
    file_format: str
    content: str


def build_edit_proposal_modal(params: EditProposalModalParams) -> dict[str, Any]:
    """Construct an interactive modal view to edit document proposal attributes."""
    return {
        "type": "modal",
        "callback_id": "submit_edit_file_proposal",
        "private_metadata": params.proposal_id,
        "title": {"type": "plain_text", "text": "Edit Proposal", "emoji": True},
        "submit": {"type": "plain_text", "text": "Save & Update", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "blocks": [
            {
                "type": "input",
                "block_id": "block_file_name",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "input_file_name",
                    "initial_value": params.file_name,
                },
                "label": {"type": "plain_text", "text": "File Name"},
            },
            {
                "type": "input",
                "block_id": "block_file_format",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "input_file_format",
                    "initial_value": params.file_format,
                },
                "label": {"type": "plain_text", "text": "Format (pdf, docx, csv, txt)"},
            },
            {
                "type": "input",
                "block_id": "block_content",
                "element": {
                    "type": "plain_text_input",
                    "action_id": "input_content",
                    "multiline": True,
                    "initial_value": params.content[:2500],
                },
                "label": {"type": "plain_text", "text": "Document Content"},
            },
        ],
    }


def build_approved_status_card(proposal_id: str, user_id: str) -> list[dict[str, Any]]:
    """Render approval confirmation status, disabling buttons."""
    confirmation = f"✅ *Document approved by <@{user_id}>*. Building and uploading file now..."
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": confirmation,
            },
        }
    ]


def build_rejected_status_card(proposal_id: str, user_id: str) -> list[dict[str, Any]]:
    """Render rejection status, disabling buttons."""
    return [
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": f"❌ *Document generation rejected by <@{user_id}>*. Proposal discarded.",
            },
        }
    ]
