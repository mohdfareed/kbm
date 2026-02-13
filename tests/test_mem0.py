"""Tests for Mem0 engine via MemoryTools."""

from collections.abc import AsyncGenerator
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastmcp.exceptions import ToolError

from kbm.config import Mem0Config
from kbm.engines.mem0 import Mem0Engine
from kbm.mcp.tools import MemoryTools
from kbm.store import CanonStore


@pytest.fixture
def mem0_config() -> Mem0Config:
    """Empty config dict - no real mem0 validation needed for mocked tests."""
    return Mem0Config(config={})


@pytest.fixture
def mock_async_memory() -> AsyncMock:
    """Create a mock AsyncMemory client."""
    mock = AsyncMock()
    mock.search.return_value = {"results": []}
    mock.add.return_value = {"results": [{"id": "mem0-id-1", "memory": "test"}]}
    mock.get_all.return_value = {"results": []}
    mock.delete.return_value = None
    return mock


def _make_tools(
    tmp_path: Path,
    mem0_config: Mem0Config,
    mock_async_memory: AsyncMock,
) -> tuple[MemoryTools, CanonStore]:
    """Helper to build MemoryTools + store with mocked AsyncMemory."""
    memory = MagicMock()
    memory.engine = "mem0"
    memory.mem0 = mem0_config

    data_path = tmp_path / "data"
    data_path.mkdir(parents=True, exist_ok=True)
    store = CanonStore(
        f"sqlite+aiosqlite:///{data_path / 'store.db'}",
        attachments_path=data_path / "attachments",
    )

    with (
        patch("kbm.engines.mem0.AsyncMemory", return_value=mock_async_memory),
        patch("kbm.engines.mem0.Mem0MemoryConfig"),
    ):
        eng = Mem0Engine(memory)
    return MemoryTools(eng, store), store


@pytest.fixture
async def tools(
    tmp_path: Path, mem0_config: Mem0Config, mock_async_memory: AsyncMock
) -> AsyncGenerator[MemoryTools, None]:
    """Create MemoryTools backed by a Mem0Engine with mocked AsyncMemory."""
    mt, store = _make_tools(tmp_path, mem0_config, mock_async_memory)
    yield mt
    await store.close()


class TestInsert:
    """Insert operation tests."""

    async def test_insert_text(
        self, tools: MemoryTools, mock_async_memory: AsyncMock
    ) -> None:
        """Insert text stores in canonical and calls Mem0 add."""
        result = await tools.insert("test content")
        assert result.id
        assert result.message == "Inserted into Mem0 memory"
        mock_async_memory.add.assert_awaited_once()

    async def test_insert_passes_canonical_id_as_metadata(
        self, tools: MemoryTools, mock_async_memory: AsyncMock
    ) -> None:
        """Insert passes canonical record ID in metadata."""
        result = await tools.insert("test content")
        call_kwargs = mock_async_memory.add.call_args
        assert call_kwargs.kwargs["metadata"]["canonical_id"] == result.id


class TestInsertFile:
    """Insert file (multimodal) operation tests."""

    async def test_insert_file_local(
        self, tools: MemoryTools, mock_async_memory: AsyncMock, tmp_path: Path
    ) -> None:
        """Insert file sends image message to Mem0."""
        test_file = tmp_path / "photo.png"
        test_file.write_bytes(b"\x89PNG\r\n\x1a\n" + b"\x00" * 100)
        result = await tools.insert_file(str(test_file))
        assert result.id

        # Verify Mem0 received a multimodal message
        call_kwargs = mock_async_memory.add.call_args
        messages = call_kwargs.kwargs["messages"]
        assert messages[0]["role"] == "user"
        content = messages[0]["content"]
        assert isinstance(content, list)
        assert content[0]["type"] == "text"
        assert content[1]["type"] == "image_url"
        assert content[1]["image_url"]["url"].startswith("data:image/png;base64,")

    async def test_insert_file_base64(
        self, tools: MemoryTools, mock_async_memory: AsyncMock
    ) -> None:
        """Insert file with base64 content passes data URL to Mem0."""
        import base64

        data = b"test file content"
        b64 = base64.b64encode(data).decode()
        result = await tools.insert_file("document.txt", content=b64)
        assert result.id

        call_kwargs = mock_async_memory.add.call_args
        messages = call_kwargs.kwargs["messages"]
        content = messages[0]["content"]
        assert content[1]["image_url"]["url"].startswith("data:text/plain;base64,")

    async def test_insert_file_not_found(self, tools: MemoryTools) -> None:
        """Insert file for missing file raises ToolError."""
        with pytest.raises(ToolError):
            await tools.insert_file("/nonexistent/file.txt")


