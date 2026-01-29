#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
uv sync --quiet

echo "==> Formatting..."
uv run ruff format src/

echo "==> Linting..."
uv run ruff check src/ --fix

echo "==> Running tests..."
uv run pytest -q

echo "==> All checks passed!"
