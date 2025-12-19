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
        from starlette.middleware.cors import CORSMiddleware

        # Build the FastMCP ASGI app for streamable HTTP transport.
        # This exposes the /mcp endpoint that Smithery expects.
        app = mcp.streamable_http_app()

        # IMPORTANT: Add CORS middleware for browser-based clients and Smithery
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["*"],
            expose_headers=["mcp-session-id", "mcp-protocol-version"],
            max_age=86400,
        )

        # Use PORT environment variable (Smithery sets this to 8081)
        host = os.getenv("FASTMCP_HOST", "0.0.0.0")
        port = int(os.environ.get("PORT", 8000))

        print(f"Starting MCP server on {host}:{port}")
        uvicorn.run(app, host=host, port=port)
        return

    # Default: STDIO transport for local development
    mcp.run(transport=args.transport)
