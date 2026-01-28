#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
uv sync --quiet
exec uv run kbm "$@"
