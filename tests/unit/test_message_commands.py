from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.base import empty_checkpoint
from langgraph.checkpoint.memory import MemorySaver

from slack_agent.agent.proposals.store import FileProposal, reset_proposal_store, save_proposal
from slack_agent.core.config import Settings
from slack_agent.slack.blocks.system_cards import (
    StatusCardParams,
    build_help_card,
    build_status_card,
)
from slack_agent.slack.handlers.commands import (
    CommandType,
    _handle_help_command,
    _handle_status_command,
    handle_system_command,
    parse_system_command,
)
from slack_agent.slack.handlers.messages import (
    PipelineExecutionContext,
    _handle_reset_command,
    _is_reset_command,
    _purge_thread_checkpoint,
    process_message_pipeline,
)


@pytest.mark.parametrize(
    "raw_input",
    [
        "reset",
        "clear",
        "/reset",
        "/clear",
        "RESET",
        "Clear",
        "<@U12345> reset",
        "<@U999ABC>   clear  ",
        "@bot reset",
        "@slackbot clear",
        "reset context",
        "clear context",
        "reset thread",
        "clear thread",
        "reset memory",
        "clear memory",
        "clear history",
        "please reset",
        "reset please",
        "please clear",
        "clear please",
        "reset.",
        "clear!",
    ],
)
def test_is_reset_command_positive(raw_input: str) -> None:
    assert _is_reset_command(raw_input) is True


@pytest.mark.parametrize(
    "raw_input",
    [
        "how do I reset my password?",
        "clear the kitchen table",
        "can you reset the values in the report?",
        "what does clear mean?",
        "hello bot",
        "",
        "   ",
        "explain reset vs revert in git",
    ],
)
def test_is_reset_command_negative(raw_input: str) -> None:
    assert _is_reset_command(raw_input) is False


@pytest.mark.asyncio
async def test_purge_thread_checkpoint_with_memory_saver() -> None:
    saver = MemorySaver()
    thread_key = "C_CHANNEL_1:T_TS_1"
    config: RunnableConfig = {"configurable": {"thread_id": thread_key, "checkpoint_ns": ""}}
    chk = empty_checkpoint()
    await saver.aput(config, chk, {}, {})

    # Checkpoint exists before purge
    checkpoint_before = await saver.aget_tuple(config)
    assert checkpoint_before is not None

    # Purge checkpoint
    await _purge_thread_checkpoint(saver, thread_key)

    # Checkpoint removed after purge
    checkpoint_after = await saver.aget_tuple(config)
    assert checkpoint_after is None


@pytest.mark.asyncio
async def test_purge_thread_checkpoint_with_none() -> None:
    # Does not raise an error when checkpointer is None
    await _purge_thread_checkpoint(None, "C_CHANNEL_1:T_TS_1")


@pytest.mark.asyncio
async def test_handle_reset_command_posts_confirmation() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True}

    saver = MemorySaver()
    thread_key = "C_TEST:T_123"
    config: RunnableConfig = {"configurable": {"thread_id": thread_key, "checkpoint_ns": ""}}
    await saver.aput(config, empty_checkpoint(), {}, {})

    mock_graph = MagicMock()
    mock_graph.checkpointer = saver

    ctx = PipelineExecutionContext(
        channel_id="C_TEST",
        thread_ts="T_123",
        user_id="U_USER_1",
        raw_text="reset",
        files=[],
        client=mock_client,
        settings=Settings(),
        agent_graph=mock_graph,
    )

    await _handle_reset_command(ctx)

    # Verify checkpointer was purged
    assert (await saver.aget_tuple(config)) is None

    # Verify confirmation message was posted to Slack
    assert mock_client.chat_postMessage.called
    call_kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert call_kwargs["channel"] == "C_TEST"
    assert call_kwargs["thread_ts"] == "T_123"
    assert "Thread memory cleared" in call_kwargs["text"]


@pytest.mark.asyncio
async def test_process_message_pipeline_reset_bypasses_llm() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True}

    mock_graph = AsyncMock()
    mock_graph.ainvoke = AsyncMock()

    ctx = PipelineExecutionContext(
        channel_id="C_TEST",
        thread_ts="T_123",
        user_id="U_USER_1",
        raw_text="<@UBOT123> clear",
        files=[],
        client=mock_client,
        settings=Settings(),
        agent_graph=mock_graph,
    )

    await process_message_pipeline(ctx)

    # Agent graph / LLM should never be invoked for reset command
    assert not mock_graph.ainvoke.called
    assert mock_client.chat_postMessage.called
    call_kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert "Thread memory cleared" in call_kwargs["text"]


@pytest.mark.parametrize(
    "raw_input",
    [
        "help",
        "/help",
        "HELP",
        "<@U12345> help",
        "<@U999ABC>   /help  ",
        "@bot help",
        "@slackbot commands",
        "commands",
        "/commands",
        "help me",
        "features",
    ],
)
def test_parse_system_command_help(raw_input: str) -> None:
    assert parse_system_command(raw_input) == CommandType.Help


@pytest.mark.parametrize(
    "raw_input",
    [
        "status",
        "/status",
        "STATUS",
        "<@U12345> status",
        "<@U999ABC>   /status  ",
        "@bot status",
        "@slackbot info",
        "info",
        "/info",
        "diagnostics",
        "stats",
        "thread status",
        "system status",
    ],
)
def test_parse_system_command_status(raw_input: str) -> None:
    assert parse_system_command(raw_input) == CommandType.Status


