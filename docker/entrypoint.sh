#!/bin/sh
set -e

NAME="${1:-$(hostname)}" # Use hostname if no argument provided
[ $# -gt 0 ] && shift || true # shift first argument if provided

# Init memory if it doesn't exist
if ! kbm status "$NAME" > /dev/null 2>&1; then
    kbm init "$NAME"
fi

# Start server
exec kbm start "$NAME" -t http -p 8000 "$@"
