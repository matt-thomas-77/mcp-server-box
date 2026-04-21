# CLAUDE.md - mcp-server-box

## Project Overview

MCP (Model Context Protocol) server that integrates Box cloud storage with Claude and other MCP-compatible clients. Forked from [box-community/mcp-server-box](https://github.com/box-community/mcp-server-box) with EQT-specific customizations, including a vision-based PDF/PowerPoint parser tool using Box AI Agents.

**Version:** 0.7.0  
**Python:** >=3.13  
**Package Manager:** uv

## Quick Reference

```bash
# Install dependencies
uv sync

# Run server (stdio, default)
uv run src/mcp_server_box.py

# Run server (HTTP with OAuth)
uv run src/mcp_server_box.py --transport http --mcp-auth-type oauth --host 0.0.0.0 --port 8005

# Run tests
uv run pytest

# Run tests with coverage
uv run pytest --cov

# Lint / format
uv run ruff check src/ tests/
uv run ruff format src/ tests/

# Docker build
docker build -t custommcps.azurecr.io/mcp-server-box:v1 .
```

## Architecture

### Entry Point & Server Startup

`src/mcp_server_box.py` is the entry point. Flow:
1. `AppConfig.from_env()` loads config from `.env` and environment variables
2. CLI args override env config (`--transport`, `--host`, `--port`, `--box-auth-type`, `--mcp-auth-type`)
3. Config validation (e.g., stdio forces `mcp_auth=none`, OAuth forces `box_auth=mcp_client`)
4. `create_mcp_server()` builds a `FastMCP` instance with the appropriate lifespan context manager
5. `register_tools()` registers all enabled tools (with group/individual filtering)
6. `mcp.run()` starts the server

### Source Layout

```
src/
  mcp_server_box.py      # CLI entry point, arg parsing
  config.py              # AppConfig, ServerConfig, enums (TransportType, BoxAuthType, McpAuthType)
  server.py              # FastMCP creation, tool registration, TOOL_GROUP_REGISTRARS dict
  server_context.py      # BoxContext dataclass, async lifespan managers (OAuth/CCG/JWT)
  middleware.py          # ASGI AuthMiddleware, Accept header normalization, CORS
  oauth_endpoints.py     # RFC 9728 OAuth protected resource metadata endpoints
  mcp_auth/
    auth_box_api.py      # Box client factories (get_oauth_client, get_ccg_client, get_jwt_client)
    auth_box.py          # Bearer token validation for Box OAuth
    auth_token.py        # MCP server token validation
  tool_registry/
    __init__.py          # register_all_tools() with per-tool filtering via mcp.tool() monkey-patch
    *.py                 # One file per tool group, each exports a register_*_tools(mcp) function
  tools/
    box_tools_*.py       # Tool implementations (async functions using asyncio.to_thread)
    box_tools_generic.py # get_box_client() helper, box_who_am_i, box_authorize_app_tool
    prompts.py           # PDF_POWERPOINT_PARSER_PROMPT (EQT custom)
```

### Tool Groups (defined in `server.py` TOOL_GROUP_REGISTRARS)

| Group | Registry File | Implementation |
|-------|--------------|----------------|
| generic | generic_tools.py | box_tools_generic.py |
| search | search_tools.py | box_tools_search.py |
| ai | ai_tools.py | box_tools_ai.py |
| doc_gen | doc_gen_tools.py | box_tools_docgen.py |
| file_transfer | file_transfer_tools.py | box_tools_file_transfer.py |
| file | file_tools.py | box_tools_file.py |
| file_representation | file_text_representation.py | box_tools_file_representation.py |
| folder | folder_tools.py | box_tools_folder.py |
| metadata | metadata_tools.py | box_tools_metadata.py |
| user | user_tools.py | box_tools_users.py |
| group | group_tools.py | box_tools_groups.py |
| collaboration | collaboration_tools.py | box_tools_collaboration.py |
| web_link | web_link_tools.py | box_tools_web_link.py |
| shared_link | shared_link_tools.py | box_tools_shared_links.py |
| tasks | tasks_tools.py | box_tools_tasks.py |

### Key Patterns

- **All tool functions are async.** Blocking Box SDK calls are wrapped with `asyncio.to_thread(lambda: ...)`.
- **BoxClient is obtained via `get_box_client(ctx)`** which casts the context's lifespan_context to `BoxContext` and calls `get_active_client()`.
- **Tool filtering** works at two levels: group-level (`TOOL_GROUPS_ENABLE`/`TOOL_GROUPS_DISABLE`) and individual-level (`TOOLS_ENABLE`/`TOOLS_DISABLE`). Enable lists take precedence over disable lists.
- **The tool registry pattern**: each `tool_registry/*.py` file defines a `register_*_tools(mcp)` function that decorates tool implementations with `@mcp.tool()`.

### Authentication

Two separate auth layers:

1. **MCP Auth** (client -> this server): `--mcp-auth-type` = `none` | `token` | `oauth`
   - `none`: No auth (required for stdio)
   - `token`: Bearer token validated against `BOX_MCP_SERVER_AUTH_TOKEN` env var
   - `oauth`: RFC 9728 OAuth 2.1 with Box as authorization server

2. **Box Auth** (this server -> Box API): `--box-auth-type` = `oauth` | `ccg` | `jwt` | `mcp_client`
   - `oauth`: Interactive OAuth flow (requires BOX_CLIENT_ID, BOX_CLIENT_SECRET)
   - `ccg`: Client Credentials Grant (requires BOX_CLIENT_ID, BOX_CLIENT_SECRET, BOX_SUBJECT_TYPE, BOX_SUBJECT_ID)
   - `jwt`: JWT auth (requires BOX_JWT_CONFIG_FILE or individual key env vars)
   - `mcp_client`: Passes through the MCP client's Bearer token to Box API

### Transport Modes

- `stdio` (default): Standard I/O, forces `mcp_auth=none`
- `sse`: Server-Sent Events over HTTP
- `http`: Streamable HTTP (mapped to `streamable-http` in FastMCP)

## Environment Variables

### Box API Auth
- `BOX_CLIENT_ID` / `BOX_CLIENT_SECRET` - OAuth/CCG credentials
- `BOX_SUBJECT_TYPE` / `BOX_SUBJECT_ID` - CCG subject (enterprise/user)
- `BOX_PUBLIC_KEY_ID` / `BOX_PRIVATE_KEY` / `BOX_PRIVATE_KEY_PASSPHRASE` - JWT keys
- `BOX_JWT_CONFIG_FILE` - JWT config file path (alternative to individual env vars)

### MCP Server Auth
- `BOX_MCP_SERVER_AUTH_TOKEN` - Bearer token for token-based MCP auth
- `OAUTH_PROTECTED_RESOURCES_CONFIG_FILE` - Path to OAuth metadata JSON (default: `.oauth-protected-resource.json`)

### Server Config
- `HOST` (default: localhost), `PORT` (default: 8005), `LOG_LEVEL` (default: INFO)

### Tool Filtering
- `TOOL_GROUPS_ENABLE` / `TOOL_GROUPS_DISABLE` - Comma-separated group names
- `TOOLS_ENABLE` / `TOOLS_DISABLE` - Comma-separated tool function names

## Testing

```bash
uv run pytest                    # Run all tests
uv run pytest tests/test_box_tools_ai.py  # Run specific test file
uv run pytest -k "test_search"   # Run tests matching pattern
```

- Tests use `FakeContext` / `FakeRequestContext` (in `tests/conftest.py`) to simulate the FastMCP context
- Auth fallback chain in fixtures: CCG -> JWT -> OAuth (prefers non-interactive)
- Tests require valid Box credentials in `.env` to actually hit the Box API
- pytest config in `pyproject.toml`: `pythonpath = [".", "src", "tests"]`

## Deployment

- **Dockerfile**: python:3.13-slim base, runs as non-root `appuser`, exposes port 8005
- **Default Docker CMD**: HTTP transport with OAuth auth
- **Registry**: `custommcps.azurecr.io/mcp-server-box`
- **Target**: Azure Container Apps

## EQT Customizations

- `box_ai_pdf_powerpoint_parser_tool` in `src/tools/box_tools_ai.py` - Vision-based content extraction from PDFs/PowerPoints using a custom Box AI Agent (default agent ID: `66136138`)
- `PDF_POWERPOINT_PARSER_PROMPT` in `src/tools/prompts.py` - Structured extraction prompt that transforms documents into normalized knowledge representations (not slide-by-slide extraction)

## Code Style

- Linter/formatter: ruff
- Type hints used throughout (Python 3.13+ syntax: `set[str]`, `list[dict]`, `X | None`)
- Naming: tools follow `box_<service>_<action>_tool` pattern
- Dataclasses for config, enums for constrained types
- Colored logging via colorlog (stderr)

## Files to Never Commit

`.env*`, `.auth.*`, `.oauth*`, `.jwt*`, credentials, secrets - all excluded via `.gitignore`
