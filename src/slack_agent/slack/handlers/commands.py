from __future__ import annotations

import re
from enum import Enum
from typing import TYPE_CHECKING, Any

from slack_agent.agent.checkpointer import make_thread_config
from slack_agent.agent.llm import create_llm_client
from slack_agent.agent.proposals.store import _proposals_cache
from slack_agent.core.logger import get_logger
from slack_agent.slack.blocks.response_card import (
    ResponseCardParams,
    build_response_attachment,
    format_slack_mrkdwn,
)
from slack_agent.slack.blocks.system_cards import (
    StatusCardParams,
    build_help_card,
    build_status_card,
)
from slack_agent.slack.status import SlackStatusNotifier

if TYPE_CHECKING:
    from slack_agent.slack.handlers.messages import PipelineExecutionContext

logger = get_logger(__name__)

_MIN_TOPIC_TEXT_LENGTH: int = 5
_MAX_FALLBACK_TOPICS: int = 5


class CommandType(Enum):
    """Enumeration of recognized fast-path system commands."""

    Unknown = "unknown"
    Help = "help"
    Status = "status"
    Reset = "reset"
    Summary = "summary"


_HELP_COMMANDS: frozenset[str] = frozenset(
    {
        "help",
        "/help",
        "/ai-help",
        "commands",
        "/commands",
        "help me",
        "show commands",
        "features",
    }
)

_STATUS_COMMANDS: frozenset[str] = frozenset(
    {
        "status",
        "/status",
        "/ai-status",
        "info",
        "/info",
        "diagnostics",
        "stats",
        "thread status",
        "system status",
    }
)

_RESET_COMMANDS: frozenset[str] = frozenset(
    {
        "reset",
        "clear",
        "/reset",
        "/ai-reset",
        "/clear",
        "please reset",
        "reset please",
        "please clear",
        "clear please",
        "reset context",
        "clear context",
        "reset thread",
        "clear thread",
        "reset memory",
        "clear memory",
        "clear history",
    }
)

_SUMMARY_COMMANDS: frozenset[str] = frozenset(
    {
        "summary",
        "/summary",
        "/ai-summary",
        "summarize",
        "/summarize",
        "recap",
        "/recap",
        "summary please",
        "please summarize",
        "summarize thread",
        "thread summary",
    }
)

_SUMMARY_EXCLUDE_KEYWORDS: frozenset[str] = frozenset(
    {
        "file",
        "files",
        "document",
        "documents",
        "doc",
        "docs",
        "pdf",
        "docx",
        "csv",
        "xlsx",
        "excel",
        "report",
        "contract",
        "attachment",
        "attachments",
        "uploaded",
        "upload",
    }
)

_SUMMARY_CHAT_KEYWORDS: tuple[str, ...] = (
    "this",
    "above",
    "thread",
    "channel",
    "conversation",
    "chat",
    "discussion",
    "messages",
    "last",
    "recent",
    "we discussed",
    "what we said",
    "here",
    "today",
    "our",
)


_MAX_SUMMARY_CONVERSATIONAL_WORDS: int = 8


def _is_summary_command(cleaned: str) -> bool:
    """Test if cleaned text represents a conversational thread/channel summary request."""
    if cleaned in _SUMMARY_COMMANDS:
        return True
    words = set(re.findall(r"\b\w+\b", cleaned))
    has_exclude = any(keyword in words for keyword in _SUMMARY_EXCLUDE_KEYWORDS)
    if has_exclude:
        return False
    has_summary_root = any(root in cleaned for root in ("summar", "recap"))
    if not has_summary_root:
        return False
    if len(cleaned.split()) <= _MAX_SUMMARY_CONVERSATIONAL_WORDS:
        return True
    return any(ref in cleaned for ref in _SUMMARY_CHAT_KEYWORDS)


