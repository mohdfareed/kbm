"""Tests for Mem0 engine."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from kbm.config import Mem0Config
from kbm.engines.base_engine import EngineBase
from kbm.engines.mem0 import Mem0Engine
from kbm.store import CanonStore


@pytest.fixture
def mem0_config() -> Mem0Config:
    return Mem0Config(user_id="test-user")


@pytest.fixture
def mock_async_memory() -> AsyncMock:
    """Create a mock AsyncMemory client."""
    mock = AsyncMock()
    mock.search.return_value = {"results": []}
    mock.add.return_value = {"results": [{"id": "mem0-id-1", "memory": "test"}]}
    mock.get_all.return_value = {"results": []}
    mock.delete.return_value = None
    return mock


@pytest.fixture
async def engine(
    tmp_path: Path, mem0_config: Mem0Config, mock_async_memory: AsyncMock
) -> AsyncGenerator[EngineBase, None]:
    """Create a Mem0 engine with mocked AsyncMemory client."""
    config = MagicMock()
    config.engine = "mem0"
    config.mem0 = mem0_config

    data_path = tmp_path / "data"
    attachments_path = data_path / "attachments"
    data_path.mkdir(parents=True, exist_ok=True)
    db_url = f"sqlite+aiosqlite:///{data_path / 'store.db'}"

    store = CanonStore(db_url, attachments_path=attachments_path)

    with patch("kbm.engines.mem0.AsyncMemory", return_value=mock_async_memory):
        eng = Mem0Engine(config, store)
    yield eng
    await store.close()


class TestInsert:
    """Insert operation tests."""

    async def test_insert_text(
        self, engine: EngineBase, mock_async_memory: AsyncMock
    ) -> None:
        """Insert text stores in canonical and calls Mem0 add."""
        result = await engine.insert("test content")
        assert result.id
        assert result.message == "Inserted into Mem0 memory"
        mock_async_memory.add.assert_awaited_once()

    async def test_insert_passes_user_id(
        self, engine: EngineBase, mock_async_memory: AsyncMock
    ) -> None:
        """Insert passes configured user_id to Mem0."""
        await engine.insert("test content")
        call_kwargs = mock_async_memory.add.call_args
        assert call_kwargs.kwargs["user_id"] == "test-user"

    async def test_insert_passes_canonical_id_as_metadata(
        self, engine: EngineBase, mock_async_memory: AsyncMock
    ) -> None:
        """Insert passes canonical record ID in metadata."""
        result = await engine.insert("test content")
        call_kwargs = mock_async_memory.add.call_args
        assert call_kwargs.kwargs["metadata"]["canonical_id"] == result.id


class TestQuery:
    """Query operation tests."""

    async def test_query_empty(self, engine: EngineBase) -> None:
        """Query returns empty results when Mem0 has none."""
        result = await engine.query("test")
        assert result.total == 0
        assert len(result.results) == 0

    async def test_query_returns_results(
        self, engine: EngineBase, mock_async_memory: AsyncMock
    ) -> None:
        """Query returns Mem0 search results."""
        mock_async_memory.search.return_value = {
            "results": [
                {"id": "mem-1", "memory": "likes basketball", "score": 0.95},
                {"id": "mem-2", "memory": "name is Alex", "score": 0.80},
            ]
        }
        result = await engine.query("what do you know about me?")
        assert result.total == 2
        assert result.results[0].content == "likes basketball"
        assert result.results[0].score == 0.95
        assert result.results[1].id == "mem-2"

    async def test_query_passes_limit(
        self, engine: EngineBase, mock_async_memory: AsyncMock
    ) -> None:
        """Query passes top_k as limit to Mem0."""
        await engine.query("test", top_k=5)
        call_kwargs = mock_async_memory.search.call_args
        assert call_kwargs.kwargs["limit"] == 5


class TestDelete:
    """Delete operation tests."""

    async def test_delete_existing(
        self, engine: EngineBase, mock_async_memory: AsyncMock
    ) -> None:
        """Delete removes from canonical and attempts Mem0 cleanup."""
        insert_result = await engine.insert("test")
        mock_async_memory.get_all.return_value = {
            "results": [
                {
                    "id": "mem0-id-1",
                    "metadata": {"canonical_id": insert_result.id},
                }
            ]
        }

        delete_result = await engine.delete(insert_result.id)
        assert delete_result.found is True
        mock_async_memory.delete.assert_awaited_once_with(memory_id="mem0-id-1")

    async def test_delete_nonexistent(self, engine: EngineBase) -> None:
        """Delete returns found=False for missing record."""
        result = await engine.delete("nonexistent")
        assert result.found is False

    async def test_delete_mem0_failure_does_not_raise(
        self, engine: EngineBase, mock_async_memory: AsyncMock
    ) -> None:
        """Mem0 cleanup failure is logged but doesn't raise."""
        insert_result = await engine.insert("test")
        mock_async_memory.get_all.side_effect = RuntimeError("connection lost")

        # Should not raise despite Mem0 error
        delete_result = await engine.delete(insert_result.id)
        assert delete_result.found is True


class TestListRecords:
    """List records tests."""

    async def test_list_returns_records(self, engine: EngineBase) -> None:
        """List returns record information from canonical store."""
        await engine.insert("content one")
        await engine.insert("content two")

        result = await engine.list_records()
        assert len(result.records) == 2
        assert result.total == 2

    async def test_list_empty(self, engine: EngineBase) -> None:
        """List returns empty when no records."""
        result = await engine.list_records()
        assert len(result.records) == 0
        assert result.total == 0


class TestInfo:
    """Info operation tests."""

    async def test_info_returns_metadata(self, engine: EngineBase) -> None:
        """Info returns structured engine metadata."""
        await engine.insert("test")

        info = await engine.info()
        assert info.engine == "mem0"
        assert info.records == 1
        assert info.metadata["user_id"] == "test-user"


class TestErrorConversion:
    """Error handling tests."""

    async def test_exception_becomes_tool_error(
        self, engine: EngineBase, mock_async_memory: AsyncMock
    ) -> None:
        """Exception raised in Mem0 is converted to ToolError."""
        mock_async_memory.search.side_effect = ValueError("bad query")
        with pytest.raises(ToolError, match="bad query"):
            await engine.query("anything")
