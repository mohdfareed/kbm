#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
mkdir -p docs
uv run typer kbm utils docs > docs/cli.md
echo "CLI docs written to docs/cli.md"