def parse_system_command(raw_text: str) -> CommandType:
    """Parse raw user message into a recognized fast-path system command."""
    text_without_mention = re.sub(r"<@[A-Z0-9]+>", "", raw_text).strip()
    cleaned = re.sub(r"^@[\w-]+\s*", "", text_without_mention).strip().lower()
    cleaned = cleaned.strip(".!?")

    if cleaned in _HELP_COMMANDS:
        return CommandType.Help
    if cleaned in _STATUS_COMMANDS:
        return CommandType.Status
    if cleaned in _RESET_COMMANDS:
        return CommandType.Reset
    if _is_summary_command(cleaned):
        return CommandType.Summary
    return CommandType.Unknown


def _is_reset_command(raw_text: str) -> bool:
    """Backwards-compatible helper to test if text is a reset command."""
    return parse_system_command(raw_text) == CommandType.Reset


async def _purge_thread_checkpoint(checkpointer: Any | None, thread_key: str) -> None:
    """Purge state checkpointer history for a given thread key."""
    if checkpointer is None:
        return
    if hasattr(checkpointer, "adelete_thread"):
        await checkpointer.adelete_thread(thread_key)
        return
    if hasattr(checkpointer, "delete_thread"):
        checkpointer.delete_thread(thread_key)


async def _handle_reset_command(ctx: PipelineExecutionContext) -> None:
    """Purge thread context checkpoint and acknowledge to user without LLM invocation."""
    thread_key = f"{ctx.channel_id}:{ctx.thread_ts}"
    checkpointer = getattr(ctx.agent_graph, "checkpointer", None)
    await _purge_thread_checkpoint(checkpointer, thread_key)
    logger.info(
        "Purged thread context memory",
        extra={"ChannelId": ctx.channel_id, "ThreadTs": ctx.thread_ts, "UserId": ctx.user_id},
    )
    await ctx.client.chat_postMessage(
        channel=ctx.channel_id,
        thread_ts=ctx.thread_ts,
        text="🧹 _Thread memory cleared. What would you like to work on next?_",
    )


async def _handle_help_command(ctx: PipelineExecutionContext) -> None:
    """Send interactive Block Kit card detailing bot capabilities and commands."""
    blocks = build_help_card()
    await ctx.client.chat_postMessage(
        channel=ctx.channel_id,
        thread_ts=ctx.thread_ts,
        text="🤖 Slack AI Assistant Capabilities & Commands Guide",
        blocks=blocks,
    )


def _extract_messages_length(state_values: Any) -> int:
    """Safely determine message count from state values dict."""
    has_dict_values = isinstance(state_values, dict)
    if has_dict_values:
        messages = state_values.get("messages", [])
        has_list = isinstance(messages, (list, tuple))
        return len(messages) if has_list else 0
    return 0


async def _fetch_thread_messages(ctx: PipelineExecutionContext) -> list[Any]:
    """Retrieve raw messages stored in the thread checkpoint state."""
    is_stateful = hasattr(ctx.agent_graph, "aget_state")
    if not is_stateful:
        return []
    thread_config = make_thread_config(ctx.channel_id, ctx.thread_ts)
    state = await ctx.agent_graph.aget_state(thread_config)
    state_values = getattr(state, "values", None)
    if not isinstance(state_values, dict):
        return []
    messages = state_values.get("messages", [])
    is_list = isinstance(messages, (list, tuple))
    return list(messages) if is_list else []


async def _count_thread_messages(ctx: PipelineExecutionContext) -> int:
    """Count number of messages stored in the thread's checkpoint state."""
    messages = await _fetch_thread_messages(ctx)
    return len(messages)


def _determine_storage_backend(ctx: PipelineExecutionContext) -> str:
    """Identify whether persistent SQLite or in-memory checkpointer is active."""
    checkpointer = getattr(ctx.agent_graph, "checkpointer", None)
    if checkpointer is None:
        return "None"
    class_name = checkpointer.__class__.__name__
    is_sqlite = "Sqlite" in class_name
    return "SQLite (Persistent)" if is_sqlite else f"In-Memory ({class_name})"


