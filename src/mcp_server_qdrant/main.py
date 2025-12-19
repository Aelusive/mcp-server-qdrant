import argparse


def main():
    """
    Main entry point for the mcp-server-qdrant script defined
    in pyproject.toml. It runs the MCP server with a specific transport
    protocol.
    """

    # Parse the command-line arguments to determine the transport protocol.
    parser = argparse.ArgumentParser(description="mcp-server-qdrant")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
    )
    args = parser.parse_args()

    # Import is done here to make sure environment variables are loaded
    # only after we make the changes.
    from mcp_server_qdrant.server import mcp

    # For HTTP transports, build an explicit ASGI app and run it with Uvicorn.
    # This makes it possible to expose discovery endpoints (/.well-known/...)
    # at the root, which is required by platforms like Smithery during scan.
    if args.transport in {"sse", "streamable-http"}:
        import os

        import uvicorn
        from starlette.responses import JSONResponse
        from starlette.routing import Route

        # Build the FastMCP ASGI app for the requested transport.
        # FastMCP's default endpoints are typically:
        # - SSE:            /sse
        # - Streamable HTTP: /mcp/
        app = mcp.http_app(transport=args.transport)

        def _server_card(_request):
            # Keep this lightweight and stable. Smithery mainly needs to learn
            # the transport endpoint path so it can POST to it.
            endpoint = "/mcp/" if args.transport == "streamable-http" else "/sse"
            return JSONResponse(
                {
                    "name": "mcp-server-qdrant",
                    "description": "MCP server for retrieving context from a Qdrant vector database",
                    "version": "0.8.1",
                    "capabilities": {
                        "tools": True,
                    },
                    "transport": {"type": args.transport, "endpoint": endpoint},
                    "authentication": {"required": False},
                }
            )

        def _mcp_config(_request):
            # Minimal Smithery discovery document. Some scanners look for this
            # file to determine whether config UI is needed.
            return JSONResponse({"mcpServers": {}})

        # Attach discovery endpoints at the root of the app.
        # We add them explicitly instead of relying on decorators because some
        # FastMCP runners mount sub-apps where /.well-known/* would not be visible.
        # Smithery expects the server card at /.well-known/mcp.json
        app.router.routes.insert(
            0, Route("/.well-known/mcp.json", _server_card, methods=["GET"])
        )
        # Also keep the standard MCP path for compatibility
        app.router.routes.insert(
            0, Route("/.well-known/mcp/server-card.json", _server_card, methods=["GET"])
        )
        app.router.routes.insert(
            0, Route("/.well-known/mcp-config", _mcp_config, methods=["GET"])
        )

        host = os.getenv("FASTMCP_HOST", "127.0.0.1")
        port_str = os.getenv("FASTMCP_PORT") or os.getenv("PORT") or "8000"
        port = int(port_str)

        uvicorn.run(app, host=host, port=port)
        return

    mcp.run(transport=args.transport)
