#!/usr/bin/env bash
set -e

if ! command -v uv &> /dev/null; then
    echo "error: uv is required" >&2
    exit 1
fi

cd "$(dirname "$0")/.."
uv sync