class TestQuery:
    """Query operation tests."""

    async def test_query_empty(self, tools: MemoryTools) -> None:
        """Query returns empty results when Mem0 has none."""
        result = await tools.query("test")
        assert result.total == 0
        assert len(result.results) == 0

    async def test_query_returns_results(
        self, tools: MemoryTools, mock_async_memory: AsyncMock
    ) -> None:
        """Query returns Mem0 search results."""
        mock_async_memory.search.return_value = {
            "results": [
                {"id": "mem-1", "memory": "likes basketball", "score": 0.95},
                {"id": "mem-2", "memory": "name is Alex", "score": 0.80},
            ]
        }
        result = await tools.query("what do you know about me?")
        assert result.total == 2
        assert result.results[0].content == "likes basketball"
        assert result.results[0].score == 0.95
        assert result.results[1].id == "mem-2"

    async def test_query_passes_limit(
        self, tools: MemoryTools, mock_async_memory: AsyncMock
    ) -> None:
        """Query passes top_k as limit to Mem0."""
        await tools.query("test", top_k=5)
        call_kwargs = mock_async_memory.search.call_args
        assert call_kwargs.kwargs["limit"] == 5

    async def test_query_with_reranker(
        self, tmp_path: Path, mock_async_memory: AsyncMock
    ) -> None:
        """Query passes rerank=True when reranker is in config."""
        cfg = Mem0Config(
            config={
                "reranker": {
                    "provider": "sentence_transformer",
                    "config": {"model": "cross-encoder/ms-marco-MiniLM-L-6-v2"},
                },
            }
        )
        mt, store = _make_tools(tmp_path, cfg, mock_async_memory)
        try:
            await mt.query("test")
            call_kwargs = mock_async_memory.search.call_args
            assert call_kwargs.kwargs["rerank"] is True
        finally:
            await store.close()

    async def test_query_without_reranker(
        self, tools: MemoryTools, mock_async_memory: AsyncMock
    ) -> None:
        """Query does not pass rerank when no reranker configured."""
        await tools.query("test")
        call_kwargs = mock_async_memory.search.call_args
        assert "rerank" not in call_kwargs.kwargs


class TestDelete:
    """Delete operation tests."""

    async def test_delete_existing(
        self, tools: MemoryTools, mock_async_memory: AsyncMock
    ) -> None:
        """Delete removes from canonical and attempts Mem0 cleanup."""
        insert_result = await tools.insert("test")
        mock_async_memory.get_all.return_value = {
            "results": [
                {
                    "id": "mem0-id-1",
                    "metadata": {"canonical_id": insert_result.id},
                }
            ]
        }

        delete_result = await tools.delete(insert_result.id)
        assert delete_result.found is True
        mock_async_memory.delete.assert_awaited_once_with(memory_id="mem0-id-1")

    async def test_delete_nonexistent(self, tools: MemoryTools) -> None:
        """Delete returns found=False for missing record."""
        result = await tools.delete("nonexistent")
        assert result.found is False

    async def test_delete_mem0_failure_does_not_raise(
        self, tools: MemoryTools, mock_async_memory: AsyncMock
    ) -> None:
        """Mem0 cleanup failure is logged but does not raise."""
        insert_result = await tools.insert("test")
        mock_async_memory.get_all.side_effect = RuntimeError("connection lost")

        # Should not raise despite Mem0 error
        delete_result = await tools.delete(insert_result.id)
        assert delete_result.found is True


class TestListRecords:
    """List records tests."""

    async def test_list_returns_records(self, tools: MemoryTools) -> None:
        """List returns record information from canonical store."""
        await tools.insert("content one")
        await tools.insert("content two")

        result = await tools.list_records()
        assert len(result.records) == 2
        assert result.total == 2

    async def test_list_empty(self, tools: MemoryTools) -> None:
        """List returns empty when no records."""
        result = await tools.list_records()
        assert len(result.records) == 0
        assert result.total == 0


