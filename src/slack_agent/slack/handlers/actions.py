from __future__ import annotations

import asyncio
from typing import Any

from slack_bolt.async_app import AsyncAck
from slack_sdk.web.async_client import AsyncWebClient

from slack_agent.agent.proposals.store import (
    FileProposal,
    delete_proposal,
    get_proposal,
    save_proposal,
)
from slack_agent.core.logger import get_logger
from slack_agent.core.result import Result
from slack_agent.generators.docx import generate_docx_bytes
from slack_agent.generators.pdf import generate_pdf_bytes
from slack_agent.slack.blocks.approval_card import (
    ApprovalCardParams,
    EditProposalModalParams,
    build_approval_card,
    build_approved_status_card,
    build_edit_proposal_modal,
    build_rejected_status_card,
)
from slack_agent.slack.uploader import UploadDocumentParams, upload_generated_document

logger = get_logger(__name__)


async def handle_approval_action(
    ack: AsyncAck,
    body: dict[str, Any],
    client: AsyncWebClient,
) -> None:
    """Handle user clicking [Approve & Write] on a file proposal card."""
    await ack()

    actions = body.get("actions", [])
    if not actions:
        return

    proposal_id = actions[0].get("value", "")
    user_id = body.get("user", {}).get("id", "unknown_user")
    channel_id = body.get("channel", {}).get("id", "")
    message_ts = body.get("message", {}).get("ts", "")

    try:
        await client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=f"✅ Document generation approved by <@{user_id}>. Building file...",
            blocks=build_approved_status_card(proposal_id, user_id),
        )
    except Exception as exc:
        logger.warning(
            "Failed to update approval card message",
            extra={"ProposalId": proposal_id, "Error": str(exc)},
        )

    asyncio.create_task(
        execute_approved_file_generation(
            proposal_id=proposal_id,
            channel_id=channel_id,
            thread_ts=message_ts,
            client=client,
        )
    )


async def handle_rejection_action(
    ack: AsyncAck,
    body: dict[str, Any],
    client: AsyncWebClient,
) -> None:
    """Handle user clicking [Reject] on a file proposal card."""
    await ack()

    actions = body.get("actions", [])
    if not actions:
        return

    proposal_id = actions[0].get("value", "")
    user_id = body.get("user", {}).get("id", "unknown_user")
    channel_id = body.get("channel", {}).get("id", "")
    message_ts = body.get("message", {}).get("ts", "")

    delete_proposal(proposal_id)

    try:
        await client.chat_update(
            channel=channel_id,
            ts=message_ts,
            text=f"❌ Document generation rejected by <@{user_id}>.",
            blocks=build_rejected_status_card(proposal_id, user_id),
        )
    except Exception as exc:
        logger.warning(
            "Failed to update rejection card message",
            extra={"ProposalId": proposal_id, "Error": str(exc)},
        )


def _build_updated_proposal(existing: FileProposal, values: dict[str, Any]) -> FileProposal:
    """Construct an updated FileProposal from modal form values."""
    file_name = (
        values.get("block_file_name", {}).get("input_file_name", {}).get("value", "").strip()
    )
    file_format = (
        values.get("block_file_format", {})
        .get("input_file_format", {})
        .get("value", "pdf")
        .strip()
        .lower()
    )
    content = values.get("block_content", {}).get("input_content", {}).get("value", "").strip()
    return FileProposal(
        proposal_id=existing.proposal_id,
        file_name=file_name or existing.file_name,
        file_format=file_format or existing.file_format,
        content_summary=existing.content_summary,
        full_content=content or existing.full_content,
        channel_id=existing.channel_id,
        thread_ts=existing.thread_ts,
        user_id=existing.user_id,
        created_at=existing.created_at,
        ttl_seconds=existing.ttl_seconds,
    )


