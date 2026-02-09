"""Tests for config loading and validation.

Unit tests for MemoryConfig parsing, validation, and source priority.
These test the config layer in isolation (no CLI, no filesystem side effects).
"""

from pathlib import Path

import pytest
from pydantic import ValidationError

from kbm.config import Engine, MemoryConfig, Transport
from kbm.config.settings import MemorySettings


def _settings(name: str = "test") -> MemorySettings:
    """Helper to build a MemorySettings for tests."""
    return MemorySettings(name=name)


class TestValidation:
    """Input validation - rejected inputs raise immediately."""

    def test_requires_settings(self) -> None:
        with pytest.raises(ValidationError):
            MemoryConfig()  # type: ignore[call-arg]

    def test_defaults_without_file(self) -> None:
        cfg = MemoryConfig(settings=_settings())
        assert cfg.engine == Engine.CHAT_HISTORY
        assert cfg.transport == Transport.STDIO

    def test_rejects_invalid_engine(self) -> None:
        with pytest.raises(ValidationError):
            MemoryConfig(settings=_settings(), engine="invalid")  # type: ignore[arg-type]

    def test_rejects_invalid_transport(self) -> None:
        with pytest.raises(ValidationError):
            MemoryConfig(settings=_settings(), transport="invalid")  # type: ignore[arg-type]

    def test_missing_file_raises(self, tmp_path: Path) -> None:
        with pytest.raises(FileNotFoundError):
            MemoryConfig._from_file(tmp_path / "nonexistent.yaml", settings=_settings())

    def test_empty_file_uses_defaults(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("")
        cfg = MemoryConfig._from_file(f, settings=_settings())
        assert cfg.engine == Engine.CHAT_HISTORY

    def test_extra_fields_ignored(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("unknown_field: value\n")
        cfg = MemoryConfig._from_file(f, settings=_settings())
        assert cfg.settings.name == "test"
        assert not hasattr(cfg, "unknown_field")


class TestYamlLoading:
    """Values read from YAML appear on the config object."""

    def test_engine(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("engine: rag-anything\n")
        cfg = MemoryConfig._from_file(f, settings=_settings())
        assert cfg.engine == Engine.RAG_ANYTHING

    def test_transport_and_port(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("transport: http\nport: 9000\n")
        cfg = MemoryConfig._from_file(f, settings=_settings())
        assert cfg.transport == Transport.HTTP
        assert cfg.port == 9000

    def test_nested_engine_config(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("engine: rag-anything\nrag_anything:\n  embedding_dim: 1536\n")
        cfg = MemoryConfig._from_file(f, settings=_settings())
        assert cfg.rag_anything.embedding_dim == 1536

    def test_defaults_applied(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("")
        cfg = MemoryConfig._from_file(f, settings=_settings())
        assert cfg.engine == Engine.CHAT_HISTORY
        assert cfg.transport == Transport.STDIO
        assert cfg.port == 8000


class TestSourcePriority:
    """Priority: init kwargs > env vars > .env file > YAML file."""

    def test_env_overrides_yaml(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("engine: chat-history\n")
        monkeypatch.setenv("KBM_ENGINE", "rag-anything")

        cfg = MemoryConfig._from_file(f, settings=_settings())
        assert cfg.engine == Engine.RAG_ANYTHING

    def test_init_overrides_env(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("instructions: yaml-inst\nengine: chat-history\n")
        monkeypatch.setenv("KBM_ENGINE", "rag-anything")

        cfg = MemoryConfig(
            settings=_settings(),
            instructions="from-init",
            _yaml_file=f,  # type: ignore[call-arg]
        )
        assert cfg.instructions == "from-init"  # init wins over yaml
        assert cfg.engine == Engine.RAG_ANYTHING  # env wins over yaml


class TestSerialization:
    """Round-trip: write config → read it back."""

    def test_dump_and_reload(self, tmp_path: Path) -> None:
        f = tmp_path / "config.yaml"
        f.write_text("engine: rag-anything\n")
        settings = _settings()
        original = MemoryConfig._from_file(f, settings=settings)

        out = tmp_path / "out.yaml"
        out.write_text(original.dump_yaml())
        reloaded = MemoryConfig._from_file(out, settings=settings)

        assert reloaded.engine == original.engine
        assert reloaded.settings.name == original.settings.name
        assert reloaded.engine == original.engine
        assert reloaded.transport == original.transport
