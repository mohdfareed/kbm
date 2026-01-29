#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

if [[ "$1" == "--rebuild" || "$1" == "-r" ]]; then
    shift
    uv sync --quiet
    exec uv run kbm "$@"
else
    exec ./.venv/bin/kbm "$@"
fi
