from __future__ import annotations

import json
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from slack_agent.core.config import Settings
from slack_agent.slack.handlers.slash_commands import (
    ACTION_FILE_INPUT,
    ACTION_JD_FILE_INPUT,
    ACTION_TEXT_INPUT,
    BLOCK_FILE_UPLOAD,
    BLOCK_JD_FILE_UPLOAD,
    BLOCK_TEXT_INPUT,
    MODAL_COMPLIANCE_CALLBACK_ID,
    MODAL_CV_CALLBACK_ID,
    ModalSubmissionContext,
    SlashCommandContext,
    _extract_modal_submission,
    _hydrate_file_urls,
    build_compliance_modal,
    build_cv_modal,
    handle_modal_submission,
    handle_slash_command,
    validate_compliance_modal_submission,
    validate_cv_modal_submission,
)
from slack_agent.slack.router import register_slack_routes


def test_build_compliance_modal_structure() -> None:
    modal = build_compliance_modal(
        channel_id="C12345",
        thread_ts="111.222",
        user_id="U999",
        initial_text="https://example.com/article",
    )
    assert modal["type"] == "modal"
    assert modal["callback_id"] == MODAL_COMPLIANCE_CALLBACK_ID
    assert len(modal["title"]["text"]) <= 24

    meta = json.loads(modal["private_metadata"])
    assert meta["channel_id"] == "C12345"
    assert meta["thread_ts"] == "111.222"
    assert meta["user_id"] == "U999"

    blocks = modal["blocks"]
    file_block = next(b for b in blocks if b.get("block_id") == BLOCK_FILE_UPLOAD)
    assert file_block["element"]["type"] == "file_input"
    assert "pdf" in file_block["element"]["filetypes"]
    assert "html" in file_block["element"]["filetypes"]
    assert "htm" in file_block["element"]["filetypes"]

    notes_block = next(b for b in blocks if b.get("block_id") == BLOCK_TEXT_INPUT)
    assert notes_block["element"]["initial_value"] == "https://example.com/article"


def test_build_cv_modal_structure() -> None:
    modal = build_cv_modal(
        channel_id="C54321",
        thread_ts="",
        user_id="U888",
        initial_text="Senior Python Engineer",
    )
    assert modal["type"] == "modal"
    assert modal["callback_id"] == MODAL_CV_CALLBACK_ID
    assert len(modal["title"]["text"]) <= 24

    meta = json.loads(modal["private_metadata"])
    assert meta["channel_id"] == "C54321"
    assert meta["thread_ts"] == ""

    blocks = modal["blocks"]
    file_block = next(b for b in blocks if b.get("block_id") == BLOCK_FILE_UPLOAD)
    assert file_block["element"]["type"] == "file_input"

    jd_file_block = next(b for b in blocks if b.get("block_id") == BLOCK_JD_FILE_UPLOAD)
    assert jd_file_block["element"]["type"] == "file_input"
    assert jd_file_block["optional"] is True
    assert jd_file_block["element"]["max_files"] == 1

    jd_block = next(b for b in blocks if b.get("block_id") == BLOCK_TEXT_INPUT)
    assert jd_block["element"]["initial_value"] == "Senior Python Engineer"


def _create_test_settings() -> Settings:
    return Settings.model_construct(
        agent_name="AIAssistant",
        openrouter_model="test-model",
    )


@pytest.mark.asyncio
async def test_handle_slash_command_opens_compliance_modal() -> None:
    mock_client = AsyncMock()
    settings = _create_test_settings()
    ctx = SlashCommandContext(
        command_name="/compliance-check",
        body={
            "trigger_id": "trig_123",
            "channel_id": "C123",
            "thread_ts": "111.222",
            "user_id": "U123",
            "text": "https://kita.com.au",
        },
        client=mock_client,
        settings=settings,
        agent_graph=MagicMock(),
    )
    await handle_slash_command(ctx)

    mock_client.views_open.assert_awaited_once()
    call_kwargs = mock_client.views_open.call_args.kwargs
    assert call_kwargs["trigger_id"] == "trig_123"
    assert call_kwargs["view"]["callback_id"] == MODAL_COMPLIANCE_CALLBACK_ID


