#!/bin/sh
set -e

# Default memory name
NAME="${1:-default}"
shift 2>/dev/null || true

# Init memory if it doesn't exist
if ! kbm status "$NAME" > /dev/null 2>&1; then
    kbm init "$NAME"
fi

# Start server
exec kbm start "$NAME" -t http -p 8000 "$@"
