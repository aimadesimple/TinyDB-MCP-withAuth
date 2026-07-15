"""TinyDB MCP resource server authenticated by Auth0-issued access tokens."""

from __future__ import annotations

from typing import Any

from mcp.server.auth.settings import AuthSettings
from mcp.server.fastmcp import FastMCP
from tinydb import TinyDB

from auth0_config import Auth0Config
from auth0_token_verifier import Auth0TokenVerifier


config = Auth0Config.from_env()
mcp = FastMCP(
    "tinydb-remote-mcp-auth0",
    host=config.host,
    port=config.port,
    auth=AuthSettings(
        issuer_url=config.issuer_url,
        resource_server_url=config.server_url,
        required_scopes=[config.required_scope],
    ),
    token_verifier=Auth0TokenVerifier(config),
)

db = TinyDB("db.json")


@mcp.tool()
def insert_data(data: dict[str, Any]) -> str:
    """Insert one JSON document into TinyDB."""
    db.insert(data)
    return "Data inserted successfully."


@mcp.tool()
def get_all_data() -> list[dict[str, Any]]:
    """Return every document currently stored in TinyDB."""
    return db.all()


@mcp.tool()
def delete_all_data() -> str:
    """Delete every document from TinyDB."""
    db.truncate()
    return "Data deleted successfully."


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
