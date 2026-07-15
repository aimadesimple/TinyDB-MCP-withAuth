"""MCP adapter for Auth0's access-token verification client."""

from __future__ import annotations

from typing import Any

from auth0_api_python import ApiClient, ApiClientOptions
from auth0_api_python.errors import VerifyAccessTokenError
from mcp.server.auth.provider import AccessToken, TokenVerifier

from auth0_config import Auth0Config


class Auth0TokenVerifier(TokenVerifier):
    """Validate Auth0 JWTs and convert their claims to MCP access tokens."""

    def __init__(self, config: Auth0Config) -> None:
        self.client = ApiClient(ApiClientOptions(domain=config.domain, audience=config.audience))

    async def verify_token(self, token: str) -> AccessToken | None:
        """Return an MCP access token when Auth0 verifies the supplied JWT."""
        try:
            claims = await self.client.verify_access_token(token, required_claims=["sub"])
        except VerifyAccessTokenError:
            return None

        scopes = set(claims.get("scope", "").split())
        permissions = claims.get("permissions", [])
        if isinstance(permissions, list):
            scopes.update(permission for permission in permissions if isinstance(permission, str))

        client_id = claims.get("azp") or claims.get("client_id") or claims["sub"]
        additional_claims = {
            key: claims[key]
            for key in ("iss", "act")
            if claims.get(key) is not None
        }

        return AccessToken(
            token=token,
            client_id=str(client_id),
            scopes=sorted(scopes),
            expires_at=_integer_claim(claims, "exp"),
            subject=str(claims["sub"]),
            claims=additional_claims or None,
        )


def _integer_claim(claims: dict[str, Any], name: str) -> int | None:
    """Return a numeric JWT claim as an integer, if present."""
    value = claims.get(name)
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
