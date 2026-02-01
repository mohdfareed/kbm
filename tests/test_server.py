"""Tests for MCP server initialization."""

from pathlib import Path

import pytest

from app.config import Engines, Settings


@pytest.fixture
def configured_settings(
    tmp_data_dir: Path, reset_settings: None, clean_env: None
) -> None:
    """Set up settings for server tests."""
    import app.config as config_module

    config_module._settings = Settings(data_dir=tmp_data_dir)


class TestServerInit:
    """Server initialization tests."""

    def test_init_chat_history_engine(
        self, configured_settings: None, reset_settings: None
    ) -> None:
        """Server initializes with chat history engine."""
        import app.config as config_module

        assert config_module._settings is not None
        config_module._settings = Settings(
            engine=Engines.chat_history,
            data_dir=config_module._settings.data_dir,
        )

        from app.server import init_server

        mcp = init_server()
        assert mcp is not None
        assert mcp.name == config_module._settings.server_name

    def test_init_rag_anything_engine(
        self,
        configured_settings: None,
        reset_settings: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """Server initializes with RAG-Anything engine."""
        import app.config as config_module

        # RAG-Anything requires API key
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        assert config_module._settings is not None
        config_module._settings = Settings(
            engine=Engines.rag_anything,
            data_dir=config_module._settings.data_dir,
        )

        from app.server import init_server

        mcp = init_server()
        assert mcp is not None

    def test_init_unknown_engine(
        self, configured_settings: None, reset_settings: None
    ) -> None:
        """Settings validation rejects unknown engine."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Settings(engine="invalid")  # type: ignore[arg-type]
