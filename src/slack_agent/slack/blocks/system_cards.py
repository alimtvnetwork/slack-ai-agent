from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class StatusCardParams:
    """Parameters required to build a diagnostic status Block Kit card."""

    channel_id: str
    thread_ts: str
    message_count: int
    model_name: str
    storage_backend: str
    pending_proposals_count: int


def build_help_card() -> list[dict[str, Any]]:
    """Construct an interactive Block Kit help card detailing bot capabilities and commands."""
    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "🤖 KITA Slack AI Assistant & Analyst Guide",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Welcome! KITA provides specialized AI assistants equipped with native "
                    "slash commands, interactive upload modals, document parsing (including HTML), "
                    "CV candidate ranking, and RTO marketing compliance auditing."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*How to Interact in Slack:*\n"
                    "• *Native Slash Commands:* Type `/` commands directly in any message box "
                    "without needing to tag the bot.\n"
                    "• *Interactive Modals:* Commands like `/compliance-check` and `/cv-check` "
                    "pop up a native modal with drag & drop file upload fields.\n"
                    "• *Group Chat / Channels:* Tag the bot (`@AIAssistant` or `@kita-analyst`) "
                    "with queries or attached files.\n"
                    "• *Direct Chat (1-on-1 DM):* Chat directly with the bot or drop files "
                    "(no @ tag needed)."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Specialist Workflow Commands:*\n"
                    "• `/compliance-check` (or `@bot compliance-check`) — Audits marketing "
                    "materials against KITA's official 25-item Standards for RTOs checklist. "
                    "Supports *PDF, Word (.docx), Web Pages (.html, .htm), Plain Text (.txt)*, "
                    "or live website URLs. Delivers single-verdict executive callout, sleek table, "
                    "and remediation plan.\n"
                    "• `/cv-check` (or `@bot cv-check`) — Benchmarks candidate resumes against "
                    "Job Description (JD) mandatory tickets and role criteria. Supports *PDF, "
                    "DOCX, TXT* with ranked scoring breakdown."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Operational & Analysis Commands:*\n"
                    "• `/ai-summary` (or `/summary`, `/recap`) — Executive summary of recent "
                    "conversation (default 25 messages with thread replies expanded, or specify "
                    "custom count e.g. `/ai-summary 50` or a URL).\n"
                    "• `/ai-status` (or `@AIAssistant status`, `/info`) — Check thread memory, "
                    "active model, and stats.\n"
                    "• `/ai-reset` (or `@AIAssistant reset`, `/clear`) — Purge memory for active "
                    "thread.\n"
                    "• `/ai-help` (or `@AIAssistant help`, `/commands`) — Display this guide."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Core Autonomous Capabilities:*\n"
                    "• 📁 *File Analysis:* Multi-sheet Excel (`.xlsx`), PDF, Word (`.docx`), "
                    "HTML web pages (`.html`, `.htm`), CSV, and source code.\n"
                    "• 📊 *Data Charts:* Auto-generate high-res bar, line, and pie charts.\n"
                    "• 🌐 *Web Lookups:* Live web search and direct URL article extraction.\n"
                    "• ✍️ *Write Gate:* Review and approve formal document proposals "
                    "before generation."
                ),
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        "💡 _Tip: Type `/` in your Slack message composer to browse all native "
                        "slash commands and trigger interactive upload modals._"
                    ),
                }
            ],
        },
    ]


def build_status_card(params: StatusCardParams) -> list[dict[str, Any]]:
    """Construct a Block Kit card detailing thread diagnostics and memory state."""
    has_memory = params.message_count > 0
    memory_text = (
        f"*{params.message_count}* message(s) stored" if has_memory else "Clean (0 messages)"
    )

    has_proposals = params.pending_proposals_count > 0
    proposals_text = (
        f"*{params.pending_proposals_count}* awaiting review" if has_proposals else "None pending"
    )

    return [
        {
            "type": "header",
            "text": {
                "type": "plain_text",
                "text": "📊 Thread & System Diagnostics",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "fields": [
                {
                    "type": "mrkdwn",
                    "text": f"*Thread Context:*\n`{params.channel_id}:{params.thread_ts}`",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Memory State:*\n{memory_text}",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Active Model:*\n`{params.model_name}`",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Storage Backend:*\n`{params.storage_backend}`",
                },
                {
                    "type": "mrkdwn",
                    "text": f"*Write Gate Proposals:*\n{proposals_text}",
                },
            ],
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 _Send `@bot reset` to clear memory, or `@bot help` for guide._",
                }
            ],
        },
    ]
