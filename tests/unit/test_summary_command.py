from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import SecretStr
from slack_sdk.web.slack_response import SlackResponse

from slack_agent.core.config import Settings
from slack_agent.slack.handlers.commands import (
    CommandType,
    _extract_conversation_turns,
    _generate_summary_text,
    _handle_summary_command,
    parse_system_command,
)
from slack_agent.slack.handlers.messages import PipelineExecutionContext


def test_parse_summary_command_variants() -> None:
    assert parse_system_command("summary") == CommandType.Summary
    assert parse_system_command("/summary") == CommandType.Summary
    assert parse_system_command("summarize") == CommandType.Summary
    assert parse_system_command("/summarize") == CommandType.Summary
    assert parse_system_command("recap") == CommandType.Summary
    assert parse_system_command("@kita-ops summary") == CommandType.Summary
    assert parse_system_command("<@U12345> /summary") == CommandType.Summary


def test_extract_conversation_turns_filters_and_limits() -> None:
    messages = [
        SystemMessage(content="System prompt"),
        HumanMessage(content="Turn 1"),
        AIMessage(content="Turn 2"),
        ToolMessage(content="Tool output", tool_call_id="call_1"),
        HumanMessage(content="Turn 3"),
        AIMessage(content="Turn 4"),
        HumanMessage(content="Turn 5"),
        AIMessage(content="Turn 6"),
        HumanMessage(content="   "),  # Empty content should be skipped
    ]

    turns = _extract_conversation_turns(messages, limit=5)
    assert len(turns) == 5
    assert turns[0] == ("Assistant", "Turn 2")
    assert turns[1] == ("User", "Turn 3")
    assert turns[2] == ("Assistant", "Turn 4")
    assert turns[3] == ("User", "Turn 5")
    assert turns[4] == ("Assistant", "Turn 6")


@pytest.mark.asyncio
async def test_generate_summary_text_fallback_without_creds() -> None:
    settings = Settings(
        slack_bot_token=SecretStr("xoxb-test"),
        slack_app_token=SecretStr("xapp-test"),
        openrouter_api_key=SecretStr(""),
    )
    turns = [
        ("User", "What are KITA's forklift courses?"),
        ("Assistant", "KITA provides TLILIC0003 Licence to operate a forklift truck."),
    ]
    summary = await _generate_summary_text(turns, settings)
    assert "Overview" in summary
    assert "Key Discussions" in summary
    assert "What are KITA's forklift courses?" in summary
    assert "TLILIC0003" in summary


@pytest.mark.asyncio
async def test_handle_summary_command_empty_history() -> None:
    client = AsyncMock()
    client.conversations_replies = AsyncMock(return_value={"messages": []})
    client.conversations_history = AsyncMock(return_value={"messages": []})
    graph = MagicMock()
    state = MagicMock()
    state.values = {"messages": []}
    graph.aget_state = AsyncMock(return_value=state)

    ctx = PipelineExecutionContext(
        channel_id="C123",
        thread_ts="12345.678",
        user_id="U123",
        raw_text="/summary",
        files=[],
        client=client,
        settings=Settings(
            slack_bot_token=SecretStr("xoxb-test"),
            slack_app_token=SecretStr("xapp-test"),
        ),
        agent_graph=graph,
    )

    await _handle_summary_command(ctx)
    assert client.chat_postMessage.called or client.chat_update.called
    update_kwargs = getattr(client.chat_update.call_args, "kwargs", {})
    post_kwargs = getattr(client.chat_postMessage.call_args, "kwargs", {})
    text = update_kwargs.get("text", "") or post_kwargs.get("text", "")
    assert "No previous conversation history" in text