class TestInfo:
    """Info operation tests."""

    async def test_info_basic(self, tools: MemoryTools) -> None:
        """Info returns structured engine metadata."""
        info = await tools.info()
        assert info.engine == "mem0"

    async def test_info_with_all_features(
        self, tmp_path: Path, mock_async_memory: AsyncMock
    ) -> None:
        """Info reports enabled features from default config dict."""
        cfg = Mem0Config()  # defaults: vision + reranker + graph store
        mt, store = _make_tools(tmp_path, cfg, mock_async_memory)
        try:
            info = await mt.info()
            assert info.metadata["graph_store"] == "kuzu"
            assert "cross-encoder" in info.metadata["reranker"]
            assert "graph memory" in info.instructions
            assert "reranker" in info.instructions
            assert "multi-modal" in info.instructions
        finally:
            await store.close()

    async def test_info_features_disabled(
        self, tmp_path: Path, mock_async_memory: AsyncMock
    ) -> None:
        """Info with empty config has no feature metadata."""
        cfg = Mem0Config(config={})
        mt, store = _make_tools(tmp_path, cfg, mock_async_memory)
        try:
            info = await mt.info()
            assert "graph_store" not in info.metadata
            assert "reranker" not in info.metadata
        finally:
            await store.close()


class TestBuildClient:
    """Client configuration tests."""

    def test_empty_config_uses_bare_client(
        self, tmp_path: Path, mock_async_memory: AsyncMock
    ) -> None:
        """Empty config dict creates client with no custom config."""
        cfg = Mem0Config(config={})
        with (
            patch("kbm.engines.mem0.AsyncMemory", return_value=mock_async_memory) as m,
            patch("kbm.engines.mem0.Mem0MemoryConfig"),
        ):
            memory = MagicMock()
            memory.engine = "mem0"
            memory.mem0 = cfg
            Mem0Engine(memory)
            # Empty dict -> bare AsyncMemory()
            m.assert_called_once_with()

    def test_config_dict_passed_through(
        self, tmp_path: Path, mock_async_memory: AsyncMock
    ) -> None:
        """Non-empty config dict is passed to Mem0MemoryConfig."""
        cfg = Mem0Config(
            config={
                "llm": {"provider": "openai", "config": {"model": "gpt-4o"}},
                "graph_store": {
                    "provider": "neo4j",
                    "config": {"url": "bolt://x:7687"},
                },
            }
        )
        with (
            patch("kbm.engines.mem0.AsyncMemory", return_value=mock_async_memory),
            patch("kbm.engines.mem0.Mem0MemoryConfig") as mock_mem0_config,
        ):
            memory = MagicMock()
            memory.engine = "mem0"
            memory.mem0 = cfg
            Mem0Engine(memory)
            call_kwargs = mock_mem0_config.call_args.kwargs
            assert call_kwargs["llm"]["provider"] == "openai"
            assert call_kwargs["graph_store"]["provider"] == "neo4j"

    def test_null_values_stripped(
        self, tmp_path: Path, mock_async_memory: AsyncMock
    ) -> None:
        """Config keys set to None (null in YAML) are stripped."""
        cfg = Mem0Config(
            config={
                "llm": {"provider": "openai", "config": {}},
                "graph_store": None,
                "reranker": None,
            }
        )
        with (
            patch("kbm.engines.mem0.AsyncMemory", return_value=mock_async_memory),
            patch("kbm.engines.mem0.Mem0MemoryConfig") as mock_mem0_config,
        ):
            memory = MagicMock()
            memory.engine = "mem0"
            memory.mem0 = cfg
            Mem0Engine(memory)
            call_kwargs = mock_mem0_config.call_args.kwargs
            assert "graph_store" not in call_kwargs
            assert "reranker" not in call_kwargs
            assert "llm" in call_kwargs


class TestErrorConversion:
    """Error handling tests."""

    async def test_exception_becomes_tool_error(
        self, tools: MemoryTools, mock_async_memory: AsyncMock
    ) -> None:
        """Exception raised in Mem0 is converted to ToolError."""
        mock_async_memory.search.side_effect = ValueError("bad query")
        with pytest.raises(ToolError, match="bad query"):
            await tools.query("anything")
