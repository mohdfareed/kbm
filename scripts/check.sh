#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
echo "==> Updating dependencies..."
uv sync --dev

echo
echo "==> Formatting..."
uv run ruff format src/

echo
echo "==> Linting..."
uv run ruff check src/ --fix

echo
echo "==> Type checking..."
uv run pyright src/

echo
echo "==> Running tests..."
uv run pytest

echo
echo "==> All checks passed!"
