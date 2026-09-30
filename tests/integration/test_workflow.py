from __future__ import annotations

import time
from collections.abc import Generator
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from langchain_core.messages import AIMessage, ToolCall
from langgraph.checkpoint.memory import MemorySaver

from slack_agent.agent.graph import create_agent_graph
from slack_agent.agent.proposals.store import (
    FileProposal,
    get_proposal,
    reset_proposal_store,
    save_proposal,
)
from slack_agent.agent.tools.chart import clear_generated_charts, generate_chart
from slack_agent.agent.tools.write_gate import propose_file_write
from slack_agent.core.config import Settings
from slack_agent.core.result import Result
from slack_agent.generators.pdf import generate_pdf_bytes
from slack_agent.slack.handlers.actions import (
    execute_approved_file_generation,
    handle_edit_action,
    handle_modal_submission,
    handle_rejection_action,
)
from slack_agent.slack.handlers.messages import (
    PipelineExecutionContext,
    process_message_pipeline,
)


@pytest.fixture(autouse=True)
def clean_proposals() -> Generator[None, None, None]:
    reset_proposal_store()
    clear_generated_charts()
    yield
    reset_proposal_store()
    clear_generated_charts()


@pytest.mark.asyncio
async def test_end_to_end_pipeline_and_approval_flow() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True, "ts": "123.456"}
    mock_client.chat_update.return_value = {"ok": True}

    settings = Settings()

    # 1. Setup mock agent graph that calls propose_file_write
    async def mock_agent_invoke(
        initial_input: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        # Agent decides to call propose_file_write
        propose_file_write.invoke(
            {
                "file_name": "quarterly_summary.pdf",
                "file_format": "pdf",
                "content_summary": "Quarterly financial summary",
                "full_content": "Total revenue grew by 24% year-over-year.",
            }
        )
        return {
            "messages": [
                AIMessage(
                    content=(
                        "I have analyzed your request and prepared "
                        "the quarterly summary for review."
                    )
                )
            ]
        }

    mock_graph = AsyncMock()
    mock_graph.ainvoke = mock_agent_invoke

    sample_pdf_bytes = generate_pdf_bytes("Input", "Test Input Content").value()

    # 2. Run message pipeline with mock file download
    with patch(
        "slack_agent.slack.handlers.messages.download_slack_file",
        return_value=Result.ok(sample_pdf_bytes),
    ):
        ctx = PipelineExecutionContext(
            channel_id="C_TEST_101",
            thread_ts="1700000000.000100",
            user_id="U_TEST_USER",
            raw_text="Please summarize the uploaded file and generate a PDF report.",
            files=[
                {
                    "id": "F_SAMPLE_1",
                    "name": "input_doc.pdf",
                    "filetype": "pdf",
                    "url_private_download": "https://slack.test/files/sample.pdf",
                }
            ],
            client=mock_client,
            settings=settings,
            agent_graph=mock_graph,
        )

        await process_message_pipeline(ctx)

    # 3. Verify approval card was rendered in Slack (in-place update or post)
    assert mock_client.chat_postMessage.called
    update_kwargs = getattr(mock_client.chat_update.call_args, "kwargs", {})
    post_kwargs = getattr(mock_client.chat_postMessage.call_args, "kwargs", {})
    card_kwargs = update_kwargs if "blocks" in update_kwargs else post_kwargs
    assert card_kwargs["channel"] == "C_TEST_101"
    assert "blocks" in card_kwargs

    blocks = card_kwargs["blocks"]
    action_block = next((b for b in blocks if b.get("type") == "actions"), None)
    assert action_block is not None

    elements = action_block.get("elements", [])
    proposal_id = elements[0].get("value")
    assert proposal_id is not None
    assert proposal_id.startswith("prop_")

    # 4. Verify proposal is registered in store
    retrieved = get_proposal(proposal_id)
    assert retrieved.is_success is True
    assert retrieved.value().file_name == "quarterly_summary.pdf"

    # 5. Simulate user clicking [Approve & Write]
    with patch(
        "slack_agent.slack.handlers.actions.upload_generated_document",
        new_callable=AsyncMock,
    ) as mock_upload:
        mock_upload.return_value = Result.ok({"id": "F_UPLOADED_123"})

        await execute_approved_file_generation(
            proposal_id=proposal_id,
            channel_id="C_TEST_101",
            thread_ts="1700000000.000100",
            client=mock_client,
        )

        # 6. Verify upload was called with valid PDF bytes starting with %PDF-
        assert mock_upload.called
        upload_params = mock_upload.call_args.args[0]
        assert upload_params.file_name == "quarterly_summary.pdf"
        assert upload_params.file_bytes.startswith(b"%PDF-")

    # 7. Verify proposal was purged from store
    purged_check = get_proposal(proposal_id)
    assert purged_check.has_error is True


@pytest.mark.asyncio
async def test_end_to_end_rejection_flow() -> None:
    mock_client = AsyncMock()
    mock_client.chat_update.return_value = {"ok": True}
    mock_ack = AsyncMock()

    proposal = FileProposal(
        proposal_id="prop_reject_test",
        file_name="unwanted_file.pdf",
        file_format="pdf",
        content_summary="Unwanted document",
        full_content="Content that should not be published.",
        channel_id="C_TEST_202",
        thread_ts="1700000000.000200",
        user_id="U_USER_2",
        created_at=1000000.0,
        ttl_seconds=3600,
    )
    save_proposal(proposal)

    body = {
        "actions": [{"value": "prop_reject_test"}],
        "user": {"id": "U_USER_2"},
        "channel": {"id": "C_TEST_202"},
        "message": {"ts": "1700000000.000200"},
    }

    await handle_rejection_action(mock_ack, body, mock_client)

    assert mock_ack.called
    assert mock_client.chat_update.called
    update_kwargs = mock_client.chat_update.call_args.kwargs
    assert "rejected by <@U_USER_2>" in update_kwargs["text"]

    # Verify proposal was discarded
    assert get_proposal("prop_reject_test").has_error is True


@pytest.mark.asyncio
async def test_langgraph_tool_execution_node() -> None:
    # Test LangGraph agent workflow routing to write gate tool
    mock_llm = MagicMock()
    bound_llm = AsyncMock()

    # First invocation returns tool call
    tool_call = ToolCall(
        name="propose_file_write",
        args={
            "file_name": "langgraph_output.pdf",
            "file_format": "pdf",
            "content_summary": "LangGraph generated output",
            "full_content": "Content verified by LangGraph node.",
        },
        id="call_test_123",
    )
    bound_llm.ainvoke.side_effect = [
        AIMessage(content="", tool_calls=[tool_call]),
        AIMessage(content="File proposal created for review."),
    ]
    mock_llm.bind_tools.return_value = bound_llm

    checkpointer = MemorySaver()
    graph = create_agent_graph(mock_llm, checkpointer)

    result = await graph.ainvoke(
        {
            "messages": [AIMessage(content="Please generate the file.")],
            "channel_id": "C_TEST_303",
            "thread_ts": "1700000000.000300",
            "user_id": "U_USER_3",
        },
        config={"configurable": {"thread_id": "C_TEST_303:1700000000.000300"}},
    )

    messages = result["messages"]
    assert len(messages) >= 2

    # Verify tool response message is in state
    has_tool_message = any(getattr(m, "type", "") == "tool" for m in messages)
    assert has_tool_message is True


@pytest.mark.asyncio
async def test_end_to_end_edit_flow() -> None:
    mock_client = AsyncMock()
    mock_client.views_open.return_value = {"ok": True}
    mock_client.chat_postMessage.return_value = {"ok": True, "ts": "1700000000.000450"}
    mock_ack = AsyncMock()

    proposal = FileProposal(
        proposal_id="prop_edit_flow_test",
        file_name="initial_summary.pdf",
        file_format="pdf",
        content_summary="Original draft summary",
        full_content="Draft content that needs refinement.",
        channel_id="C_TEST_404",
        thread_ts="1700000000.000400",
        user_id="U_USER_4",
        created_at=time.time(),
        ttl_seconds=3600,
    )
    save_proposal(proposal)

    # 1. User clicks [✏️ Edit / Refine] button
    click_body = {
        "actions": [{"value": "prop_edit_flow_test"}],
        "trigger_id": "trig_edit_12345",
        "user": {"id": "U_USER_4"},
    }
    await handle_edit_action(mock_ack, click_body, mock_client)
    assert mock_ack.called
    assert mock_client.views_open.called
    open_kwargs = mock_client.views_open.call_args.kwargs
    assert open_kwargs["trigger_id"] == "trig_edit_12345"
    assert open_kwargs["view"]["callback_id"] == "submit_edit_file_proposal"
    assert open_kwargs["view"]["private_metadata"] == "prop_edit_flow_test"

    # 2. User modifies form and submits modal
    submit_body = {
        "view": {
            "private_metadata": "prop_edit_flow_test",
            "state": {
                "values": {
                    "block_file_name": {"input_file_name": {"value": "refined_summary.docx"}},
                    "block_file_format": {"input_file_format": {"value": "docx"}},
                    "block_content": {
                        "input_content": {"value": "Polished, executive-ready document content."}
                    },
                }
            },
        }
    }
    mock_ack.reset_mock()
    await handle_modal_submission(mock_ack, submit_body, mock_client)
    assert mock_ack.called
    assert mock_client.chat_postMessage.called
    post_kwargs = mock_client.chat_postMessage.call_args.kwargs
    assert post_kwargs["channel"] == "C_TEST_404"
    assert post_kwargs["thread_ts"] == "1700000000.000400"
    assert "refined_summary.docx" in post_kwargs["text"]

    # 3. Verify proposal was updated in store
    updated = get_proposal("prop_edit_flow_test")
    assert updated.is_success is True
    val = updated.value()
    assert val.file_name == "refined_summary.docx"
    assert val.file_format == "docx"
    assert val.full_content == "Polished, executive-ready document content."


@pytest.mark.asyncio
async def test_end_to_end_chart_generation_and_upload() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True, "ts": "123.456"}
    mock_client.chat_update.return_value = {"ok": True}
    mock_client.files_upload_v2.return_value = {"ok": True, "file": {"id": "F_CHART_101"}}

    settings = Settings()

    async def mock_agent_chart_invoke(
        initial_input: dict[str, Any],
        config: dict[str, Any],
    ) -> dict[str, Any]:
        generate_chart.invoke(
            {
                "chart_type": "bar",
                "title": "Quarterly Growth Analysis",
                "categories": ["Q1", "Q2", "Q3"],
                "values": [12.5, 18.2, 24.0],
            }
        )
        return {
            "messages": [
                AIMessage(
                    content="I analyzed the data and generated a bar chart showing the growth."
                )
            ]
        }

    mock_graph = AsyncMock()
    mock_graph.ainvoke = mock_agent_chart_invoke

    ctx = PipelineExecutionContext(
        channel_id="C_CHART_INTEG",
        thread_ts="1700000000.000500",
        user_id="U_CHART_USER",
        raw_text="Show me quarterly growth in a chart.",
        files=[],
        client=mock_client,
        settings=settings,
        agent_graph=mock_graph,
    )

    await process_message_pipeline(ctx)

    # 1. Verify text response was posted/updated
    assert mock_client.chat_postMessage.called or mock_client.chat_update.called

    # 2. Verify chart file was uploaded to Slack thread
    assert mock_client.files_upload_v2.called
    upload_kwargs = mock_client.files_upload_v2.call_args.kwargs
    assert upload_kwargs["channel"] == "C_CHART_INTEG"
    assert upload_kwargs["thread_ts"] == "1700000000.000500"
    assert "quarterly_growth_analysis.png" in upload_kwargs["filename"]
    assert "Quarterly Growth Analysis" in upload_kwargs["initial_comment"]
    assert upload_kwargs["file"].startswith(b"\x89PNG")
