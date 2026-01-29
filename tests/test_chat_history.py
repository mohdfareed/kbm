"""Tests for chat history engine."""

from pathlib import Path

import pytest

from app.config import ChatHistoryConfig
from engines.chat_history import ChatHistoryEngine


@pytest.fixture
def engine(
    tmp_data_dir: Path, reset_settings: None, clean_env: None
) -> ChatHistoryEngine:
    """Create a chat history engine with temp directory."""
    import app.config as config_module
    from app.config import Settings, init_settings

    config_module._settings = None
    init_settings()
    # Override data dir for testing
    settings = Settings(
        data_dir=tmp_data_dir,
        chat_history=ChatHistoryConfig(data_dir="records"),
    )
    config_module._settings = settings
    return ChatHistoryEngine()


class TestInsert:
    """Insert operation tests."""

    @pytest.mark.asyncio
    async def test_insert_text(self, engine: ChatHistoryEngine) -> None:
        """Insert text content returns ID."""
        doc_id = await engine.insert("test content")
        assert doc_id is not None
        # Verify file was created
        record_path = engine.data_dir / f"{doc_id}.json"
        assert record_path.exists()

    @pytest.mark.asyncio
    async def test_insert_with_custom_id(self, engine: ChatHistoryEngine) -> None:
        """Insert with custom doc_id uses that ID."""
        doc_id = await engine.insert("test content", doc_id="custom-id")
        assert doc_id == "custom-id"
        assert (engine.data_dir / "custom-id.json").exists()

    @pytest.mark.asyncio
    async def test_insert_file(self, engine: ChatHistoryEngine, tmp_path: Path) -> None:
        """Insert file reads content from file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("file content")

        doc_id = await engine.insert_file(str(test_file))
        assert doc_id == "test"  # Uses filename stem

        record = engine._load_record(doc_id)
        assert record is not None
        assert record["content"] == "file content"

    @pytest.mark.asyncio
    async def test_insert_file_not_found(self, engine: ChatHistoryEngine) -> None:
        """Insert file raises for missing file."""
        with pytest.raises(FileNotFoundError):
            await engine.insert_file("/nonexistent/file.txt")


class TestQuery:
    """Query operation tests."""

    @pytest.mark.asyncio
    async def test_query_matches(self, engine: ChatHistoryEngine) -> None:
        """Query finds matching records."""
        await engine.insert("hello world", doc_id="doc1")
        await engine.insert("goodbye world", doc_id="doc2")

        result = await engine.query("hello")
        assert "doc1" in result
        assert "doc2" not in result

    @pytest.mark.asyncio
    async def test_query_case_insensitive(self, engine: ChatHistoryEngine) -> None:
        """Query is case-insensitive."""
        await engine.insert("Hello World", doc_id="doc1")
        result = await engine.query("hello")
        assert "doc1" in result

    @pytest.mark.asyncio
    async def test_query_no_matches(self, engine: ChatHistoryEngine) -> None:
        """Query returns message when no matches."""
        await engine.insert("hello world", doc_id="doc1")
        result = await engine.query("nonexistent")
        assert "No matching records" in result


class TestDelete:
    """Delete operation tests."""

    @pytest.mark.asyncio
    async def test_delete_existing(self, engine: ChatHistoryEngine) -> None:
        """Delete removes existing record."""
        await engine.insert("test", doc_id="to-delete")
        assert (engine.data_dir / "to-delete.json").exists()

        await engine.delete("to-delete")
        assert not (engine.data_dir / "to-delete.json").exists()

    @pytest.mark.asyncio
    async def test_delete_nonexistent(self, engine: ChatHistoryEngine) -> None:
        """Delete raises for missing record."""
        with pytest.raises(ValueError, match="not found"):
            await engine.delete("nonexistent")


class TestListRecords:
    """List records tests."""

    @pytest.mark.asyncio
    async def test_list_returns_summaries(self, engine: ChatHistoryEngine) -> None:
        """List returns record summaries."""
        await engine.insert("content one", doc_id="doc1")
        await engine.insert("content two", doc_id="doc2")

        records = await engine.list_records()
        assert len(records) == 2
        # Should have summary fields
        assert all("id" in r for r in records)
        assert all("content_preview" in r for r in records)

    @pytest.mark.asyncio
    async def test_list_pagination(self, engine: ChatHistoryEngine) -> None:
        """List respects limit and offset."""
        for i in range(5):
            await engine.insert(f"content {i}", doc_id=f"doc{i}")

        records = await engine.list_records(limit=2, offset=1)
        assert len(records) == 2


class TestInfo:
    """Info operation tests."""

    @pytest.mark.asyncio
    async def test_info_returns_metadata(self, engine: ChatHistoryEngine) -> None:
        """Info returns engine metadata."""
        await engine.insert("test", doc_id="doc1")

        info = await engine.info()
        assert info["engine"] == "chat-history"
        assert info["record_count"] == 1
        assert "data_dir" in info
