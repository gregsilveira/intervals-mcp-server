"""
Shared MCP instance module.

This module provides a shared FastMCP instance that can be imported by both
the server module and tool modules without creating cyclic imports.
"""

import os

from mcp.server.fastmcp import FastMCP  # pylint: disable=import-error
from mcp.server.transport_security import TransportSecuritySettings  # pylint: disable=import-error

from intervals_mcp_server.api.client import setup_api_client

# These are read here (not via FASTMCP_* env) because FastMCP.__init__ passes its
# defaults explicitly into pydantic Settings, which then take precedence over env vars.
# Reading them at construction is what makes remote (streamable-http) hosting work:
#   - host/port: bind correctly inside a container / on a host.
#   - stateless_http/json_response: required on serverless (Vercel Fluid, Lambda) where a
#     session's follow-up requests are not guaranteed to hit the same instance, so in-memory
#     session state would break. Both default off to preserve stdio/container behavior.
#   - transport_security: the MCP Streamable HTTP layer enforces DNS-rebinding protection
#     and rejects any Host it doesn't recognise with "421 Invalid Host header". Behind a
#     custom domain (e.g. app.example.com) that means every request 421s unless the host is
#     allow-listed. Set MCP_ALLOWED_HOSTS (comma-separated) to the public host(s), or set
#     MCP_DISABLE_DNS_REBINDING=true to turn the check off entirely (safe when the endpoint
#     is already IP-locked at the edge). Unset → library default (stdio/container unaffected).
def _env_bool(name: str) -> bool:
    return os.getenv(name, "").strip().lower() in ("1", "true", "yes", "on")


def _env_list(name: str) -> list[str]:
    return [item.strip() for item in os.getenv(name, "").split(",") if item.strip()]


_host = os.getenv("FASTMCP_HOST", "127.0.0.1")
_port = int(os.getenv("FASTMCP_PORT", "8000"))
_stateless = _env_bool("MCP_STATELESS_HTTP")
_json_response = _env_bool("MCP_JSON_RESPONSE")

_allowed_hosts = _env_list("MCP_ALLOWED_HOSTS")
_allowed_origins = _env_list("MCP_ALLOWED_ORIGINS")
_transport_security: TransportSecuritySettings | None = None
if _env_bool("MCP_DISABLE_DNS_REBINDING"):
    _transport_security = TransportSecuritySettings(enable_dns_rebinding_protection=False)
elif _allowed_hosts or _allowed_origins:
    _transport_security = TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=_allowed_hosts or ["*"],
        allowed_origins=_allowed_origins or ["*"],
    )

mcp: FastMCP = FastMCP(  # pylint: disable=invalid-name
    "intervals-icu",
    lifespan=setup_api_client,
    host=_host,
    port=_port,
    stateless_http=_stateless,
    json_response=_json_response,
    transport_security=_transport_security,
)