@pytest.mark.asyncio
async def test_handle_slash_command_opens_cv_modal() -> None:
    mock_client = AsyncMock()
    settings = _create_test_settings()
    ctx = SlashCommandContext(
        command_name="/cv-check",
        body={
            "trigger_id": "trig_456",
            "channel_id": "C456",
            "user_id": "U456",
            "text": "Excavator Operator",
        },
        client=mock_client,
        settings=settings,
        agent_graph=MagicMock(),
    )
    await handle_slash_command(ctx)

    mock_client.views_open.assert_awaited_once()
    call_kwargs = mock_client.views_open.call_args.kwargs
    assert call_kwargs["trigger_id"] == "trig_456"
    assert call_kwargs["view"]["callback_id"] == MODAL_CV_CALLBACK_ID


@pytest.mark.asyncio
async def test_handle_slash_command_dispatches_direct_command() -> None:
    mock_client = AsyncMock()
    settings = _create_test_settings()
    ctx = SlashCommandContext(
        command_name="/summary",
        body={
            "channel_id": "C123",
            "user_id": "U123",
            "text": "20",
        },
        client=mock_client,
        settings=settings,
        agent_graph=MagicMock(),
    )
    with patch(
        "slack_agent.slack.handlers.slash_commands.process_message_pipeline",
        new_callable=AsyncMock,
    ) as mock_pipeline:
        await handle_slash_command(ctx)
        # Give asyncio task a tick
        mock_pipeline.assert_called_once()
        pipeline_arg = mock_pipeline.call_args[0][0]
        assert pipeline_arg.raw_text == "/summary 20"
        assert pipeline_arg.channel_id == "C123"


def test_extract_modal_submission() -> None:
    view = {
        "state": {
            "values": {
                BLOCK_FILE_UPLOAD: {
                    ACTION_FILE_INPUT: {
                        "files": [
                            {"id": "F1", "name": "doc.pdf", "url_private_download": "http://d"}
                        ]
                    }
                },
                BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": "Sample notes"}},
            }
        },
        "private_metadata": json.dumps({"channel_id": "C1", "thread_ts": "ts1", "user_id": "U1"}),
    }
    files, user_text, meta = _extract_modal_submission(view)
    assert len(files) == 1
    assert files[0]["name"] == "doc.pdf"
    assert user_text == "Sample notes"
    assert meta["channel_id"] == "C1"


def test_extract_modal_submission_with_jd_file() -> None:
    view = {
        "state": {
            "values": {
                BLOCK_FILE_UPLOAD: {
                    ACTION_FILE_INPUT: {
                        "files": [
                            {
                                "id": "F1",
                                "name": "candidate.pdf",
                                "url_private_download": "http://d1",
                            }
                        ]
                    }
                },
                BLOCK_JD_FILE_UPLOAD: {
                    ACTION_JD_FILE_INPUT: {
                        "files": [
                            {
                                "id": "F2",
                                "name": "job_spec.pdf",
                                "url_private_download": "http://d2",
                            }
                        ]
                    }
                },
                BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": "Extra requirements"}},
            }
        },
        "private_metadata": json.dumps({"channel_id": "C2", "thread_ts": "ts2", "user_id": "U2"}),
    }
    files, user_text, meta = _extract_modal_submission(view)
    assert len(files) == 2
    assert files[0]["name"] == "candidate.pdf"
    assert files[1]["name"] == "job_spec.pdf"
    assert "[BENCHMARK JD: Document 'job_spec.pdf'" in user_text
    assert "Extra requirements" in user_text
    assert meta["channel_id"] == "C2"


