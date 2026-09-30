from __future__ import annotations

from collections.abc import Sequence
from typing import Annotated, Any

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    """Canonical LangGraph state container for the Slack AI Agent."""

    messages: Annotated[Sequence[BaseMessage], add_messages]
    channel_id: str
    thread_ts: str
    user_id: str
    is_write_approved: bool
    pending_proposal_id: str | None
    latest_proposal_card: list[dict[str, Any]] | None
