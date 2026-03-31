FROM python:3.13-slim

WORKDIR /app

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir uv

COPY pyproject.toml uv.lock README.md ./

COPY src/ ./src/

# install dependencies and create a virtual environment using uv
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
# ENV OAUTH_PROTECTED_RESOURCES_CONFIG_FILE=.oauth-protected-resource.json
ENV LOG_LEVEL=debug
ENV PATH="/app/.venv/bin:$PATH"

# --transport http: Uses Streaming HTTP transport
CMD ["uv", "run", "src/mcp_server_box.py", "--transport", "http", "--mcp-auth-type", "token", "--box-auth-type", "ccg", "--host", "0.0.0.0", "--port", "8005"]