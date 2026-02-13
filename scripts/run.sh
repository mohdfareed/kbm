#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."

# Use --rebuild/-r to force sync first
if [[ "$1" == "--rebuild" || "$1" == "-r" ]]; then
    shift
    uv sync --quiet
fi

# Use --install/-i to force install first
if [[ "$1" == "--install" || "$1" == "-i" ]]; then
    shift
    uv tool install . -e --force
    exit 0
fi

exec uv run --quiet kbm "$@"
