from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Any

from langchain_core.messages import HumanMessage
from slack_bolt.async_app import AsyncAck
from slack_sdk.web.async_client import AsyncWebClient

from slack_agent.agent.checkpointer import make_thread_config
from slack_agent.agent.proposals.store import _proposals_cache
from slack_agent.agent.tools.chart import GeneratedChart, get_generated_charts
from slack_agent.core.config import Settings
from slack_agent.core.logger import get_logger
from slack_agent.files.downloader import download_slack_file
from slack_agent.files.injector import ExtractedDocument, synthesize_prompt_with_files
from slack_agent.files.parser import parse_file_bytes
from slack_agent.slack.blocks.approval_card import ApprovalCardParams, build_approval_card
from slack_agent.slack.handlers.commands import (
    CommandType,
    _handle_reset_command,
    _is_reset_command,
    _purge_thread_checkpoint,
    handle_system_command,
    parse_system_command,
)
from slack_agent.slack.middleware.dedup import is_duplicate_event
from slack_agent.slack.middleware.filter import is_bot_loopback
from slack_agent.slack.status import SlackStatusNotifier
from slack_agent.slack.uploader import UploadDocumentParams, upload_generated_document

logger = get_logger(__name__)

__all__ = [
    "CommandType",
    "MessageEventContext",
    "PipelineExecutionContext",
    "_handle_reset_command",
    "_is_reset_command",
    "_purge_thread_checkpoint",
    "handle_incoming_message_event",
    "handle_system_command",
    "parse_system_command",
    "process_message_pipeline",
]


@dataclass(frozen=True)
class MessageEventContext:
    """Encapsulates context needed to dispatch an incoming Slack message event."""

    event: dict[str, Any]
    ack: AsyncAck
    client: AsyncWebClient
    settings: Settings
    agent_graph: Any
    bot_user_id: str


@dataclass(frozen=True)
class PipelineExecutionContext:
    """Parameters required to process the message pipeline end-to-end."""

    channel_id: str
    thread_ts: str
    user_id: str
    raw_text: str
    files: list[dict[str, Any]]
    client: AsyncWebClient
    settings: Settings
    agent_graph: Any


async def handle_incoming_message_event(ctx: MessageEventContext) -> None:
    """Acknowledge Slack immediately (<3s) and route event to async processing."""
    await ctx.ack()

    channel_id = str(ctx.event.get("channel", ""))
    message_ts = str(ctx.event.get("ts") or ctx.event.get("event_ts", ""))
    event_id = (
        f"{channel_id}:{message_ts}"
        if (channel_id and message_ts)
        else str(ctx.event.get("client_msg_id") or message_ts)
    )
    if is_duplicate_event(event_id):
        logger.info("Ignoring duplicate Slack event", extra={"EventId": event_id})
        return

    if is_bot_loopback(ctx.event, ctx.bot_user_id):
        return

    thread_ts = str(ctx.event.get("thread_ts") or ctx.event.get("ts", ""))
    user_id = str(ctx.event.get("user", ""))
    raw_text = str(ctx.event.get("text", ""))
    files = list(ctx.event.get("files", []))

    pipeline_ctx = PipelineExecutionContext(
        channel_id=channel_id,
        thread_ts=thread_ts,
        user_id=user_id,
        raw_text=raw_text,
        files=files,
        client=ctx.client,
        settings=ctx.settings,
        agent_graph=ctx.agent_graph,
    )

    asyncio.create_task(process_message_pipeline(pipeline_ctx))


