FROM python:3.11-slim

WORKDIR /app

# Install uv for package management
RUN pip install --no-cache-dir uv

# Install the mcp-server-qdrant package
RUN uv pip install --system --no-cache-dir mcp-server-qdrant

# Expose the default port for SSE transport
EXPOSE 8000

# Set environment variables with defaults that can be overridden at runtime
ENV FASTMCP_HOST="0.0.0.0"
ENV QDRANT_URL=":memory:"
ENV COLLECTION_NAME="default-collection"
ENV EMBEDDING_MODEL="sentence-transformers/all-MiniLM-L6-v2"
ENV FASTEMBED_CACHE_PATH="/tmp/fastembed"
ENV UV_CACHE_DIR="/tmp/uv-cache"
ENV UV_TOOL_DIR="/tmp/uv-tools"

# Run the server with SSE transport
CMD ["uvx", "mcp-server-qdrant", "--transport", "streamable-http"]