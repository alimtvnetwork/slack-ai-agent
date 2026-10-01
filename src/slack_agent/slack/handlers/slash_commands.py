from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from typing import Any

from slack_sdk.web.async_client import AsyncWebClient

from slack_agent.core.config import Settings
from slack_agent.core.logger import get_logger
from slack_agent.slack.handlers.messages import (
    PipelineExecutionContext,
    process_message_pipeline,
)

logger = get_logger(__name__)

MODAL_COMPLIANCE_CALLBACK_ID = "modal_compliance_check"
MODAL_CV_CALLBACK_ID = "modal_cv_check"

BLOCK_FILE_UPLOAD = "file_upload_block"
ACTION_FILE_INPUT = "files_input"

BLOCK_JD_FILE_UPLOAD = "jd_file_upload_block"
ACTION_JD_FILE_INPUT = "jd_file_input"

BLOCK_TEXT_INPUT = "text_input_block"
ACTION_TEXT_INPUT = "text_input"


@dataclass(frozen=True)
class SlashCommandContext:
    """Context container for native Slack slash command invocations."""

    command_name: str
    body: dict[str, Any]
    client: AsyncWebClient
    settings: Settings
    agent_graph: Any


@dataclass(frozen=True)
class ModalSubmissionContext:
    """Context container for Slack modal view submissions."""

    callback_id: str
    body: dict[str, Any]
    client: AsyncWebClient
    settings: Settings
    agent_graph: Any


def build_compliance_modal(
    channel_id: str,
    thread_ts: str,
    user_id: str,
    initial_text: str = "",
) -> dict[str, Any]:
    """Build Block Kit modal dialog for RTO marketing compliance audit."""
    metadata = json.dumps(
        {
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "user_id": user_id,
        }
    )
    notes_element: dict[str, Any] = {
        "type": "plain_text_input",
        "action_id": ACTION_TEXT_INPUT,
        "multiline": True,
        "placeholder": {
            "type": "plain_text",
            "text": "Optional notes, website URL, or specific clauses to audit...",
        },
    }
    if initial_text:
        notes_element["initial_value"] = initial_text[:3000]

    return {
        "type": "modal",
        "callback_id": MODAL_COMPLIANCE_CALLBACK_ID,
        "title": {"type": "plain_text", "text": "⚖️ Compliance Audit", "emoji": True},
        "submit": {"type": "plain_text", "text": "Start Audit", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "private_metadata": metadata,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "Upload marketing brochures, articles, web pages (.html), "
                        "or course overviews to audit against KITA's 25-item checklist."
                    ),
                },
            },
            {
                "type": "input",
                "block_id": BLOCK_FILE_UPLOAD,
                "label": {
                    "type": "plain_text",
                    "text": "Audit Document(s) (Optional)",
                    "emoji": True,
                },
                "element": {
                    "type": "file_input",
                    "action_id": ACTION_FILE_INPUT,
                    "filetypes": ["pdf", "docx", "txt", "csv", "xlsx", "html", "htm"],
                    "max_files": 10,
                },
                "optional": True,
            },
            {
                "type": "input",
                "block_id": BLOCK_TEXT_INPUT,
                "label": {
                    "type": "plain_text",
                    "text": "Marketing Text, URL, or Context (Optional)",
                    "emoji": True,
                },
                "element": notes_element,
                "optional": True,
            },
        ],
    }