def test_build_help_card_structure() -> None:
    blocks = build_help_card()
    assert len(blocks) >= 4
    header_block = blocks[0]
    assert header_block["type"] == "header"
    assert "Guide" in header_block["text"]["text"]

    all_texts = [str(b.get("text", {}).get("text", "")) for b in blocks if "text" in b]
    combined = " ".join(all_texts)
    assert "File Analysis" in combined
    assert "Data Charts" in combined
    assert "Web Lookups" in combined
    assert "Write Gate" in combined
    assert "@AIAssistant help" in combined
    assert "@AIAssistant status" in combined
    assert "@AIAssistant reset" in combined
    assert "@kita-analyst" in combined
    assert "Direct Chat" in combined
    assert "Group Chat" in combined


def test_build_status_card_structure() -> None:
    params = StatusCardParams(
        channel_id="C_DIAG_101",
        thread_ts="1700000000.999",
        message_count=5,
        model_name="anthropic/claude-3.5-sonnet",
        storage_backend="SQLite (Persistent)",
        pending_proposals_count=2,
    )
    blocks = build_status_card(params)
    assert len(blocks) >= 2
    assert blocks[0]["type"] == "header"

    section_fields = blocks[1].get("fields", [])
    fields_text = " ".join(f.get("text", "") for f in section_fields)
    assert "C_DIAG_101:1700000000.999" in fields_text
    assert "*5* message(s) stored" in fields_text
    assert "claude-3.5-sonnet" in fields_text
    assert "SQLite (Persistent)" in fields_text
    assert "*2* awaiting review" in fields_text


@pytest.mark.asyncio
async def test_handle_help_command_renders_blocks() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True}

    ctx = PipelineExecutionContext(
        channel_id="C_HELP_TEST",
        thread_ts="T_HELP_TS",
        user_id="U_HELP_USER",
        raw_text="help",
        files=[],
        client=mock_client,
        settings=Settings(),
        agent_graph=MagicMock(),
    )

    await _handle_help_command(ctx)

    assert mock_client.chat_postMessage.called
    kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert kwargs["channel"] == "C_HELP_TEST"
    assert kwargs["thread_ts"] == "T_HELP_TS"
    assert "blocks" in kwargs
    assert len(kwargs["blocks"]) > 0


@pytest.mark.asyncio
async def test_handle_status_command_with_metrics() -> None:
    reset_proposal_store()
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True}

    # Setup mock state snapshot
    mock_state = MagicMock()
    mock_state.values = {"messages": ["msg1", "msg2", "msg3"]}

    mock_graph = MagicMock()
    mock_graph.aget_state = AsyncMock(return_value=mock_state)
    mock_graph.checkpointer = MagicMock()
    mock_graph.checkpointer.__class__.__name__ = "AsyncSqliteSaver"

    # Register a proposal for this thread
    save_proposal(
        FileProposal(
            proposal_id="prop_diag_test",
            file_name="report.pdf",
            file_format="pdf",
            content_summary="Diagnostic summary",
            full_content="Draft content",
            channel_id="C_STATUS_TEST",
            thread_ts="T_STATUS_TS",
            user_id="U_STATUS_USER",
            created_at=1000.0,
            ttl_seconds=3600,
        )
    )

    ctx = PipelineExecutionContext(
        channel_id="C_STATUS_TEST",
        thread_ts="T_STATUS_TS",
        user_id="U_STATUS_USER",
        raw_text="status",
        files=[],
        client=mock_client,
        settings=Settings(),
        agent_graph=mock_graph,
    )

    await _handle_status_command(ctx)

    assert mock_client.chat_postMessage.called
    kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert kwargs["channel"] == "C_STATUS_TEST"
    assert kwargs["thread_ts"] == "T_STATUS_TS"
    assert "blocks" in kwargs

    fields = kwargs["blocks"][1]["fields"]
    fields_str = " ".join(f["text"] for f in fields)
    assert "*3* message(s) stored" in fields_str
    assert "SQLite (Persistent)" in fields_str
    assert "*1* awaiting review" in fields_str
    reset_proposal_store()


@pytest.mark.asyncio
async def test_process_message_pipeline_help_bypasses_llm() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True}
    mock_graph = AsyncMock()
    mock_graph.ainvoke = AsyncMock()

    ctx = PipelineExecutionContext(
        channel_id="C_TEST",
        thread_ts="T_123",
        user_id="U_USER_1",
        raw_text="<@UBOT123> help",
        files=[],
        client=mock_client,
        settings=Settings(),
        agent_graph=mock_graph,
    )

    await process_message_pipeline(ctx)

    assert not mock_graph.ainvoke.called
    assert mock_client.chat_postMessage.called
    kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert "blocks" in kwargs


@pytest.mark.asyncio
async def test_process_message_pipeline_status_bypasses_llm() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True}
    mock_graph = AsyncMock()
    mock_graph.ainvoke = AsyncMock()

    ctx = PipelineExecutionContext(
        channel_id="C_TEST",
        thread_ts="T_123",
        user_id="U_USER_1",
        raw_text="@bot /status",
        files=[],
        client=mock_client,
        settings=Settings(),
        agent_graph=mock_graph,
    )

    await process_message_pipeline(ctx)

    assert not mock_graph.ainvoke.called
    assert mock_client.chat_postMessage.called
    kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert "blocks" in kwargs


@pytest.mark.asyncio
async def test_handle_system_command_returns_false_for_normal_message() -> None:
    mock_client = AsyncMock()
    ctx = PipelineExecutionContext(
        channel_id="C_TEST",
        thread_ts="T_123",
        user_id="U_USER_1",
        raw_text="What are our Q3 revenue numbers?",
        files=[],
        client=mock_client,
        settings=Settings(),
        agent_graph=MagicMock(),
    )

    is_handled = await handle_system_command(ctx)
    assert is_handled is False
    assert not mock_client.chat_postMessage.called
