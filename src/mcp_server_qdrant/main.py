import argparse
import os


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
    # Smithery requires CORS middleware and listening on PORT env variable.
    if args.transport in {"sse", "streamable-http"}:
        import uvicorn
        from starlette.applications import Starlette
        from starlette.middleware import Middleware
        from starlette.middleware.cors import CORSMiddleware
        from starlette.responses import JSONResponse
        from starlette.routing import Mount, Route

        # MCP Server Card endpoint - required by Smithery for server discovery
        async def server_card(request):
            return JSONResponse({
                "name": "mcp-server-qdrant",
                "version": "0.8.1",
                "description": "MCP server for retrieving context from a Qdrant vector database",
                "vendor": {
                    "name": "Qdrant"
                },
                "capabilities": {
                    "tools": {}
                }
            })

        # Get the FastMCP ASGI app for the /mcp endpoint
        mcp_app = mcp.http_app()

        # Create a wrapper Starlette app with discovery endpoints and the MCP app
        app = Starlette(
            routes=[
                # Discovery endpoint for Smithery
                Route("/.well-known/mcp.json", server_card, methods=["GET"]),
                # Mount the FastMCP app at /mcp
                Mount("/mcp", app=mcp_app.routes[0].app),
            ],
            middleware=[
                Middleware(
                    CORSMiddleware,
                    allow_origins=["*"],
                    allow_credentials=True,
                    allow_methods=["GET", "POST", "OPTIONS"],
                    allow_headers=["*"],
                    expose_headers=["mcp-session-id", "mcp-protocol-version"],
                    max_age=86400,
                ),
            ],
        )

        # Use PORT environment variable (Smithery sets this to 8081)
        host = os.getenv("FASTMCP_HOST", "0.0.0.0")
        port = int(os.environ.get("PORT", 8000))

        print(f"Starting MCP server on {host}:{port}")
        uvicorn.run(app, host=host, port=port)
        return

    # Default: STDIO transport for local development
    mcp.run(transport=args.transport)
