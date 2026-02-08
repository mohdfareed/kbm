"""Tests for config loading and validation.

Unit tests for MemoryConfig parsing, validation, and source priority.
These test the config layer in isolation (no CLI, no filesystem side effects).
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from kbm.config import Engine, MemoryConfig, Transport


class TestValidation:
    """Input validation - rejected inputs raise immediately."""

    def test_requires_name(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            MemoryConfig()  # type: ignore[call-arg]

    def test_requires_file_path(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            MemoryConfig(name="test")  # type: ignore[call-arg]

    def test_rejects_invalid_engine(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            MemoryConfig(name="test", file_path=tmp_path, engine="invalid")  # type: ignore[arg-type]

    def test_rejects_invalid_transport(self, tmp_path: Path) -> None:
        with pytest.raises(ValidationError):
            MemoryConfig(name="test", file_path=tmp_path, transport="invalid")  # type: ignore[arg-type]

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            MemoryConfig.from_file(tmp_path / "nonexistent.yaml")

    def test_empty_file_raises(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("")
        with pytest.raises(ValidationError):
            MemoryConfig.from_file(f)

    def test_extra_fields_ignored(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("name: test\nunknown_field: value\n")
        config = MemoryConfig.from_file(f)
        assert config.name == "test"
        assert not hasattr(config, "unknown_field")


class TestYamlLoading:
    """Values read from YAML appear on the config object."""

    def test_name(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("name: my-memory\n")
        assert MemoryConfig.from_file(f).name == "my-memory"

    def test_engine(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("name: test\nengine: rag-anything\n")
        assert MemoryConfig.from_file(f).engine == Engine.RAG_ANYTHING

    def test_transport_and_port(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("name: test\ntransport: http\nport: 9000\n")
        cfg = MemoryConfig.from_file(f)
        assert cfg.transport == Transport.HTTP
        assert cfg.port == 9000

    def test_nested_engine_config(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text(
            "name: test\nengine: rag-anything\nrag_anything:\n  embedding_dim: 1536\n"
        )
        cfg = MemoryConfig.from_file(f)
        assert cfg.rag_anything.embedding_dim == 1536

    def test_defaults_applied(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("name: test\n")
        cfg = MemoryConfig.from_file(f)
        assert cfg.engine == Engine.CHAT_HISTORY
        assert cfg.transport == Transport.STDIO
        assert cfg.port == 8000


class TestSourcePriority:
    """Priority: init kwargs > env vars > .env file > YAML file."""

    def test_env_overrides_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("name: from-yaml\n")
        monkeypatch.setenv("KBM_NAME", "from-env")

        assert MemoryConfig.from_file(f).name == "from-env"

    def test_init_overrides_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("name: from-yaml\ninstructions: yaml-inst\n")
        monkeypatch.setenv("KBM_NAME", "from-env")
        monkeypatch.setenv("KBM_INSTRUCTIONS", "env-inst")

        cfg = MemoryConfig(
            name="from-init",
            file_path=f,
            _yaml_file=f,  # type: ignore[call-arg]
        )
        assert cfg.name == "from-init"  # init wins
        assert cfg.instructions == "env-inst"  # env wins over yaml


class TestSerialization:
    """Round-trip: write config → read it back."""

    def test_dump_and_reload(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("name: test\n")
        original = MemoryConfig.from_file(f)

        out = tmp_path / "out.yaml"
        out.write_text(original.dump_yaml())
        reloaded = MemoryConfig.from_file(out)

        assert reloaded.name == original.name
        assert reloaded.engine == original.engine
        assert reloaded.transport == original.transport