def build_cv_modal(
    channel_id: str,
    thread_ts: str,
    user_id: str,
    initial_text: str = "",
) -> dict[str, Any]:
    """Build Block Kit modal dialog for candidate CV benchmarking."""
    metadata = json.dumps(
        {
            "channel_id": channel_id,
            "thread_ts": thread_ts,
            "user_id": user_id,
        }
    )
    jd_element: dict[str, Any] = {
        "type": "plain_text_input",
        "action_id": ACTION_TEXT_INPUT,
        "multiline": True,
        "placeholder": {
            "type": "plain_text",
            "text": "Paste Job Description (JD) or mandatory tickets/experience criteria...",
        },
    }
    if initial_text:
        jd_element["initial_value"] = initial_text[:3000]

    return {
        "type": "modal",
        "callback_id": MODAL_CV_CALLBACK_ID,
        "title": {"type": "plain_text", "text": "📋 CV Assessment", "emoji": True},
        "submit": {"type": "plain_text", "text": "Assess Candidates", "emoji": True},
        "close": {"type": "plain_text", "text": "Cancel", "emoji": True},
        "private_metadata": metadata,
        "blocks": [
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (
                        "Upload candidate resumes/CVs to benchmark and rank "
                        "against role criteria and mandatory tickets."
                    ),
                },
            },
            {
                "type": "input",
                "block_id": BLOCK_FILE_UPLOAD,
                "label": {
                    "type": "plain_text",
                    "text": "Candidate CV(s) / Resumes",
                    "emoji": True,
                },
                "element": {
                    "type": "file_input",
                    "action_id": ACTION_FILE_INPUT,
                    "filetypes": ["pdf", "docx", "txt"],
                    "max_files": 10,
                },
                "optional": False,
            },
            {
                "type": "input",
                "block_id": BLOCK_JD_FILE_UPLOAD,
                "label": {
                    "type": "plain_text",
                    "text": "Job Description Document (Optional PDF / DOCX)",
                    "emoji": True,
                },
                "element": {
                    "type": "file_input",
                    "action_id": ACTION_JD_FILE_INPUT,
                    "filetypes": ["pdf", "docx", "txt"],
                    "max_files": 1,
                },
                "optional": True,
            },
            {
                "type": "input",
                "block_id": BLOCK_TEXT_INPUT,
                "label": {
                    "type": "plain_text",
                    "text": "Or Paste Job Description Text / Criteria (Optional)",
                    "emoji": True,
                },
                "element": jd_element,
                "optional": True,
            },
        ],
    }


def validate_compliance_modal_submission(view: dict[str, Any]) -> dict[str, str] | None:
    """Validate that at least an audit document or text/URL was provided."""
    values = view.get("state", {}).get("values", {})
    files = list(values.get(BLOCK_FILE_UPLOAD, {}).get(ACTION_FILE_INPUT, {}).get("files", []))
    user_text = str(
        values.get(BLOCK_TEXT_INPUT, {}).get(ACTION_TEXT_INPUT, {}).get("value") or ""
    ).strip()

    has_content = bool(files) or bool(user_text)
    if has_content:
        return None

    return {
        BLOCK_FILE_UPLOAD: "Upload a document to audit or provide text/URL below.",
        BLOCK_TEXT_INPUT: "Enter text/URL here or upload a document above.",
    }


def validate_cv_modal_submission(view: dict[str, Any]) -> dict[str, str] | None:
    """Validate that at least a JD file or JD text was provided for CV assessment."""
    values = view.get("state", {}).get("values", {})
    jd_files = list(
        values.get(BLOCK_JD_FILE_UPLOAD, {}).get(ACTION_JD_FILE_INPUT, {}).get("files", [])
    )
    user_text = str(
        values.get(BLOCK_TEXT_INPUT, {}).get(ACTION_TEXT_INPUT, {}).get("value") or ""
    ).strip()

    has_jd_source = bool(jd_files) or bool(user_text)
    if has_jd_source:
        return None

    return {
        BLOCK_JD_FILE_UPLOAD: "Upload a Job Description document or paste role criteria below.",
        BLOCK_TEXT_INPUT: "Paste role criteria here or upload a Job Description document above.",
    }


def _extract_modal_submission(
    view: dict[str, Any],
) -> tuple[list[dict[str, Any]], str, dict[str, str]]:
    """Extract uploaded files, notes/criteria text, and metadata from modal view."""
    values = view.get("state", {}).get("values", {})
    files = list(values.get(BLOCK_FILE_UPLOAD, {}).get(ACTION_FILE_INPUT, {}).get("files", []))
    jd_files = list(
        values.get(BLOCK_JD_FILE_UPLOAD, {}).get(ACTION_JD_FILE_INPUT, {}).get("files", [])
    )
    user_text = str(
        values.get(BLOCK_TEXT_INPUT, {}).get(ACTION_TEXT_INPUT, {}).get("value") or ""
    ).strip()
    if jd_files:
        jd_name = str(jd_files[0].get("name", "Job Description"))
        jd_marker = (
            f"[BENCHMARK JD: Document '{jd_name}' is the target Job Description to rank against]"
        )
        user_text = f"{jd_marker}\n{user_text}".strip()

    all_files = files + jd_files
    raw_meta = view.get("private_metadata", "{}")
    meta = json.loads(raw_meta) if raw_meta else {}
    return all_files, user_text, meta