def _count_pending_proposals(ctx: PipelineExecutionContext) -> int:
    """Count pending approval proposals registered for this thread."""
    matching_props = [
        p
        for p in _proposals_cache.values()
        if p.channel_id == ctx.channel_id and p.thread_ts == ctx.thread_ts
    ]
    return len(matching_props)


def _is_summary_text(text: str) -> bool:
    """Check if message content is a summary command."""
    cleaned = text.strip().lower()
    return _is_summary_command(cleaned)


def _is_ignorable_text(text: str) -> bool:
    """Identify status notifications, channel joins, or summary commands."""
    lower = text.lower()
    if "has joined the channel" in lower or "has left the channel" in lower:
        return True
    if any(
        phrase in lower
        for phrase in ("analyzing conversation", "synthesizing executive", "analyzing query")
    ):
        return True
    return _is_summary_text(text)


def _is_ignorable_slack_item(item: dict[str, Any], text: str) -> bool:
    """Determine if a Slack message item should be omitted from summary context."""
    subtype = str(item.get("subtype") or "").lower()
    if subtype in {"channel_join", "channel_leave", "channel_topic", "channel_purpose"}:
        return True
    return _is_ignorable_text(text)


def _extract_conversation_turns(messages: list[Any], limit: int = 25) -> list[tuple[str, str]]:
    """Extract up to N human and AI conversation turns from message history."""
    turns: list[tuple[str, str]] = []
    for msg in messages:
        msg_type = getattr(msg, "type", "")
        content = getattr(msg, "content", "")
        is_valid_text = isinstance(content, str) and bool(content.strip())
        if not is_valid_text or _is_ignorable_text(str(content)):
            continue
        if msg_type == "human":
            turns.append(("User", content.strip()))
        elif msg_type == "ai":
            turns.append(("Assistant", content.strip()))
    return turns[-limit:]


async def _request_llm_summary(
    transcript: str,
    settings: Any,
    label: str = "Conversation",
) -> str:
    """Invoke LLM to generate chronological timeline/progression summary bullets."""
    try:
        llm = create_llm_client(settings, max_tokens=3000)
        prompt = (
            "You are an executive assistant. Generate a clear Timeline / Progression Flow "
            f"summary of the following Slack {label.lower()} conversation and thread replies "
            "for team leads and stakeholders.\n\n"
            "Format strictly using clean Slack mrkdwn under 250 words following this "
            "exact structure:\n"
            "1️⃣ *Context & Initial Inquiries (Overview):* 1-2 sentences on what initiated the "
            "discussion or what goals were raised.\n"
            "2️⃣ *Key Discussions & Progression:* 2-3 chronological bullets summarizing how the "
            "conversation evolved, technical points explored, and options evaluated.\n"
            "3️⃣ *Decisions & Milestones:* 1-2 bullet points detailing agreements reached, "
            "approvals, or milestones achieved.\n"
            "4️⃣ *Action Items & Current Status:* 1-2 actionable next steps with owners, and "
            "current status (or `None identified` if closed).\n\n"
            f"Conversation Transcript:\n{transcript}"
        )
        response = await llm.ainvoke(prompt)
        content = getattr(response, "content", "")
        return content.strip() if isinstance(content, str) else ""
    except Exception as exc:
        logger.warning(f"LLM summary generation failed: {exc}")
        return ""


