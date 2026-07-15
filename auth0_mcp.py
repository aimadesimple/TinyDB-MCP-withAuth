"""Auth0 protection for a FastMCP Streamable HTTP server."""

from __future__ import annotations

import contextlib
import logging
import os
from collections.abc import AsyncIterator, Callable
from dataclasses import dataclass
from typing import Any

from auth0_api_python import ApiClient, ApiClientOptions
from auth0_api_python.errors import VerifyAccessTokenError
from dotenv import load_dotenv
from mcp.server.auth.routes import build_resource_metadata_url, create_protected_resource_routes
from mcp.server.fastmcp import FastMCP
from starlette.applications import Starlette
from starlette.middleware import Middleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Mount
from starlette.types import ASGIApp

logger = logging.getLogger(__name__)


class AuthenticationRequired(Exception):
    """Raised when an MCP request has no usable Auth0 access token."""

    status_code = 401
    error_code = "invalid_token"

    def __init__(self, description: str = "Authentication required") -> None:
        self.description = description
        super().__init__(description)


class InsufficientScope(Exception):
    """Raised when a valid token does not grant access to this MCP."""

    status_code = 403
    error_code = "insufficient_scope"

    def __init__(self, description: str = "Missing required permission") -> None:
        self.description = description
        super().__init__(description)


@dataclass(frozen=True)
class Auth0Config:
    """Runtime configuration loaded from environment variables."""

    domain: str
    audience: str
    server_url: str
    required_scope: str
    port: int
    cors_origins: list[str]

    @classmethod
    def from_env(cls) -> "Auth0Config":
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

        audience = audience.strip()
        server_url = server_url.rstrip("/")
        if audience != server_url:
            raise RuntimeError("AUTH0_AUDIENCE must match MCP_SERVER_URL")

        return cls(
            domain=domain.strip(),
            audience=audience,
            server_url=server_url,
            required_scope=os.getenv("AUTH0_REQUIRED_SCOPE", "tinydb:tools"),
            port=int(os.getenv("PORT", "10000")),
            cors_origins=[origin.strip() for origin in os.getenv("CORS_ORIGINS", "*").split(",")],
        )


class Auth0Middleware(BaseHTTPMiddleware):
    """Validate Auth0 bearer tokens before requests reach the MCP server."""

    def __init__(self, app: ASGIApp, config: Auth0Config) -> None:
        super().__init__(app)
        self.client = ApiClient(ApiClientOptions(domain=config.domain, audience=config.audience))
        self.required_scope = config.required_scope

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        authorization = request.headers.get("authorization", "")
        if not authorization.lower().startswith("bearer "):
            raise AuthenticationRequired("A Bearer access token is required")

        try:
            token = await self.client.verify_access_token(
                authorization[7:].strip(), required_claims=["sub"]
            )
        except VerifyAccessTokenError as error:
            logger.info("Auth0 token validation failed: %s", error)
            raise AuthenticationRequired("Invalid or expired access token") from error

        scopes = set(token.get("scope", "").split())
        scopes.update(token.get("permissions", []))
        if self.required_scope not in scopes:
            raise InsufficientScope(f"Missing required permission: {self.required_scope}")

        request.state.auth = {"subject": token["sub"], "scopes": sorted(scopes)}
        return await call_next(request)


class Auth0Mcp:
    """Build a FastMCP application protected by an Auth0 API."""

    def __init__(self, name: str, config: Auth0Config) -> None:
        self.config = config
        self.mcp = FastMCP(
            name,
            host="0.0.0.0",
            port=config.port,
            stateless_http=True,
            json_response=True,
        )

    def app(self) -> ASGIApp:
        metadata_routes = create_protected_resource_routes(
            resource_url=self.config.audience,
            authorization_servers=[f"https://{self.config.domain}"],
            scopes_supported=[self.config.required_scope],
            resource_name=self.mcp.name,
        )

        @contextlib.asynccontextmanager
        async def lifespan(_: Starlette) -> AsyncIterator[None]:
            async with contextlib.AsyncExitStack() as stack:
                await stack.enter_async_context(self.mcp.session_manager.run())
                yield

        starlette_app = Starlette(
            routes=[
                *metadata_routes,
                Mount(
                    "/",
                    app=self.mcp.streamable_http_app(),
                    middleware=[Middleware(Auth0Middleware, config=self.config)],
                ),
            ],
            lifespan=lifespan,
            exception_handlers={
                AuthenticationRequired: self._auth_error,
                InsufficientScope: self._auth_error,
            },
        )
        return CORSMiddleware(
            starlette_app,
            allow_origins=self.config.cors_origins,
            allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
            allow_headers=["Authorization", "Content-Type", "Mcp-Session-Id", "MCP-Protocol-Version"],
            expose_headers=["Mcp-Session-Id"],
        )

    def _auth_error(self, _: Request, error: Exception) -> JSONResponse:
        assert isinstance(error, (AuthenticationRequired, InsufficientScope))
        headers = {"WWW-Authenticate": f'Bearer error="{error.error_code}"'}
        if error.status_code == 401:
            metadata_url = build_resource_metadata_url(self.config.audience)
            headers["WWW-Authenticate"] += f', resource_metadata="{metadata_url}"'
        return JSONResponse(
            {"error": error.error_code, "error_description": error.description},
            status_code=error.status_code,
            headers=headers,
        )