async def _fetch_file_download_url(
    file_id: str,
    client: AsyncWebClient,
) -> dict[str, str]:
    """Retrieve file metadata via Slack files.info API."""
    resp = await client.files_info(file=file_id)
    is_ok = bool(resp.get("ok"))
    if not is_ok:
        return {}
    f_data: dict[str, Any] = resp.get("file") or {}
    download_url = str(f_data.get("url_private_download") or f_data.get("url_private", ""))
    return {
        "url_private_download": download_url,
        "name": str(f_data.get("name", "document")),
        "filetype": str(f_data.get("filetype", "unknown")),
    }


async def _hydrate_file_urls(
    files: list[dict[str, Any]],
    client: AsyncWebClient,
) -> list[dict[str, Any]]:
    """Ensure all file dicts contain private download URLs."""
    hydrated: list[dict[str, Any]] = []
    for file_info in files:
        updated = dict(file_info)
        needs_lookup = not updated.get("url_private_download") and bool(updated.get("id"))
        if needs_lookup:
            meta = await _fetch_file_download_url(str(updated["id"]), client)
            updated.update(meta)
        hydrated.append(updated)
    return hydrated


def _build_command_context(
    ctx: SlashCommandContext,
    raw_text: str,
) -> PipelineExecutionContext:
    """Build PipelineExecutionContext from native Slack slash command payload."""
    raw_thread_ts = ctx.body.get("thread_ts")
    return PipelineExecutionContext(
        channel_id=str(ctx.body.get("channel_id", "")),
        thread_ts=str(raw_thread_ts or ""),
        user_id=str(ctx.body.get("user_id", "")),
        raw_text=raw_text,
        files=[],
        client=ctx.client,
        settings=ctx.settings,
        agent_graph=ctx.agent_graph,
        is_thread_reply=bool(raw_thread_ts),
    )


async def _try_open_command_modal(ctx: SlashCommandContext, cmd: str) -> bool:
    """Attempt opening a specialized Block Kit modal for compliance or CV check."""
    trigger_id = str(ctx.body.get("trigger_id", ""))
    if not trigger_id:
        return False

    channel_id = str(ctx.body.get("channel_id", ""))
    thread_ts = str(ctx.body.get("thread_ts") or "")
    user_id = str(ctx.body.get("user_id", ""))
    user_arg = str(ctx.body.get("text", "")).strip()

    if cmd in ("/compliance-check", "compliance-check"):
        modal = build_compliance_modal(channel_id, thread_ts, user_id, user_arg)
        await ctx.client.views_open(trigger_id=trigger_id, view=modal)
        return True

    if cmd in ("/cv-check", "cv-check"):
        modal = build_cv_modal(channel_id, thread_ts, user_id, user_arg)
        await ctx.client.views_open(trigger_id=trigger_id, view=modal)
        return True

    return False


async def handle_slash_command(ctx: SlashCommandContext) -> None:
    """Route native slash command to modal dialog or execution pipeline."""
    cmd = ctx.command_name.lower().strip()
    is_modal_opened = await _try_open_command_modal(ctx, cmd)
    if is_modal_opened:
        return

    user_arg = str(ctx.body.get("text", "")).strip()
    raw_text = f"{cmd} {user_arg}".strip()
    pipeline_ctx = _build_command_context(ctx, raw_text)
    asyncio.create_task(process_message_pipeline(pipeline_ctx))


async def handle_modal_submission(ctx: ModalSubmissionContext) -> None:
    """Handle modal view submission, hydrate file URLs, and launch processing."""
    view = ctx.body.get("view", {})
    raw_files, user_text, meta = _extract_modal_submission(view)
    files = await _hydrate_file_urls(raw_files, ctx.client)

    channel_id = str(meta.get("channel_id", ""))
    thread_ts = str(meta.get("thread_ts", ""))
    user_id = str(meta.get("user_id", ""))

    is_compliance = ctx.callback_id == MODAL_COMPLIANCE_CALLBACK_ID
    prefix = "/compliance-check" if is_compliance else "/cv-check"
    raw_text = f"{prefix} {user_text}".strip()

    pipeline_ctx = PipelineExecutionContext(
        channel_id=channel_id,
        thread_ts=thread_ts,
        user_id=user_id,
        raw_text=raw_text,
        files=files,
        client=ctx.client,
        settings=ctx.settings,
        agent_graph=ctx.agent_graph,
        is_thread_reply=bool(thread_ts),
    )
    asyncio.create_task(process_message_pipeline(pipeline_ctx))
