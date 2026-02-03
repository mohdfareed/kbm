"""Shared test fixtures."""

import os
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture(autouse=True)
def isolate_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Isolate tests from repo's .env file by changing to tmp_path."""
    monkeypatch.chdir(tmp_path)


@pytest.fixture
def tmp_config(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary .kbm.yaml config file."""
    config_path = tmp_path / ".kbm.yaml"
    config_path.write_text("name: test-memory\nengine: chat-history\n")
    yield config_path


@pytest.fixture
def tmp_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Set up temporary KBM_HOME directory."""
    from kbm.config import app_metadata

    # Clear cached properties so new env var takes effect
    for prop in ("home", "memories_path", "data_root"):
        app_metadata.__dict__.pop(prop, None)  # type: ignore[attr-defined]

    home = tmp_path / "kbm-home"
    home.mkdir()
    (home / "memories").mkdir()
    (home / "data").mkdir()
    monkeypatch.setenv("KBM_HOME", str(home))
    return home


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Remove KBM env vars for clean config tests."""
    env_vars = {k: v for k, v in os.environ.items() if k.startswith("KBM_")}
    for k in env_vars:
        del os.environ[k]
    yield
    os.environ.update(env_vars)