async def handle_edit_action(
    ack: AsyncAck,
    body: dict[str, Any],
    client: AsyncWebClient,
) -> None:
    """Handle user clicking [✏️ Edit / Refine] to open the edit modal dialog."""
    await ack()
    actions = body.get("actions", [])
    if not actions:
        return

    proposal_id = actions[0].get("value", "")
    trigger_id = body.get("trigger_id", "")
    proposal_res = get_proposal(proposal_id)
    if proposal_res.has_error or not trigger_id:
        return

    proposal = proposal_res.value()
    modal_params = EditProposalModalParams(
        proposal_id=proposal.proposal_id,
        file_name=proposal.file_name,
        file_format=proposal.file_format,
        content=proposal.full_content,
    )
    try:
        await client.views_open(
            trigger_id=trigger_id,
            view=build_edit_proposal_modal(modal_params),
        )
    except Exception as exc:
        logger.warning(
            "Failed to open edit modal",
            extra={"ProposalId": proposal_id, "Error": str(exc)},
        )


async def handle_modal_submission(
    ack: AsyncAck,
    body: dict[str, Any],
    client: AsyncWebClient,
) -> None:
    """Handle user submitting edited proposal attributes from the modal dialog."""
    await ack()
    view = body.get("view", {})
    proposal_id = view.get("private_metadata", "")
    values = view.get("state", {}).get("values", {})

    proposal_res = get_proposal(proposal_id)
    if proposal_res.has_error:
        return

    updated = _build_updated_proposal(proposal_res.value(), values)
    save_proposal(updated)

    card_params = ApprovalCardParams(
        proposal_id=updated.proposal_id,
        file_name=updated.file_name,
        file_format=updated.file_format,
        content_summary=updated.content_summary,
        preview_snippet=updated.full_content[:280],
    )
    try:
        await client.chat_postMessage(
            channel=updated.channel_id,
            thread_ts=updated.thread_ts,
            text=f"✏️ Proposal updated: '{updated.file_name}' ({updated.file_format.upper()})",
            blocks=build_approval_card(card_params),
        )
    except Exception as exc:
        logger.warning("Failed to post updated proposal card", extra={"Error": str(exc)})


def _render_proposal_bytes(proposal: FileProposal) -> Result[bytes]:
    """Generate byte content based on proposal document format."""
    if proposal.file_format == "pdf":
        return generate_pdf_bytes(title=proposal.file_name, content=proposal.full_content)

    if proposal.file_format == "docx":
        return generate_docx_bytes(title=proposal.file_name, content=proposal.full_content)

    return Result.ok(proposal.full_content.encode("utf-8"))


async def _notify_slack_failure(
    client: AsyncWebClient,
    channel_id: str,
    thread_ts: str,
    message: str,
) -> None:
    """Post an error notification to the Slack conversation thread."""
    await client.chat_postMessage(
        channel=channel_id,
        thread_ts=thread_ts,
        text=f"⚠️ {message}",
    )


async def execute_approved_file_generation(
    proposal_id: str,
    channel_id: str,
    thread_ts: str,
    client: AsyncWebClient,
) -> None:
    """Generate approved document bytes and upload to Slack conversation thread."""
    proposal_result = get_proposal(proposal_id)
    if proposal_result.has_error:
        await _notify_slack_failure(client, channel_id, thread_ts, proposal_result.error().message)
        return

    proposal = proposal_result.value()
    gen_result = _render_proposal_bytes(proposal)
    if gen_result.has_error:
        await _notify_slack_failure(client, channel_id, thread_ts, gen_result.error().message)
        return

    target_thread = proposal.thread_ts if proposal.thread_ts else thread_ts
    target_channel = proposal.channel_id if proposal.channel_id else channel_id

    upload_params = UploadDocumentParams(
        client=client,
        channel_id=target_channel,
        thread_ts=target_thread,
        file_bytes=gen_result.value(),
        file_name=proposal.file_name,
        title=proposal.file_name,
    )
    upload_result = await upload_generated_document(upload_params)
    delete_proposal(proposal_id)

    if upload_result.has_error:
        await _notify_slack_failure(
            client, channel_id, target_thread, upload_result.error().message
        )
