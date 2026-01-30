#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

# Use --rebuild/-r to force sync first
if [[ "$1" == "--rebuild" || "$1" == "-r" ]]; then
    shift
    uv sync --quiet
fi

exec uv run kbm "$@"