async def _download_and_extract_attachments(
    files: list[dict[str, Any]],
    settings: Settings,
) -> list[ExtractedDocument]:
    """Download and extract text from user-attached files."""
    extracted_docs: list[ExtractedDocument] = []
    bot_token = settings.slack_bot_token.get_secret_value()

    for file_info in files:
        download_url = file_info.get("url_private_download", "")
        file_name = file_info.get("name", "document")
        file_type = file_info.get("filetype", "unknown")
        file_id = file_info.get("id", "")

        if download_url and bot_token:
            dl_result = await download_slack_file(
                download_url=download_url,
                bot_token=bot_token,
                max_bytes=settings.max_file_size_bytes,
            )
            if dl_result.is_success:
                parse_result = parse_file_bytes(
                    file_bytes=dl_result.value(),
                    file_name=file_name,
                    file_type=file_type,
                )
                if parse_result.is_success:
                    extracted_text = parse_result.value()
                    extracted_docs.append(
                        ExtractedDocument(
                            file_id=file_id,
                            file_name=file_name,
                            file_type=file_type,
                            text_content=extracted_text,
                            char_count=len(extracted_text),
                        )
                    )

    return extracted_docs


async def _post_or_update_card(
    prop: Any,
    ctx: PipelineExecutionContext,
    status_notifier: SlackStatusNotifier,
) -> None:
    """Update status message in-place with approval card, or post if subsequent."""
    card_params = ApprovalCardParams(
        proposal_id=prop.proposal_id,
        file_name=prop.file_name,
        file_format=prop.file_format,
        content_summary=prop.content_summary,
        preview_snippet=prop.full_content[:280],
    )
    card_text = f"Proposal for '{prop.file_name}' requires your approval."
    blocks = build_approval_card(card_params)

    finalized = False
    if not status_notifier.has_finalized:
        finalized = await status_notifier.finalize(text=card_text, blocks=blocks)
    if not finalized:
        await ctx.client.chat_postMessage(
            channel=ctx.channel_id,
            thread_ts=ctx.thread_ts,
            text=card_text,
            blocks=blocks,
        )


async def _dispatch_new_proposals(
    new_proposals: set[str],
    ctx: PipelineExecutionContext,
    status_notifier: SlackStatusNotifier,
) -> None:
    """Post or in-place update Block Kit approval cards for newly created proposals."""
    for prop_id in new_proposals:
        prop = _proposals_cache.get(prop_id)
        if prop is not None:
            _proposals_cache[prop_id] = prop.__class__(
                proposal_id=prop.proposal_id,
                file_name=prop.file_name,
                file_format=prop.file_format,
                content_summary=prop.content_summary,
                full_content=prop.full_content,
                channel_id=ctx.channel_id,
                thread_ts=ctx.thread_ts,
                user_id=ctx.user_id,
                created_at=prop.created_at,
                ttl_seconds=prop.ttl_seconds,
            )
            await _post_or_update_card(prop, ctx, status_notifier)


async def _invoke_agent_graph(
    ctx: PipelineExecutionContext,
    prompt: str,
    callbacks: list[Any] | None = None,
) -> dict[str, Any] | None:
    """Invoke the LangGraph agent and return output or post failure notification."""
    thread_config = make_thread_config(ctx.channel_id, ctx.thread_ts)
    if callbacks:
        thread_config["callbacks"] = callbacks

    initial_input = {
        "messages": [HumanMessage(content=prompt)],
        "channel_id": ctx.channel_id,
        "thread_ts": ctx.thread_ts,
        "user_id": ctx.user_id,
    }

    try:
        output: dict[str, Any] = await ctx.agent_graph.ainvoke(initial_input, config=thread_config)
        return output
    except Exception as exc:
        err_msg = str(exc)
        logger.error(
            f"LangGraph agent execution failed: {err_msg}",
            exc_info=True,
            extra={"ChannelId": ctx.channel_id, "ThreadTs": ctx.thread_ts},
        )
        await ctx.client.chat_postMessage(
            channel=ctx.channel_id,
            thread_ts=ctx.thread_ts,
            text=f"⚠️ Error communicating with AI model: {err_msg}",
        )
        return None


