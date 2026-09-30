from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver


def create_in_memory_checkpointer() -> BaseCheckpointSaver[Any]:
    """Initialize LangGraph in-memory state checkpointer (for testing)."""
    return MemorySaver()


def create_checkpointer(db_path: str = ":memory:") -> BaseCheckpointSaver[Any]:
    """Initialize LangGraph state checkpointer."""
    return MemorySaver()


@asynccontextmanager
async def get_async_checkpointer(
    db_path: str = "data/checkpoints.sqlite",
) -> AsyncIterator[BaseCheckpointSaver[Any]]:
    """Initialize persistent AsyncSqliteSaver context manager for LangGraph state."""
    if db_path != ":memory:":
        path = Path(db_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        async with AsyncSqliteSaver.from_conn_string(str(path)) as saver:
            await saver.setup()
            yield saver
    else:
        async with AsyncSqliteSaver.from_conn_string(":memory:") as saver:
            await saver.setup()
            yield saver


def make_thread_config(channel_id: str, thread_ts: str) -> dict[str, Any]:
    """
    Construct composite checkpointer thread configuration.

    Guarantees state is isolated per channel_id:thread_ts.
    """
    thread_key = f"{channel_id}:{thread_ts}"
    return {"configurable": {"thread_id": thread_key}}
