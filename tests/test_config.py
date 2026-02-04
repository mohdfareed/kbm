"""Tests for config loading."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from kbm.config import Engine, MemoryConfig, Transport


class TestConfigValidation:
    """Config validation tests."""

    def test_requires_name(self, tmp_path: Path) -> None:
        """Config requires a name field."""
        with pytest.raises(ValidationError):
            MemoryConfig()  # type: ignore[call-arg]

    def test_requires_file_path(self, tmp_path: Path) -> None:
        """Config requires file_path field."""
        with pytest.raises(ValidationError):
            MemoryConfig(name="test")  # type: ignore[call-arg]

    def test_unknown_engine_rejected(self, tmp_path: Path) -> None:
        """Config validation rejects unknown engine."""
        with pytest.raises(ValidationError):
            MemoryConfig(name="test", file_path=tmp_path, engine="invalid")  # type: ignore[arg-type]

    def test_unknown_transport_rejected(self, tmp_path: Path) -> None:
        """Config validation rejects unknown transport."""
        with pytest.raises(ValidationError):
            MemoryConfig(name="test", file_path=tmp_path, transport="invalid")  # type: ignore[arg-type]


class TestYamlLoading:
    """YAML config file loading tests."""

    def test_loads_name_from_yaml(self, tmp_path: Path) -> None:
        """Loads name field from YAML."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("name: my-memory\n")

        config = MemoryConfig.from_config(config_path)
        assert config.name == "my-memory"

    def test_loads_engine_from_yaml(self, tmp_path: Path) -> None:
        """Loads engine field from YAML."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("name: test\nengine: rag-anything\n")

        config = MemoryConfig.from_config(config_path)
        assert config.engine == Engine.RAG_ANYTHING

    def test_loads_transport_from_yaml(self, tmp_path: Path) -> None:
        """Loads transport field from YAML."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("name: test\ntransport: http\nport: 9000\n")

        config = MemoryConfig.from_config(config_path)
        assert config.transport == Transport.HTTP
        assert config.port == 9000

    def test_loads_nested_config(self, tmp_path: Path) -> None:
        """Loads nested engine config from YAML."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text(
            "name: test\nengine: rag-anything\nrag_anything:\n  embedding_dim: 1536\n"
        )

        config = MemoryConfig.from_config(config_path)
        assert config.rag_anything.embedding_dim == 1536

    def test_default_values_applied(self, tmp_path: Path) -> None:
        """Default values are applied when not in YAML."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("name: test\n")

        config = MemoryConfig.from_config(config_path)
        assert config.engine == Engine.CHAT_HISTORY  # default
        assert config.transport == Transport.STDIO  # default
        assert config.port == 8000  # default

    def test_missing_yaml_file_raises(self, tmp_path: Path) -> None:
        """Raises error for missing YAML file."""
        with pytest.raises(Exception):
            MemoryConfig.from_config(tmp_path / "nonexistent.yaml")

    def test_empty_yaml_file_raises(self, tmp_path: Path) -> None:
        """Empty YAML file still requires name."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("")

        with pytest.raises(ValidationError):
            MemoryConfig.from_config(config_path)

    def test_ignores_extra_fields(self, tmp_path: Path) -> None:
        """Extra fields in YAML are ignored."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("name: test\nunknown_field: value\n")

        config = MemoryConfig.from_config(config_path)
        assert config.name == "test"
        assert not hasattr(config, "unknown_field")


class TestEnvVarOverrides:
    """Environment variable override tests."""

    def test_env_overrides_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Environment variables override YAML values."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("name: from-yaml\nengine: chat-history\n")

        monkeypatch.setenv("KBM_ENGINE", "rag-anything")

        config = MemoryConfig.from_config(config_path)
        assert config.name == "from-yaml"  # from YAML
        assert config.engine == Engine.RAG_ANYTHING  # from env

    def test_nested_env_override(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Nested config can be overridden via env."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("name: test\n")

        monkeypatch.setenv("KBM_RAG_ANYTHING__EMBEDDING_DIM", "1536")

        config = MemoryConfig.from_config(config_path)
        assert config.rag_anything.embedding_dim == 1536

    def test_init_overrides_env_and_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Init kwargs have highest priority."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("name: from-yaml\nengine: rag-anything\n")
        monkeypatch.setenv("KBM_ENGINE", "rag-anything")

        config = MemoryConfig(
            name="from-init",
            file_path=config_path,
            engine=Engine.CHAT_HISTORY,
            _yaml_file=config_path,  # type: ignore[call-arg]
        )
        assert config.name == "from-init"  # from init (highest)
        assert config.engine == Engine.CHAT_HISTORY  # from init (highest)


class TestComputedPaths:
    """Computed path tests."""

    def test_data_path(self, tmp_config: Path, tmp_home: Path) -> None:
        """data_path is $KBM_HOME/data/<name>/."""
        config = MemoryConfig.from_config(tmp_config)
        assert config.data_path == tmp_home / "data" / "test-memory"


class TestSourcePriority:
    """Test config source priority: init > env > dotenv > yaml."""

    def test_priority_init_over_env_over_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Verify full priority chain."""
        config_path = tmp_path / "config.yaml"
        config_path.write_text("name: test\nport: 1000\nhost: yaml-host\n")

        monkeypatch.setenv("KBM_PORT", "2000")
        monkeypatch.setenv("KBM_HOST", "env-host")

        config = MemoryConfig(
            name="test",
            file_path=config_path,
            port=3000,  # init kwarg (highest priority)
            _yaml_file=config_path,  # type: ignore[call-arg]
        )

        assert config.port == 3000  # from init (highest)
        assert config.host == "env-host"  # from env (middle)
        # yaml values used only when not overridden
