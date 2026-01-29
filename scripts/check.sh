#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
uv sync --quiet

echo "==> Formatting..."
uv run ruff format src/

echo "==> Linting..."
uv run ruff check src/ --fix

echo "==> Type checking..."
uv run pyright src/

echo "==> Running tests..."
uv run pytest

echo "==> All checks passed!"
