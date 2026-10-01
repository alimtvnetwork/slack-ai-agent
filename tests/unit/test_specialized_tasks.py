from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage
from pydantic import SecretStr

from slack_agent.agent.analyst_prompts import ANALYST_SYSTEM_PROMPT
from slack_agent.core.config import Settings
from slack_agent.slack.handlers.messages import (
    PipelineExecutionContext,
    _detect_specialized_task,
    _dispatch_final_response,
    _format_fallback_notification,
    _resolve_card_title,
)
from slack_agent.slack.status import SlackStatusNotifier


def test_detect_cv_check_task() -> None:
    directive, status = _detect_specialized_task("/cv-check please review attached JD and resumes")
    assert "[TASK: CV ANALYSIS & RANKING]" in directive
    assert "MANDATORY REQUIREMENT" in directive
    assert "Job Description (JD)" in directive
    assert "benchmark and rank" in directive
    assert status is not None
    assert "Reviewing candidate documents" in status


def test_detect_compliance_check_task() -> None:
    directive, status = _detect_specialized_task(
        "/compliance-check https://kita.edu.au/courses/forklift"
    )
    assert "[TASK: RTO MARKETING COMPLIANCE AUDIT]" in directive
    assert "Standards for RTOs" in directive
    assert status is not None
    assert "Auditing content against RTO compliance" in status


def test_detect_compliance_check_with_mentions_and_spaces() -> None:
    directive1, status1 = _detect_specialized_task("<@U012345> compliance check")
    assert "[TASK: RTO MARKETING COMPLIANCE AUDIT]" in directive1
    assert status1 is not None

    directive2, status2 = _detect_specialized_task("please check compliance on this pdf")
    assert "[TASK: RTO MARKETING COMPLIANCE AUDIT]" in directive2
    assert status2 is not None


def test_detect_cv_check_with_mentions_and_spaces() -> None:
    directive, status = _detect_specialized_task("<@U012345> cv check for candidate resumes")
    assert "[TASK: CV ANALYSIS & RANKING]" in directive
    assert status is not None


def test_detect_regular_message_no_specialized_task() -> None:
    directive, status = _detect_specialized_task("How do I enroll in rigging?")
    assert directive == ""
    assert status is None


def test_settings_for_analyst() -> None:
    primary_settings = Settings(
        slack_bot_token=SecretStr("xoxb-primary"),
        slack_app_token=SecretStr("xapp-primary"),
        agent_name="AIAssistant",
        accent_color="#1A85FF",
        analyst_slack_bot_token=SecretStr("xoxb-analyst"),
        analyst_slack_app_token=SecretStr("xapp-analyst"),
        analyst_agent_name="KITA-Analyst",
        analyst_accent_color="#007A5A",
    )

    assert primary_settings.has_slack_credentials is True
    assert primary_settings.has_analyst_slack_credentials is True

    analyst_settings = primary_settings.for_analyst()
    assert analyst_settings.agent_name == "KITA-Analyst"
    assert analyst_settings.accent_color == "#007A5A"
    assert analyst_settings.slack_bot_token.get_secret_value() == "xoxb-analyst"
    assert analyst_settings.slack_app_token.get_secret_value() == "xapp-analyst"


def test_analyst_prompt_requires_jd_before_ranking() -> None:
    assert "MANDATORY JD REQUIREMENT" in ANALYST_SYSTEM_PROMPT
    assert "DO NOT sort, rank, or assign match percentages" in ANALYST_SYSTEM_PROMPT
    assert "Job Description Required" in ANALYST_SYSTEM_PROMPT
    assert "benchmark and rank these candidates against?" in ANALYST_SYSTEM_PROMPT


def test_format_fallback_notification() -> None:
    short_text = "Short summary"
    assert _format_fallback_notification(short_text) == short_text

    long_text = "C" * 3500
    formatted = _format_fallback_notification(long_text, max_chars=2800)
    assert len(formatted) == 2800
    assert formatted.endswith("...")


@pytest.mark.asyncio
async def test_dispatch_final_response_long_compliance_payload() -> None:
    mock_client = AsyncMock()
    mock_client.chat_postMessage.return_value = {"ok": True}
    mock_client.chat_update.return_value = {"ok": True}

    status_notifier = SlackStatusNotifier(
        client=mock_client,
        channel_id="C_LONG_COMPLIANCE",
        thread_ts="1700000000.123",
    )
    status_notifier.status_ts = "1700000000.999"

    long_reply = "### Compliance Audit\n\n" + "\n".join(
        [
            f"Item {i} | Standard 1.{i % 5} | PASS | Citation information for standard clause {i}"
            * 4
            for i in range(25)
        ]
    )
    assert len(long_reply) > 5000

    ctx = PipelineExecutionContext(
        channel_id="C_LONG_COMPLIANCE",
        thread_ts="1700000000.123",
        user_id="U_USER_1",
        raw_text="/compliance-check",
        files=[],
        client=mock_client,
        settings=Settings(agent_name="KITA-Analyst", accent_color="#007A5A"),
        agent_graph=MagicMock(),
    )

    await _dispatch_final_response(
        messages=[AIMessage(content=long_reply)],
        has_proposals=False,
        ctx=ctx,
        status_notifier=status_notifier,
    )

    # Status notifier finalized the message in-place
    assert mock_client.chat_update.called
    update_kwargs = mock_client.chat_update.call_args.kwargs
    assert len(update_kwargs["text"]) <= 2800
    assert "attachments" in update_kwargs
    attachment = update_kwargs["attachments"][0]
    header_block = next((b for b in attachment["blocks"] if b.get("type") == "header"), None)
    assert header_block is not None
    assert header_block["text"]["text"] == "⚖️ RTO Marketing Compliance Audit"

    for block in attachment["blocks"]:
        if block.get("type") == "section":
            assert len(block["text"]["text"]) <= 2800


def test_resolve_card_title() -> None:
    assert _resolve_card_title("/compliance-check", "") == "⚖️ RTO Marketing Compliance Audit"
    assert _resolve_card_title("please run a cv-check", "") == "📋 Candidate CV Assessment"
    assert (
        _resolve_card_title("give me a thread summary", "") == "⏱️ Executive Timeline & Progression"
    )
    assert (
        _resolve_card_title("general prompt", "📊 *Q3 Revenue Analysis*\nDetailed data...")
        == "Q3 Revenue Analysis"
    )
    assert _resolve_card_title("hello", "Plain response without header") == ""
