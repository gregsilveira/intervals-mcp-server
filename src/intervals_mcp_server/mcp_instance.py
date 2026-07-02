"""
Shared MCP instance module.

This module provides a shared FastMCP instance that can be imported by both
the server module and tool modules without creating cyclic imports.
"""

import os

from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error

from intervals_mcp_server.api.client import setup_api_client

# These are read here (not via FASTMCP_* env) because FastMCP.__init__ passes its
# defaults explicitly into pydantic Settings, which then take precedence over env vars.
# Reading them at construction is what makes remote (streamable-http) hosting work:
#   - host/port: bind correctly inside a container / on a host.
#   - stateless_http/json_response: required on serverless (Vercel Fluid, Lambda) where a
#     session's follow-up requests are not guaranteed to hit the same instance, so in-memory
#     session state would break. Both default off to preserve stdio/container behavior.
def _env_bool(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


_host = os.getenv("FASTMCP_HOST", "127.0.0.1")
_port = int(os.getenv("FASTMCP_PORT", "8000"))
_stateless = _env_bool("MCP_STATELESS_HTTP")
_json_response = _env_bool("MCP_JSON_RESPONSE")

mcp: FastMCP = FastMCP(  # pylint: disable=invalid-name
    "intervals-icu",
    lifespan=setup_api_client,
    host=_host,
    port=_port,
    stateless_http=_stateless,
    json_response=_json_response,
)