async def _dispatch_final_response(
    messages: list[Any],
    has_proposals: bool,
    ctx: PipelineExecutionContext,
    status_notifier: SlackStatusNotifier,
) -> None:
    """Post or in-place update final textual response from agent when no proposals are pending."""
    if messages and not has_proposals:
        reply_content = getattr(messages[-1], "content", "")
        if reply_content and isinstance(reply_content, str):
            finalized = await status_notifier.finalize(text=reply_content)
            if not finalized:
                await ctx.client.chat_postMessage(
                    channel=ctx.channel_id,
                    thread_ts=ctx.thread_ts,
                    text=reply_content,
                )


async def _prepare_prompt(
    ctx: PipelineExecutionContext,
    status_notifier: SlackStatusNotifier,
) -> str:
    """Download attachments, update status if present, and synthesize prompt."""
    if ctx.files:
        await status_notifier.update(f"📊 _Analyzing {len(ctx.files)} attached file(s)..._")
    extracted_docs = await _download_and_extract_attachments(ctx.files, ctx.settings)
    return synthesize_prompt_with_files(ctx.raw_text, extracted_docs)


async def _upload_generated_charts(
    charts: list[GeneratedChart],
    ctx: PipelineExecutionContext,
) -> None:
    """Upload newly generated chart PNG files to the Slack conversation thread."""
    for chart in charts:
        is_chart_ready = chart.file_path.is_file()
        if is_chart_ready:
            chart_bytes = chart.file_path.read_bytes()
            clean_title = "".join(c for c in chart.title if c.isalnum() or c in (" ", "_", "-"))
            clean_slug = clean_title.strip().replace(" ", "_").lower()
            file_name = f"{clean_slug or 'chart'}.png"
            upload_params = UploadDocumentParams(
                client=ctx.client,
                channel_id=ctx.channel_id,
                thread_ts=ctx.thread_ts,
                file_bytes=chart_bytes,
                file_name=file_name,
                title=chart.title,
                initial_comment=f"📊 *{chart.title}*",
            )
            await upload_generated_document(upload_params)


async def _handle_agent_output(
    graph_output: dict[str, Any],
    proposals_before: set[str],
    charts_before_count: int,
    ctx: PipelineExecutionContext,
    status_notifier: SlackStatusNotifier,
) -> None:
    """Dispatch any new proposals, the final agent reply, and generated charts."""
    new_proposals = set(_proposals_cache.keys()) - proposals_before
    await _dispatch_new_proposals(new_proposals, ctx, status_notifier)
    messages = graph_output.get("messages", [])
    has_proposals = len(new_proposals) > 0
    await _dispatch_final_response(messages, has_proposals, ctx, status_notifier)
    new_charts = get_generated_charts()[charts_before_count:]
    await _upload_generated_charts(new_charts, ctx)


async def _execute_pipeline_run(
    ctx: PipelineExecutionContext,
    status_notifier: SlackStatusNotifier,
) -> None:
    """Execute agent reasoning and handle proposal, response, and chart outputs."""
    final_prompt = await _prepare_prompt(ctx, status_notifier)
    proposals_before = set(_proposals_cache.keys())
    charts_before_count = len(get_generated_charts())
    graph_output = await _invoke_agent_graph(
        ctx=ctx,
        prompt=final_prompt,
        callbacks=[status_notifier],
    )
    if graph_output is not None:
        await _handle_agent_output(
            graph_output,
            proposals_before,
            charts_before_count,
            ctx,
            status_notifier,
        )


async def process_message_pipeline(ctx: PipelineExecutionContext) -> None:
    """Coordinate file extraction, agent execution, and response delivery."""
    is_command_handled = await handle_system_command(ctx)
    if is_command_handled:
        return

    status_notifier = SlackStatusNotifier(
        client=ctx.client,
        channel_id=ctx.channel_id,
        thread_ts=ctx.thread_ts,
    )
    await status_notifier.start("⏳ _Thinking..._")
    try:
        await _execute_pipeline_run(ctx, status_notifier)
    finally:
        await status_notifier.cleanup()
