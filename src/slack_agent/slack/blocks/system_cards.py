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
                    "Welcome! KITA provides two specialized Slack AI assistants equipped with "
                    "document analysis, CV candidate ranking, ASQA compliance auditing, "
                    "and document drafting."
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
                    "• *Group Chat / Channels:* Tag the specific bot "
                    "(`@AIAssistant` or `@kita-analyst`).\n"
                    "• *Direct Chat (1-on-1 DM):* Type commands or queries directly "
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
                    "*AIAssistant Operational Commands (@AIAssistant only):*\n"
                    "• `/help` (or `@AIAssistant help`) — Display this capabilities guide.\n"
                    "• `/summary` (or `@AIAssistant summary`) — Summarize last 5 thread messages.\n"
                    "• `/status` (or `@AIAssistant status`) — Check memory, model, and stats.\n"
                    "• `/reset` (or `@AIAssistant reset`, `clear`) — Purge thread context memory."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*KITA-Analyst Specialist Commands (@kita-analyst only):*\n"
                    "• `/cv-check` (or `@kita-analyst cv-check`) — Attach Job Description "
                    "(PDF/DOCX/link) + Candidate CVs (PDF) to screen, score, and rank applicants.\n"
                    "• `/compliance-check` (or `@kita-analyst compliance-check`) — Provide "
                    "a brochure (PDF/DOC) or website URL to audit against KITA ASQA rules."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Core Autonomous Capabilities (Both Bots):*\n"
                    "• 📁 *File Analysis:* Ingest multi-sheet workbooks (`.xlsx`), PDFs, DOCX.\n"
                    "• 📊 *Data Charts:* Auto-generate high-res bar, line, and pie charts.\n"
                    "• 🌐 *Web Lookups:* Live web search and direct URL article reading.\n"
                    "• ✍️ *Write Gate:* Review & approve before formal documents are published."
                ),
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": (
                        "💡 _Tip: In DMs no @ mention is needed. "
                        "In channels always tag @AIAssistant or @kita-analyst._"
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