@pytest.mark.asyncio
async def test_hydrate_file_urls() -> None:
    mock_client = AsyncMock()
    mock_client.files_info.return_value = {
        "ok": True,
        "file": {
            "id": "F99",
            "name": "resolved.pdf",
            "url_private_download": "https://slack.com/files/resolved.pdf",
            "filetype": "pdf",
        },
    }
    files = [{"id": "F99", "name": "resolved.pdf"}]
    hydrated = await _hydrate_file_urls(files, mock_client)
    assert len(hydrated) == 1
    assert hydrated[0]["url_private_download"] == "https://slack.com/files/resolved.pdf"


@pytest.mark.asyncio
async def test_handle_modal_submission_compliance() -> None:
    mock_client = AsyncMock()
    settings = _create_test_settings()
    body = {
        "view": {
            "state": {
                "values": {
                    BLOCK_FILE_UPLOAD: {
                        ACTION_FILE_INPUT: {
                            "files": [
                                {
                                    "id": "F10",
                                    "name": "kita.pdf",
                                    "url_private_download": "http://download",
                                }
                            ]
                        }
                    },
                    BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": "Check WA standard"}},
                }
            },
            "private_metadata": json.dumps(
                {"channel_id": "C_AUDIT", "thread_ts": "123.456", "user_id": "U_AUDIT"}
            ),
        }
    }
    ctx = ModalSubmissionContext(
        callback_id=MODAL_COMPLIANCE_CALLBACK_ID,
        body=body,
        client=mock_client,
        settings=settings,
        agent_graph=MagicMock(),
    )
    with patch(
        "slack_agent.slack.handlers.slash_commands.process_message_pipeline",
        new_callable=AsyncMock,
    ) as mock_pipeline:
        await handle_modal_submission(ctx)
        mock_pipeline.assert_called_once()
        pipeline_arg = mock_pipeline.call_args[0][0]
        assert pipeline_arg.channel_id == "C_AUDIT"
        assert pipeline_arg.thread_ts == "123.456"
        assert "/compliance-check Check WA standard" in pipeline_arg.raw_text
        assert len(pipeline_arg.files) == 1


def test_register_slack_routes_wires_slash_commands() -> None:
    mock_app = MagicMock()
    settings = _create_test_settings()
    register_slack_routes(
        app=mock_app,
        settings=settings,
        agent_graph=MagicMock(),
        bot_user_id="B123",
    )
    # Ensure command and view listeners were registered
    mock_app.command.assert_any_call("/help")
    mock_app.command.assert_any_call("/compliance-check")
    mock_app.command.assert_any_call("/cv-check")
    mock_app.command.assert_any_call("/summary")
    mock_app.command.assert_any_call("/status")
    mock_app.command.assert_any_call("/reset")
    mock_app.view.assert_any_call(MODAL_COMPLIANCE_CALLBACK_ID)
    mock_app.view.assert_any_call(MODAL_CV_CALLBACK_ID)


def test_validate_cv_modal_submission_fails_when_both_empty() -> None:
    view = {
        "state": {
            "values": {
                BLOCK_FILE_UPLOAD: {ACTION_FILE_INPUT: {"files": [{"id": "F1"}]}},
                BLOCK_JD_FILE_UPLOAD: {ACTION_JD_FILE_INPUT: {"files": []}},
                BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": ""}},
            }
        }
    }
    errors = validate_cv_modal_submission(view)
    assert errors is not None
    assert BLOCK_JD_FILE_UPLOAD in errors
    assert BLOCK_TEXT_INPUT in errors


def test_validate_cv_modal_submission_succeeds_with_jd_file() -> None:
    view = {
        "state": {
            "values": {
                BLOCK_FILE_UPLOAD: {ACTION_FILE_INPUT: {"files": [{"id": "F1"}]}},
                BLOCK_JD_FILE_UPLOAD: {ACTION_JD_FILE_INPUT: {"files": [{"id": "F_JD"}]}},
                BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": ""}},
            }
        }
    }
    assert validate_cv_modal_submission(view) is None


def test_validate_cv_modal_submission_succeeds_with_jd_text() -> None:
    view = {
        "state": {
            "values": {
                BLOCK_FILE_UPLOAD: {ACTION_FILE_INPUT: {"files": [{"id": "F1"}]}},
                BLOCK_JD_FILE_UPLOAD: {ACTION_JD_FILE_INPUT: {"files": []}},
                BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": "Must hold LF and DG"}},
            }
        }
    }
    assert validate_cv_modal_submission(view) is None