def _format_fallback_summary(turns: list[tuple[str, str]], label: str) -> str:
    """Produce a structured timeline/progression summary when LLM generation is unavailable."""
    topics: list[str] = []
    for role, text in turns:
        first_line = text.split("\n")[0].strip()
        cleaned = re.sub(r"^[•\-\*\s>]+", "", first_line).strip()
        has_text = bool(cleaned and cleaned not in topics and len(cleaned) > _MIN_TOPIC_TEXT_LENGTH)
        if has_text:
            topics.append(f"*{role}:* {cleaned[:100]}")

    first_turn = turns[0] if turns else ("User", "Initial discussion")
    last_turn = turns[-1] if len(turns) > 1 else first_turn

    context_sec = (
        "1️⃣ *Context & Initial Inquiries (Overview):*\n"
        f"• Initiated by *{first_turn[0]}:* {first_turn[1].splitlines()[0][:100]}."
    )
    progression_bullets = (
        "\n".join(f"• {t}" for t in topics[:_MAX_FALLBACK_TOPICS])
        if topics
        else "• General discussion and inquiries."
    )
    progression_sec = f"2️⃣ *Key Discussions & Progression:*\n{progression_bullets}"
    decisions_sec = (
        "3️⃣ *Decisions & Milestones:*\n"
        f"• Addressed latest turn from *{last_turn[0]}:* {last_turn[1].splitlines()[0][:100]}."
    )
    status_sec = (
        "4️⃣ *Action Items & Current Status:*\n"
        f"• {label} conversation captured ({len(turns)} messages); no further action required."
    )
    return f"{context_sec}\n\n{progression_sec}\n\n{decisions_sec}\n\n{status_sec}"


async def _generate_summary_text(
    turns: list[tuple[str, str]],
    settings: Any,
    label: str = "Conversation",
) -> str:
    """Synthesize conversation summary via LLM or fallback structured transcript."""
    formatted_lines = [f"{role}: {text}" for role, text in turns]
    transcript_block = "\n\n".join(formatted_lines)
    has_creds = getattr(settings, "has_openrouter_credentials", False)
    if has_creds:
        summary_result = await _request_llm_summary(transcript_block, settings, label=label)
        if summary_result:
            return summary_result

    return _format_fallback_summary(turns, label=label)


def _extract_slack_messages(resp: Any) -> list[dict[str, Any]]:
    """Safely extract list of message dicts from a Slack API response or payload dict."""
    if resp is None:
        return []
    payload = getattr(resp, "data", resp)
    has_dict_payload = isinstance(payload, dict)
    if has_dict_payload:
        messages = payload.get("messages", [])
        has_list = isinstance(messages, list)
        return [m for m in messages if isinstance(m, dict)] if has_list else []
    return []


def _extract_text_from_slack_message(item: dict[str, Any]) -> str:
    """Extract clean text content from a Slack message item."""
    raw_text = str(item.get("text", "")).strip()
    if raw_text:
        return raw_text
    attachments = item.get("attachments", [])
    has_attachments = isinstance(attachments, list)
    if has_attachments:
        for att in attachments:
            has_att_text = isinstance(att, dict) and bool(att.get("text"))
            if has_att_text:
                return str(att.get("text", "")).strip()
    return ""


async def _try_join_and_fetch_history(
    ctx: PipelineExecutionContext,
) -> list[dict[str, Any]]:
    """Attempt to join public channel if not_in_channel and fetch messages."""
    try:
        await ctx.client.conversations_join(channel=ctx.channel_id)
        joined_resp = await ctx.client.conversations_history(
            channel=ctx.channel_id,
            limit=15,
        )
        msgs = _extract_slack_messages(joined_resp)
        msgs.reverse()
        return msgs
    except Exception as exc:
        logger.warning(f"Slack join channel retry failed for {ctx.channel_id}: {exc}")
        return []


