"""Tests for configuration loading and validation."""

from pathlib import Path

import pytest

from app.config import (
    APP_NAME,
    CONFIG_FILES,
    Engines,
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
        assert settings.engine == Engines.chat_history
        assert settings.data_dir == tmp_data_dir

    def test_resolve_relative_path(self, tmp_data_dir: Path, clean_env: None) -> None:
        """Relative paths resolve against data_dir."""
        settings = Settings(data_dir=tmp_data_dir)
        resolved = settings.resolve_data_path("subdir")
        assert resolved == tmp_data_dir / "subdir"

    def test_resolve_absolute_path(self, tmp_data_dir: Path, clean_env: None) -> None:
        """Absolute paths remain unchanged."""
        settings = Settings(data_dir=tmp_data_dir)
        absolute = Path("/tmp/absolute")
        resolved = settings.resolve_data_path(str(absolute))
        assert resolved == absolute

    def test_data_dir_created(self, tmp_path: Path, clean_env: None) -> None:
        """Data directory is created on initialization."""
        new_dir = tmp_path / "new_data_dir"
        assert not new_dir.exists()
        Settings(data_dir=new_dir)
        assert new_dir.exists()

    def test_yaml_config_loading(self, tmp_path: Path, clean_env: None) -> None:
        """Settings load from YAML file."""
        config_file = tmp_path / "test.yaml"
        config_file.write_text(
            f"engine: rag-anything\ndata_dir: {tmp_path}\nserver_name: test-server\n"
        )
        settings = Settings.from_yaml(config_file)
        assert settings.engine == Engines.rag_anything
        assert settings.server_name == "test-server"

    def test_engine_specific_config(self, tmp_data_dir: Path, clean_env: None) -> None:
        """Engine-specific configs are accessible."""
        settings = Settings(data_dir=tmp_data_dir)
        assert settings.chat_history.data_dir == "chat-history"
        assert settings.rag_anything.llm_model == "gpt-4o-mini"


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
        # Change to empty dir so no config file is found
        monkeypatch.chdir(tmp_path)
        settings = init_settings()
        assert settings is not None
        assert get_settings() is settings

    def test_init_settings_with_yaml(
        self, tmp_path: Path, reset_settings: None, clean_env: None
    ) -> None:
        """init_settings loads specified YAML config."""
        set_settings(None)
        config_file = tmp_path / "config.yaml"
        config_file.write_text(f"server_name: custom-server\ndata_dir: {tmp_path}\n")
        settings = init_settings(config_file)
        assert settings.server_name == "custom-server"
        assert settings.config_file == config_file


class TestConfigFiles:
    """Config file discovery tests."""

    def test_config_files_priority(self) -> None:
        """Config files have correct priority order."""
        # CONFIG_FILES is a list with both string and Path entries
        assert isinstance(CONFIG_FILES, list)
        assert CONFIG_FILES[0] == ".env"
        # File-based configs
        assert f".{APP_NAME}" in CONFIG_FILES
        assert f".{APP_NAME}.env" in CONFIG_FILES
        assert f".{APP_NAME}.json" in CONFIG_FILES
        assert f".{APP_NAME}.yaml" in CONFIG_FILES
        assert f".{APP_NAME}.yml" in CONFIG_FILES
        # Directory-based configs (Path objects)
        assert any(isinstance(f, Path) for f in CONFIG_FILES)
