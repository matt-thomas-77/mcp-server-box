FROM python:3.13-slim

WORKDIR /app

# Upgrade pip and install uv
# uv is the recommended tool for managing dependencies in this project
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

# Copy only dependency files first to leverage Docker cache
COPY pyproject.toml uv.lock README.md ./

# Copy source code
COPY src/ ./src/

# Install dependencies using uv
# This creates a virtual environment in .venv
# We run as root first to install system dependencies if any, then switch user
RUN uv sync

# Create a non-root user for security and change ownership
RUN useradd -m appuser && chown -R appuser:appuser /app

# Switch to the non-root user
USER appuser

# Expose port 8005 (default for the application)
EXPOSE 8005

# Set environment variables
ENV HOST=0.0.0.0
ENV PORT=8005
ENV BOX_SUBJECT_TYPE=enterprise
# Add the virtual environment to the PATH
ENV PATH="/app/.venv/bin:$PATH"

# --transport sse: Uses Server-Sent Events (requested streaming http mode)
# --mcp-auth-type token: Uses token for MCP authentication (default/secure for non-delegated auth)
# --box-auth-type ccg: Uses Box Client Credentials Grant (server-to-server auth)
CMD ["uv", "run", "src/mcp_server_box.py", "--transport", "sse", "--mcp-auth-type", "token", "--box-auth-type", "ccg", "--host", "0.0.0.0", "--port", "8005"]