async def _fetch_thread_replies(
    ctx: PipelineExecutionContext,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Query Slack API for replies in an existing thread."""
    try:
        reply_resp = await ctx.client.conversations_replies(
            channel=ctx.channel_id,
            ts=ctx.thread_ts,
            limit=limit,
        )
        return _extract_slack_messages(reply_resp)
    except Exception as exc:
        logger.warning(f"Slack replies lookup failed: {exc}")
        return []


async def _fetch_thread_replies_for_message(
    ctx: PipelineExecutionContext,
    thread_ts: str,
) -> list[dict[str, Any]]:
    """Fetch replies for a specific thread parent message in a channel."""
    try:
        reply_resp = await ctx.client.conversations_replies(
            channel=ctx.channel_id,
            ts=thread_ts,
            limit=25,
        )
        replies = _extract_slack_messages(reply_resp)
        has_replies = len(replies) > 1
        return replies[1:] if has_replies else []
    except Exception as exc:
        logger.debug(f"Failed to fetch replies for thread {thread_ts}: {exc}")
        return []


async def _expand_channel_messages_with_replies(
    ctx: PipelineExecutionContext,
    top_level_msgs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Expand channel messages by inserting all thread replies under parent messages."""
    expanded: list[dict[str, Any]] = []
    for msg in top_level_msgs:
        expanded.append(msg)
        reply_count = int(msg.get("reply_count") or 0)
        has_thread = reply_count > 0 and bool(msg.get("ts"))
        if has_thread:
            thread_ts = str(msg["ts"])
            thread_replies = await _fetch_thread_replies_for_message(ctx, thread_ts)
            expanded.extend(thread_replies)
    return expanded


async def _call_slack_conversations_api(
    ctx: PipelineExecutionContext,
    limit: int = 25,
) -> list[dict[str, Any]]:
    """Query Slack API for thread replies or channel/DM history with replies expanded."""
    if ctx.is_thread_reply:
        thread_msgs = await _fetch_thread_replies(ctx, limit=limit)
        if thread_msgs:
            return thread_msgs

    try:
        hist_resp = await ctx.client.conversations_history(
            channel=ctx.channel_id,
            limit=limit,
        )
        msgs = _extract_slack_messages(hist_resp)
        msgs.reverse()
        return await _expand_channel_messages_with_replies(ctx, msgs)
    except Exception as exc:
        is_not_in_chan = "not_in_channel" in str(exc).lower() and not ctx.channel_id.startswith("D")
        if is_not_in_chan:
            joined_msgs = await _try_join_and_fetch_history(ctx)
            return await _expand_channel_messages_with_replies(ctx, joined_msgs)
        logger.warning(f"Slack conversation lookup failed for {ctx.channel_id}: {exc}")

    return []


def _parse_slack_messages_into_turns(
    raw_msgs: list[dict[str, Any]],
    limit: int = 25,
) -> list[tuple[str, str]]:
    """Convert raw Slack message payloads into conversational turns."""
    turns: list[tuple[str, str]] = []
    for item in raw_msgs:
        raw_text = _extract_text_from_slack_message(item)
        clean_text = re.sub(r"<@[A-Z0-9]+>", "", raw_text).strip()
        if not clean_text or _is_ignorable_slack_item(item, clean_text):
            continue
        role = "Assistant" if item.get("bot_id") else "User"
        turns.append((role, clean_text))
    return turns[-limit:]


async def _fetch_slack_history(
    ctx: PipelineExecutionContext,
    limit: int = 25,
) -> list[tuple[str, str]]:
    """Retrieve recent conversation turns directly via Slack WebClient API."""
    raw_msgs = await _call_slack_conversations_api(ctx, limit=limit)
    return _parse_slack_messages_into_turns(raw_msgs, limit=limit)


def _determine_conversation_label(ctx: PipelineExecutionContext) -> str:
    """Return appropriate user-facing label for the conversation context."""
    if ctx.is_thread_reply:
        return "Thread"
    if ctx.channel_id.startswith("D"):
        return "Direct Message"
    return "Channel"


async def _deliver_summary_card(
    turns: list[tuple[str, str]],
    label: str,
    ctx: PipelineExecutionContext,
    status_notifier: SlackStatusNotifier,
) -> None:
    """Synthesize summary and deliver response card via status notifier or postMessage."""
    await status_notifier.update("📝 _Synthesizing timeline progression summary..._")
    summary_content = await _generate_summary_text(turns, ctx.settings, label=label)
    beautified = format_slack_mrkdwn(summary_content)
    card_params = ResponseCardParams(
        text=(
            f"> ⏱️ *Executive {label} Timeline & Progression (Last {len(turns)} messages)*\n\n"
            f"{beautified}"
        ),
        agent_name=ctx.settings.agent_name,
        accent_color=ctx.settings.accent_color,
        has_footer=True,
    )
    attachment = build_response_attachment(card_params)
    finalized = await status_notifier.finalize(
        text=f"Executive {label} Timeline & Progression",
        attachments=[attachment],
    )
    if not finalized:
        await ctx.client.chat_postMessage(
            channel=ctx.channel_id,
            thread_ts=ctx.thread_ts,
            text=f"Executive {label} Timeline & Progression",
            attachments=[attachment],
        )


async def _handle_empty_summary(
    label: str,
    ctx: PipelineExecutionContext,
    status_notifier: SlackStatusNotifier,
) -> None:
    """Deliver notice when no conversation history is available."""
    empty_msg = (
        f"ℹ️ _No previous conversation history found in this {label.lower()} to summarize._\n\n"
        "💡 _Tip: Ensure `channels:history` (public channels), `groups:history` "
        "(private channels), or `im:history` (direct messages) "
        "scopes are added in api.slack.com/apps so the bot has permission to read messages._"
    )
    finalized = await status_notifier.finalize(text=empty_msg)
    if not finalized:
        await ctx.client.chat_postMessage(
            channel=ctx.channel_id,
            thread_ts=ctx.thread_ts,
            text=empty_msg,
        )


async def _gather_summary_turns(
    ctx: PipelineExecutionContext,
) -> tuple[list[tuple[str, str]], str]:
    """Extract message turns from state or Slack API and determine label."""
    turns_limit = 25
    turns = await _fetch_slack_history(ctx, limit=turns_limit)
    if not turns:
        messages = await _fetch_thread_messages(ctx)
        turns = _extract_conversation_turns(messages, limit=turns_limit)
    label = _determine_conversation_label(ctx)
    return turns, label


async def _handle_summary_command(ctx: PipelineExecutionContext) -> None:
    """Generate and post an executive summary of recent thread, channel, or DM conversation."""
    status_notifier = SlackStatusNotifier(
        client=ctx.client,
        channel_id=ctx.channel_id,
        thread_ts=ctx.thread_ts,
    )
    await status_notifier.start("⏳ _Analyzing conversation history and thread replies..._")
    try:
        turns, label = await _gather_summary_turns(ctx)
        if not turns:
            await _handle_empty_summary(label, ctx, status_notifier)
            return

        await _deliver_summary_card(turns, label, ctx, status_notifier)
    finally:
        await status_notifier.cleanup()


async def _handle_status_command(ctx: PipelineExecutionContext) -> None:
    """Assemble diagnostic metrics and post status Block Kit card into the thread."""
    message_count = await _count_thread_messages(ctx)
    storage_backend = _determine_storage_backend(ctx)
    proposals_count = _count_pending_proposals(ctx)

    params = StatusCardParams(
        channel_id=ctx.channel_id,
        thread_ts=ctx.thread_ts,
        message_count=message_count,
        model_name=ctx.settings.openrouter_model,
        storage_backend=storage_backend,
        pending_proposals_count=proposals_count,
    )
    blocks = build_status_card(params)
    await ctx.client.chat_postMessage(
        channel=ctx.channel_id,
        thread_ts=ctx.thread_ts,
        text=f"📊 Thread Status: {message_count} messages, Model: {ctx.settings.openrouter_model}",
        blocks=blocks,
    )


async def handle_system_command(ctx: PipelineExecutionContext) -> bool:
    """Detect and execute zero-token fast-path commands. Returns True if handled."""
    if bool(ctx.files):
        return False
    cmd_type = parse_system_command(ctx.raw_text)
    if cmd_type == CommandType.Reset:
        await _handle_reset_command(ctx)
        return True
    if cmd_type == CommandType.Help:
        await _handle_help_command(ctx)
        return True
    if cmd_type == CommandType.Status:
        await _handle_status_command(ctx)
        return True
    if cmd_type == CommandType.Summary:
        await _handle_summary_command(ctx)
        return True
    return False
