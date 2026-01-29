"""Shared test fixtures."""

import os
from pathlib import Path
from typing import Generator

import pytest


@pytest.fixture
def tmp_data_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Provide a temporary data directory."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    yield data_dir


@pytest.fixture
def reset_settings() -> Generator[None, None, None]:
    """Reset global settings singleton after test."""
    import app.config as config_module

    original = config_module._settings
    yield
    config_module._settings = original


@pytest.fixture
def reset_chat_engine() -> Generator[None, None, None]:
    """Reset chat history engine singleton after test."""
    import engines.chat_history as engine_module

    original = engine_module._engine
    yield
    engine_module._engine = original


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Remove KBM env vars for clean config tests."""
    kbm_vars = {k: v for k, v in os.environ.items() if k.startswith("KBM_")}
    for k in kbm_vars:
        del os.environ[k]
    yield
    os.environ.update(kbm_vars)
