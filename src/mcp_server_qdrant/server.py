from mcp_server_qdrant.mcp_server import QdrantMCPServer
from mcp_server_qdrant.settings import (
    EmbeddingProviderSettings,
    QdrantSettings,
    ToolSettings,
)

mcp = QdrantMCPServer(
    tool_settings=ToolSettings(),
    qdrant_settings=QdrantSettings(),
    embedding_provider_settings=EmbeddingProviderSettings(),
)


# Smithery (and other HTTP clients) expect MCP discovery metadata at well-known paths.
# Providing a server card prevents the platform from "guessing" the streamable-http endpoint.
try:
    from starlette.requests import Request
    from starlette.responses import JSONResponse

    @mcp.custom_route("/.well-known/mcp/server-card.json", methods=["GET"])
    async def mcp_server_card(_: Request) -> JSONResponse:
        # FastMCP's default streamable-http endpoint is typically /mcp/
        # (see FastMCP HTTP deployment docs). Trailing slash matters for some routers.
        return JSONResponse(
            {
                "$schema": "https://static.modelcontextprotocol.io/schemas/mcp-server-card/v1.json",
                "version": "1.0",
                # Keep protocolVersion optional; clients that need it can infer via MCP headers.
                "serverInfo": {
                    "name": "mcp-server-qdrant",
                    # The package version is available in pyproject.toml; avoid importing
                    # importlib.metadata at import-time for maximal compatibility.
                    "version": "0.8.1",
                },
                "transport": {"type": "streamable-http", "endpoint": "/mcp/"},
                # This server does not implement OAuth; Qdrant API keys are used only for the
                # downstream Qdrant connection, not for authenticating the MCP client.
                "authentication": {"required": False, "schemes": []},
            }
        )
except Exception:
    # If Starlette isn't available for some reason, skip the server card route.
    # (FastMCP bundles Starlette in normal installs.)
    pass
