from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from slack_agent.slack.status import SlackStatusNotifier


@pytest.mark.asyncio
async def test_status_notifier_lifecycle() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True, "ts": "1700000000.999"}
    mock_client.chat_update.return_value = {"ok": True}
    mock_client.chat_delete.return_value = {"ok": True}

    notifier = SlackStatusNotifier(
        client=mock_client,
        channel_id="C_CHAN_1",
        thread_ts="1700000000.000",
    )

    # 1. Start posts initial status message
    await notifier.start("⏳ _Thinking..._")
    assert notifier.status_ts == "1700000000.999"
    mock_client.chat_postMessage.assert_called_once_with(
        channel="C_CHAN_1",
        thread_ts="1700000000.000",
        text="⏳ _Thinking..._",
    )

    # 2. Update modifies the message
    await notifier.update("📊 _Analyzing files..._")
    mock_client.chat_update.assert_called_once_with(
        channel="C_CHAN_1",
        ts="1700000000.999",
        text="📊 _Analyzing files..._",
    )

    # 3. Cleanup deletes the message
    await notifier.cleanup()
    mock_client.chat_delete.assert_called_once_with(
        channel="C_CHAN_1",
        ts="1700000000.999",
    )
    assert notifier.status_ts is None


@pytest.mark.asyncio
async def test_status_notifier_tool_callbacks() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True, "ts": "1700000000.999"}
    mock_client.chat_update.return_value = {"ok": True}

    notifier = SlackStatusNotifier(
        client=mock_client,
        channel_id="C_CHAN_1",
        thread_ts="1700000000.000",
    )
    await notifier.start()

    # Tool: web_search
    await notifier.on_tool_start(
        serialized={"name": "web_search"},
        input_str="",
        inputs={"query": "python 3.13 features"},
    )
    mock_client.chat_update.assert_called_with(
        channel="C_CHAN_1",
        ts="1700000000.999",
        text='🔍 _Searching the web for "python 3.13 features"..._',
    )

    # Tool: fetch_web_page
    await notifier.on_tool_start(
        serialized={"name": "fetch_web_page"},
        input_str="",
        inputs={"url": "https://drarefin.com/gallbladder-operation-cost"},
    )
    mock_client.chat_update.assert_called_with(
        channel="C_CHAN_1",
        ts="1700000000.999",
        text="📄 _Reading article from drarefin.com..._",
    )

    # Tool: generate_chart
    await notifier.on_tool_start(
        serialized={"name": "generate_chart"},
        input_str="",
        inputs={"chart_type": "bar"},
    )
    mock_client.chat_update.assert_called_with(
        channel="C_CHAN_1",
        ts="1700000000.999",
        text="📊 _Generating bar chart..._",
    )

    # Tool: propose_file_write
    await notifier.on_tool_start(
        serialized={"name": "propose_file_write"},
        input_str="",
        inputs={"file_name": "summary.pdf"},
    )
    mock_client.chat_update.assert_called_with(
        channel="C_CHAN_1",
        ts="1700000000.999",
        text="✍️ _Drafting report proposal for 'summary.pdf'..._",
    )


def test_status_notifier_domain_extraction() -> None:
    assert SlackStatusNotifier._extract_domain("https://www.python.org/downloads") == "python.org"
    assert SlackStatusNotifier._extract_domain("http://example.com/page?query=1") == "example.com"
    assert SlackStatusNotifier._extract_domain("invalid-url") == "invalid-url"


@pytest.mark.asyncio
async def test_status_notifier_in_place_finalization() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True, "ts": "1700000000.888"}
    mock_client.chat_update.return_value = {"ok": True}
    mock_client.chat_delete.return_value = {"ok": True}

    notifier = SlackStatusNotifier(
        client=mock_client,
        channel_id="C_CHAN_2",
        thread_ts="1700000000.000",
    )
    await notifier.start("⏳ _Thinking..._")
    assert notifier.has_finalized is False

    # Finalize in-place with answer text
    success = await notifier.finalize(text="This is the final answer.")
    assert success is True
    assert notifier.has_finalized is True
    mock_client.chat_update.assert_called_with(
        channel="C_CHAN_2",
        ts="1700000000.888",
        text="This is the final answer.",
    )

    # Cleanup should NOT delete the finalized message
    await notifier.cleanup()
    assert mock_client.chat_delete.called is False
    assert notifier.status_ts is None
