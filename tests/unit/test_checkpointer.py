from pathlib import Path

import pytest

from slack_agent.agent.checkpointer import (
    create_checkpointer,
    get_async_checkpointer,
    make_thread_config,
)


def test_make_thread_config() -> None:
    config = make_thread_config("C12345", "1700000000.123456")
    assert config["configurable"]["thread_id"] == "C12345:1700000000.123456"


def test_create_checkpointer_sqlite() -> None:
    checkpointer = create_checkpointer(":memory:")
    assert checkpointer is not None


@pytest.mark.asyncio
async def test_get_async_checkpointer_memory() -> None:
    async with get_async_checkpointer(":memory:") as saver:
        assert saver is not None


@pytest.mark.asyncio
async def test_get_async_checkpointer_file(tmp_path: Path) -> None:
    db_file = tmp_path / "test_checkpoints.sqlite"
    async with get_async_checkpointer(str(db_file)) as saver:
        assert saver is not None
    assert db_file.exists()