@pytest.mark.asyncio
async def test_handle_summary_command_with_history() -> None:
    client = AsyncMock()
    graph = MagicMock()
    state = MagicMock()
    state.values = {
        "messages": [
            HumanMessage(content="Hello"),
            AIMessage(content="Welcome to KITA"),
        ]
    }
    graph.aget_state = AsyncMock(return_value=state)

    settings = Settings(
        slack_bot_token=SecretStr("xoxb-test"),
        slack_app_token=SecretStr("xapp-test"),
        agent_name="KITA-Analyst",
        accent_color="#007A5A",
    )

    ctx = PipelineExecutionContext(
        channel_id="C123",
        thread_ts="12345.678",
        user_id="U123",
        raw_text="/summary",
        files=[],
        client=client,
        settings=settings,
        agent_graph=graph,
    )

    await _handle_summary_command(ctx)
    assert client.chat_postMessage.called or client.chat_update.called
    update_kwargs = getattr(client.chat_update.call_args, "kwargs", {})
    post_kwargs = getattr(client.chat_postMessage.call_args, "kwargs", {})
    card_kwargs = update_kwargs if "attachments" in update_kwargs else post_kwargs
    assert "attachments" in card_kwargs
    attachments = card_kwargs["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["color"] == "#007A5A"


@pytest.mark.asyncio
async def test_handle_summary_command_slack_api_fallback() -> None:
    client = AsyncMock()
    graph = MagicMock()
    state = MagicMock()
    state.values = {"messages": []}
    graph.aget_state = AsyncMock(return_value=state)

    client.conversations_replies = AsyncMock(
        return_value={
            "messages": [
                {"user": "U1", "text": "When is the next dogging course?"},
                {"bot_id": "B1", "text": "Next dogging DG course starts on Monday in Welshpool."},
                {"user": "U1", "text": "/summary"},
            ]
        }
    )

    settings = Settings(
        slack_bot_token=SecretStr("xoxb-test"),
        slack_app_token=SecretStr("xapp-test"),
        agent_name="AIAssistant",
        accent_color="#1A85FF",
    )

    ctx = PipelineExecutionContext(
        channel_id="C123",
        thread_ts="12345.678",
        user_id="U123",
        raw_text="/summary",
        files=[],
        client=client,
        settings=settings,
        agent_graph=graph,
        is_thread_reply=True,
    )

    await _handle_summary_command(ctx)
    assert client.chat_postMessage.called or client.chat_update.called
    update_kwargs = getattr(client.chat_update.call_args, "kwargs", {})
    post_kwargs = getattr(client.chat_postMessage.call_args, "kwargs", {})
    card_kwargs = update_kwargs if "attachments" in update_kwargs else post_kwargs
    assert "attachments" in card_kwargs
    attachments = card_kwargs["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["color"] == "#1A85FF"


@pytest.mark.asyncio
async def test_handle_summary_command_channel_history_fallback() -> None:
    client = AsyncMock()
    graph = MagicMock()
    state = MagicMock()
    state.values = {"messages": []}
    graph.aget_state = AsyncMock(return_value=state)

    client.conversations_history = AsyncMock(
        return_value={
            "messages": [
                {"user": "U1", "text": "/summary"},
                {"bot_id": "B1", "text": "Forklift course available this Friday."},
                {"user": "U1", "text": "Any forklift spots?"},
            ]
        }
    )

    settings = Settings(
        slack_bot_token=SecretStr("xoxb-test"),
        slack_app_token=SecretStr("xapp-test"),
        agent_name="AIAssistant",
        accent_color="#1A85FF",
    )

    ctx = PipelineExecutionContext(
        channel_id="C123",
        thread_ts="12345.678",
        user_id="U123",
        raw_text="/summary",
        files=[],
        client=client,
        settings=settings,
        agent_graph=graph,
        is_thread_reply=False,
    )

    await _handle_summary_command(ctx)
    assert client.chat_postMessage.called or client.chat_update.called
    update_kwargs = getattr(client.chat_update.call_args, "kwargs", {})
    post_kwargs = getattr(client.chat_postMessage.call_args, "kwargs", {})
    card_kwargs = update_kwargs if "attachments" in update_kwargs else post_kwargs
    assert "attachments" in card_kwargs
    attachments = card_kwargs["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["color"] == "#1A85FF"


@pytest.mark.asyncio
async def test_handle_summary_command_direct_message_history() -> None:
    client = AsyncMock()
    graph = MagicMock()
    state = MagicMock()
    state.values = {"messages": []}
    graph.aget_state = AsyncMock(return_value=state)

    fake_slack_response = SlackResponse(
        client=None,
        http_verb="POST",
        api_url="https://slack.com/api/conversations.history",
        req_args={},
        headers={},
        status_code=200,
        data={
            "ok": True,
            "messages": [
                {"user": "U1", "text": "summary"},
                {"bot_id": "B1", "text": "We offer Working at Heights courses on Thursdays."},
                {"user": "U1", "text": "Hi, do you offer working at heights?"},
            ],
        },
    )
    client.conversations_history = AsyncMock(return_value=fake_slack_response)

    settings = Settings(
        slack_bot_token=SecretStr("xoxb-test"),
        slack_app_token=SecretStr("xapp-test"),
        agent_name="KITA-Analyst",
        accent_color="#007A5A",
    )

    ctx = PipelineExecutionContext(
        channel_id="D12345678",
        thread_ts="12345.678",
        user_id="U123",
        raw_text="summary",
        files=[],
        client=client,
        settings=settings,
        agent_graph=graph,
        is_thread_reply=False,
    )

    await _handle_summary_command(ctx)
    assert client.chat_postMessage.called or client.chat_update.called
    update_kwargs = getattr(client.chat_update.call_args, "kwargs", {})
    post_kwargs = getattr(client.chat_postMessage.call_args, "kwargs", {})
    card_kwargs = update_kwargs if "attachments" in update_kwargs else post_kwargs
    assert "attachments" in card_kwargs
    assert "Direct Message" in card_kwargs["text"]
    attachments = card_kwargs["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["color"] == "#007A5A"


@pytest.mark.asyncio
async def test_handle_summary_command_channel_with_thread_replies_expanded() -> None:
    client = AsyncMock()
    graph = MagicMock()
    state = MagicMock()
    state.values = {"messages": []}
    graph.aget_state = AsyncMock(return_value=state)

    client.conversations_history = AsyncMock(
        return_value={
            "messages": [
                {"user": "U1", "ts": "200.1", "text": "summary"},
                {
                    "user": "U1",
                    "ts": "100.1",
                    "text": "Who is teaching dogging this week?",
                    "reply_count": 2,
                },
            ]
        }
    )
    client.conversations_replies = AsyncMock(
        return_value={
            "messages": [
                {"user": "U1", "ts": "100.1", "text": "Who is teaching dogging this week?"},
                {"user": "U2", "ts": "100.2", "text": "Dave is leading Welshpool classes."},
                {"user": "U1", "ts": "100.3", "text": "Confirmed, thank you!"},
            ]
        }
    )

    settings = Settings(
        slack_bot_token=SecretStr("xoxb-test"),
        slack_app_token=SecretStr("xapp-test"),
        agent_name="AIAssistant",
        accent_color="#1A85FF",
    )

    ctx = PipelineExecutionContext(
        channel_id="C999888",
        thread_ts="200.1",
        user_id="U123",
        raw_text="summary",
        files=[],
        client=client,
        settings=settings,
        agent_graph=graph,
        is_thread_reply=False,
    )

    await _handle_summary_command(ctx)
    client.conversations_replies.assert_awaited_with(
        channel="C999888",
        ts="100.1",
        limit=25,
    )
    assert client.chat_postMessage.called or client.chat_update.called
    update_kwargs = getattr(client.chat_update.call_args, "kwargs", {})
    post_kwargs = getattr(client.chat_postMessage.call_args, "kwargs", {})
    card_kwargs = update_kwargs if "attachments" in update_kwargs else post_kwargs
    assert "attachments" in card_kwargs
    assert "Channel" in card_kwargs["text"]
    attachments = card_kwargs["attachments"]
    assert len(attachments) == 1
    assert attachments[0]["color"] == "#1A85FF"
