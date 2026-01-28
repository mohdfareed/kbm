#!/usr/bin/env bash
set -e

cd "$(dirname "$0")/.."
uv lock --upgrade
uv sync
