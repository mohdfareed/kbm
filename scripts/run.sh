#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
./scripts/bootstrap.sh
exec uv run kbm "$@"
