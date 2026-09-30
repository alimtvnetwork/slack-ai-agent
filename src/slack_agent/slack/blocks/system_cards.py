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
                "text": "🤖 Slack AI Assistant Guide",
                "emoji": True,
            },
        },
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "Welcome! I am your enterprise AI assistant equipped with file analysis, "
                    "autonomous web research, data visualization, and document drafting."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Core Capabilities:*\n"
                    "• 📁 *File Analysis:* Drop PDFs, Word docs (`.docx`), CSVs, or multi-sheet "
                    "Excel workbooks (`.xlsx`). I extract text and cross-reference sheets.\n"
                    "• 📊 *Data Charts:* Ask for comparisons or trends. I generate high-res "
                    "bar, line, and pie charts and upload them directly to the thread.\n"
                    "• 🌐 *Web Lookups:* Mention a topic for live web search or paste a URL "
                    "for deep article reading with clickable `<URL|Label>` citations.\n"
                    "• ✍️ *Human-in-the-Loop Write Gate:* Ask me to draft formal reports "
                    "(PDF, Word, CSV). You review and approve before files are published."
                ),
            },
        },
        {"type": "divider"},
        {
            "type": "section",
            "text": {
                "type": "mrkdwn",
                "text": (
                    "*Fast-Path Commands (Zero LLM Tokens):*\n"
                    "• `@bot help` — Display this capabilities guide.\n"
                    "• `@bot status` — Check memory turn count, active model, and proposals.\n"
                    "• `@bot reset` (or `clear`) — Instantly purge thread context memory."
                ),
            },
        },
        {
            "type": "context",
            "elements": [
                {
                    "type": "mrkdwn",
                    "text": "💡 _Tip: Commands execute instantly without consuming AI tokens._",
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
