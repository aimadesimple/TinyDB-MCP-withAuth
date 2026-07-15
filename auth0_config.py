"""Configuration for the Auth0-protected TinyDB MCP server."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Auth0Config:
    """Load the Auth0 resource-server settings from environment variables."""

    domain: str
    audience: str
    server_url: str
    required_scope: str
    host: str
    port: int

    @classmethod
    def from_env(cls) -> "Auth0Config":
        """Load required settings and ensure the Auth0 audience is this MCP URL."""
        load_dotenv()
        domain = os.getenv("AUTH0_DOMAIN")
        audience = os.getenv("AUTH0_AUDIENCE")
        server_url = os.getenv("MCP_SERVER_URL")
        missing = [
            name
            for name, value in {
                "AUTH0_DOMAIN": domain,
                "AUTH0_AUDIENCE": audience,
                "MCP_SERVER_URL": server_url,
            }.items()
            if not value
        ]
        if missing:
            raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

        audience = audience.strip().rstrip("/")
        server_url = server_url.strip().rstrip("/")
        if audience != server_url:
            raise RuntimeError("AUTH0_AUDIENCE must match MCP_SERVER_URL")

        return cls(
            domain=domain.strip(),
            audience=audience,
            server_url=server_url,
            required_scope=os.getenv("AUTH0_REQUIRED_SCOPE", "tinydb:tools"),
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "10000")),
        )

    @property
    def issuer_url(self) -> str:
        """Return Auth0's issuer URL in its canonical trailing-slash form."""
        return f"https://{self.domain}/"
