from __future__ import annotations

from typing import Any


def is_bot_loopback(event: dict[str, Any], bot_user_id: str) -> bool:
    """Determine whether an incoming message was produced by the bot itself."""
    sender_id = event.get("user") or event.get("bot_id", "")
    if sender_id and sender_id == bot_user_id:
        return True

    subtype = event.get("subtype", "")
    if subtype == "bot_message":
        return True

    return "bot_id" in event
