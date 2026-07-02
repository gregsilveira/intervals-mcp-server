#!/bin/sh
set -e
# Honor a PaaS-injected $PORT if present; otherwise keep FASTMCP_PORT default (8000).
if [ -n "$PORT" ]; then
  export FASTMCP_PORT="$PORT"
fi
exec python src/intervals_mcp_server/server.py