@pytest.mark.asyncio
async def test_on_cv_submit_rejects_empty_jd() -> None:
    mock_app = MagicMock()
    settings = _create_test_settings()
    views: dict[str, Any] = {}

    def mock_view(callback_id: str) -> Any:
        def decorator(fn: Any) -> Any:
            views[callback_id] = fn
            return fn

        return decorator

    mock_app.view = mock_view
    register_slack_routes(
        app=mock_app,
        settings=settings,
        agent_graph=MagicMock(),
        bot_user_id="B123",
    )

    handler = views[MODAL_CV_CALLBACK_ID]
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    body = {
        "view": {
            "state": {
                "values": {
                    BLOCK_FILE_UPLOAD: {ACTION_FILE_INPUT: {"files": [{"id": "F1"}]}},
                    BLOCK_JD_FILE_UPLOAD: {ACTION_JD_FILE_INPUT: {"files": []}},
                    BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": ""}},
                }
            }
        }
    }
    await handler(ack=mock_ack, body=body, client=mock_client)
    mock_ack.assert_called_once_with(
        response_action="errors",
        errors={
            BLOCK_JD_FILE_UPLOAD: (
                "Upload a Job Description document or paste role criteria below."
            ),
            BLOCK_TEXT_INPUT: (
                "Paste role criteria here or upload a Job Description document above."
            ),
        },
    )


def test_validate_compliance_modal_submission_fails_when_both_empty() -> None:
    view = {
        "state": {
            "values": {
                BLOCK_FILE_UPLOAD: {ACTION_FILE_INPUT: {"files": []}},
                BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": ""}},
            }
        }
    }
    errors = validate_compliance_modal_submission(view)
    assert errors is not None
    assert BLOCK_FILE_UPLOAD in errors
    assert BLOCK_TEXT_INPUT in errors


def test_validate_compliance_modal_submission_succeeds_with_file() -> None:
    view = {
        "state": {
            "values": {
                BLOCK_FILE_UPLOAD: {ACTION_FILE_INPUT: {"files": [{"id": "F_BROCHURE"}]}},
                BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": ""}},
            }
        }
    }
    assert validate_compliance_modal_submission(view) is None


def test_validate_compliance_modal_submission_succeeds_with_text() -> None:
    view = {
        "state": {
            "values": {
                BLOCK_FILE_UPLOAD: {ACTION_FILE_INPUT: {"files": []}},
                BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": "https://kita.com.au/course"}},
            }
        }
    }
    assert validate_compliance_modal_submission(view) is None


@pytest.mark.asyncio
async def test_on_compliance_submit_rejects_empty_inputs() -> None:
    mock_app = MagicMock()
    settings = _create_test_settings()
    views: dict[str, Any] = {}

    def mock_view(callback_id: str) -> Any:
        def decorator(fn: Any) -> Any:
            views[callback_id] = fn
            return fn

        return decorator

    mock_app.view = mock_view
    register_slack_routes(
        app=mock_app,
        settings=settings,
        agent_graph=MagicMock(),
        bot_user_id="B123",
    )

    handler = views[MODAL_COMPLIANCE_CALLBACK_ID]
    mock_ack = AsyncMock()
    mock_client = AsyncMock()
    body = {
        "view": {
            "state": {
                "values": {
                    BLOCK_FILE_UPLOAD: {ACTION_FILE_INPUT: {"files": []}},
                    BLOCK_TEXT_INPUT: {ACTION_TEXT_INPUT: {"value": ""}},
                }
            }
        }
    }
    await handler(ack=mock_ack, body=body, client=mock_client)
    mock_ack.assert_called_once_with(
        response_action="errors",
        errors={
            BLOCK_FILE_UPLOAD: "Upload a document to audit or provide text/URL below.",
            BLOCK_TEXT_INPUT: "Enter text/URL here or upload a document above.",
        },
    )
