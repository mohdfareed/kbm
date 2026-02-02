"""Tests for configuration loading and validation."""

from pathlib import Path

import pytest

from app.config import (
    APP_NAME,
    CONFIG_FILES,
    ChatHistoryConfig,
    Engine,
    Settings,
    get_settings,
    init_settings,
)
from app.config import reset_settings as set_settings


class TestSettings:
    """Settings model tests."""

    def test_default_settings(self, tmp_data_dir: Path, clean_env: None) -> None:
        """Default settings should be valid."""
        settings = Settings(data_dir=tmp_data_dir)
        # Will use CHAT_HISTORY unless overridden by config file
        assert settings.engine in [Engine.CHAT_HISTORY, Engine.RAG_ANYTHING]
        assert settings.data_dir == tmp_data_dir

    def test_engine_data_dir_relative(
        self, tmp_data_dir: Path, clean_env: None
    ) -> None:
        """Engine data dir resolves relative to data_dir when relative path."""
        settings = Settings(data_dir=tmp_data_dir, engine=Engine.CHAT_HISTORY)
        # chat_history.data_dir defaults to "chat-history" (relative)
        assert settings.engine_data_dir == tmp_data_dir / "chat-history"

    def test_engine_data_dir_absolute(
        self, tmp_data_dir: Path, clean_env: None
    ) -> None:
        """Engine data dir remains unchanged when absolute path."""
        absolute = Path("/tmp/absolute")
        settings = Settings(
            data_dir=tmp_data_dir,
            engine=Engine.CHAT_HISTORY,
            chat_history=ChatHistoryConfig(data_dir=str(absolute)),
        )
        assert settings.engine_data_dir == absolute

    def test_data_dir_created(self, tmp_path: Path, clean_env: None) -> None:
        """Data directory is created on initialization."""
        new_dir = tmp_path / "new_data_dir"
        assert not new_dir.exists()
        Settings(data_dir=new_dir)
        assert new_dir.exists()

    def test_engine_specific_config(self, tmp_data_dir: Path, clean_env: None) -> None:
        """Engine-specific configs are accessible."""
        settings = Settings(data_dir=tmp_data_dir)
        assert settings.chat_history.data_dir == "chat-history"
        assert settings.rag_anything.llm_model == "gpt-4o-mini"

    def test_instructions_configurable(
        self, tmp_data_dir: Path, clean_env: None
    ) -> None:
        """Server instructions can be customized."""
        custom_instructions = "Custom instructions for the model."
        settings = Settings(data_dir=tmp_data_dir, instructions=custom_instructions)
        assert settings.instructions == custom_instructions


class TestSettingsManagement:
    """Settings singleton management tests."""

    def test_get_settings_uninitialized(self, reset_settings: None) -> None:
        """get_settings raises before init."""
        set_settings(None)
        with pytest.raises(RuntimeError, match="not initialized"):
            get_settings()

    def test_init_settings_default(
        self,
        tmp_path: Path,
        reset_settings: None,
        clean_env: None,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """init_settings works without config file."""
        set_settings(None)
        monkeypatch.chdir(tmp_path)
        settings = init_settings()
        assert settings is not None
        assert get_settings() is settings

    def test_init_settings_with_json(
        self, tmp_path: Path, reset_settings: None, clean_env: None
    ) -> None:
        """init_settings loads specified JSON config."""
        set_settings(None)
        config_file = tmp_path / "config.json"
        config_file.write_text(
            f'{{"server_name": "custom-server", "data_dir": "{tmp_path}"}}'
        )
        settings = init_settings(config_file)
        assert settings.server_name == "custom-server"
        assert settings.config_file == config_file


class TestConfigFiles:
    """Config file discovery tests."""

    def test_config_files_priority(self) -> None:
        """Config files have correct priority order."""
        assert isinstance(CONFIG_FILES, list)
        assert CONFIG_FILES[0] == ".env"
        assert f".{APP_NAME}" in CONFIG_FILES
        assert f".{APP_NAME}.env" in CONFIG_FILES
        assert f".{APP_NAME}.json" in CONFIG_FILES
        assert f".{APP_NAME}.yaml" in CONFIG_FILES
        assert f".{APP_NAME}.yml" in CONFIG_FILES
