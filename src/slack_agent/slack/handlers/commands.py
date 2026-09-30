from __future__ import annotations

import re
from enum import Enum
from typing import TYPE_CHECKING, Any

from slack_agent.agent.checkpointer import make_thread_config
from slack_agent.agent.proposals.store import _proposals_cache
from slack_agent.core.logger import get_logger
from slack_agent.slack.blocks.system_cards import (
    StatusCardParams,
    build_help_card,
    build_status_card,
)

if TYPE_CHECKING:
    from slack_agent.slack.handlers.messages import PipelineExecutionContext

logger = get_logger(__name__)


class CommandType(Enum):
    """Enumeration of recognized fast-path system commands."""

    Unknown = "unknown"
    Help = "help"
    Status = "status"
    Reset = "reset"


_HELP_COMMANDS: frozenset[str] = frozenset(
    {
        "help",
        "/help",
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


def parse_system_command(raw_text: str) -> CommandType:
    """Parse raw user message into a recognized fast-path system command."""
    text_without_mention = re.sub(r"<@[A-Z0-9]+>", "", raw_text).strip()
    cleaned = re.sub(r"^@\w+\s*", "", text_without_mention).strip().lower()
    cleaned = cleaned.strip(".!?")

    if cleaned in _HELP_COMMANDS:
        return CommandType.Help
    if cleaned in _STATUS_COMMANDS:
        return CommandType.Status
    if cleaned in _RESET_COMMANDS:
        return CommandType.Reset
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


async def _count_thread_messages(ctx: PipelineExecutionContext) -> int:
    """Count number of messages stored in the thread's checkpoint state."""
    is_stateful = hasattr(ctx.agent_graph, "aget_state")
    if is_stateful:
        thread_config = make_thread_config(ctx.channel_id, ctx.thread_ts)
        state = await ctx.agent_graph.aget_state(thread_config)
        state_values = getattr(state, "values", None)
        return _extract_messages_length(state_values)
    return 0


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
    return False
