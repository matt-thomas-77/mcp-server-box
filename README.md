# Box MCP Server

## Quick Start

### Clone the repository:

```sh
git clone https://github.com/box-community/mcp-server-box.git
cd mcp-server-box
```

### Optional but recommended `uv` installation for virtual environment and dependency management:

#### Homebrew (macOS)
```sh
brew install uv
```

#### WinGet (Windows)
```sh
winget install --id=astral-sh.uv  -e
```

#### On macOS and Linux
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```

#### On Windows
```sh
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

### Set up the virtual environment and install dependencies:

```sh
uv sync
```

### Set environment variables:
Set the following environment variables for Box authentication in a `.env` file or your system environment.

For comprehensive authentication configuration options, see the [Authentication Guide](docs/authentication.md).

#### Using OAuth2.0 with a Box App
```
BOX_CLIENT_ID = YOUR_CLIENT_ID
BOX_CLIENT_SECRET = YOUR_CLIENT_SECRET
BOX_REDIRECT_URL = http://localhost:8000/callback

# MCP Server Authentication (for HTTP transports)
BOX_MCP_SERVER_AUTH_TOKEN = YOUR_BOX_MCP_SERVER_AUTH_TOKEN
OAUTH_PROTECTED_RESOURCES_CONFIG_FILE = .oauth-protected-resource.json
```

> **Note**:
> - The `BOX_MCP_SERVER_AUTH_TOKEN` is used to authenticate the MCP client to the MCP server when using `--mcp-auth-type=token` (independent of Box authentication)

### Optional tool group filtering (server-side)
If your MCP client does not support tool-level toggles, you can filter tool groups at the server using environment variables.

**Disable specific groups** (blocklist) — all groups enabled except those listed:
```
TOOL_GROUPS_DISABLE = ai,doc_gen,shared_link
```

**Enable only specific groups** (allowlist) — only the listed groups are enabled, all others are disabled:
```
TOOL_GROUPS_ENABLE = search,file,folder
```

Supported group names:
`generic`, `search`, `ai`, `doc_gen`, `file_transfer`, `file`, `file_representation`, `folder`, `metadata`, `user`, `group`, `collaboration`, `web_link`, `shared_link`, `tasks`

Notes:
- Values are case-insensitive and comma-separated.
- Unknown group names are ignored with a warning.
- If neither variable is set, all tool groups are enabled.
- If both are set, `TOOL_GROUPS_ENABLE` takes precedence and `TOOL_GROUPS_DISABLE` is ignored.

### Optional individual tool filtering (server-side)
For finer-grained control, you can filter individual tools by their function name.

**Disable specific tools** (blocklist):
```
TOOLS_DISABLE = box_file_delete_tool,box_file_move_tool
```

**Enable only specific tools** (allowlist) — only the listed tools are registered, all others are disabled:
```
TOOLS_ENABLE = box_search_tool,box_ai_ask_file_single_tool,box_file_info_tool
```

Notes:
- Tool names are the function names (e.g. `box_search_tool`, `box_ai_ask_file_single_tool`).
- Values are case-insensitive and comma-separated.
- If both are set, `TOOLS_ENABLE` takes precedence and `TOOLS_DISABLE` is ignored.
- Individual tool filtering is applied after group filtering — a tool must pass both filters to be registered.


### Run the MCP server in STDIO mode:
```sh
uv run src/mcp_server_box.py
```

## Box Community MCP Server Tools

Below is a summary of the available tools:

| Tools available          | Description                                      |
|--------------------------|--------------------------------------------------|
| [box_tools_ai](docs/box_tools_ai.md) | AI-powered file and hub queries                  |
| [box_tools_collaboration](docs/box_tools_collaboration.md)  | Manage file/folder collaborations                |
| [box_tools_docgen](docs/box_tools_docgen.md)         | Document generation and template management      |
| [box_tools_files](docs/box_tools_files.md)          | File operations (read, upload, download)         |
| [box_tools_folders](docs/box_tools_folders.md)        | Folder operations (list, create, delete, update) |
| [box_tools_generic](docs/box_tools_generic.md)        | Generic Box API utilities                        |
| [box_tools_groups](docs/box_tools_groups.md)         | Group management and queries                     |
| [box_tools_metadata](docs/box_tools_metadata.md)       | Metadata template and instance management        |
| [box_tools_search](docs/box_tools_search.md)         | Search files and folders                         |
| [box_tools_shared_links](docs/box_tools_shared_links.md)   | Shared link management for files/folders/web-links|
| [box_tools_tasks](docs/box_tools_tasks.md)          | Task and task assignment management              |
| [box_tools_users](docs/box_tools_users.md)          | User management and queries                      |
| [box_tools_web_link](docs/box_tools_web_link.md)       | Web link creation and management                 |

## Environment Variables

All environment variables can be set in a `.env` file or your system environment.

### Server Configuration

| Variable | Description | Default | Example |
|----------|-------------|---------|---------|
| `HOST` | Server bind address | `localhost` | `0.0.0.0` |
| `PORT` | Server port | `8005` | `8005` |
| `LOG_LEVEL` | Logging level | `INFO` | `debug` |

### Box API Authentication

| Variable | Description | Required For | Example |
|----------|-------------|-------------|---------|
| `BOX_CLIENT_ID` | OAuth / CCG client ID | OAuth, CCG | `abc123def456` |
| `BOX_CLIENT_SECRET` | OAuth / CCG client secret | OAuth, CCG | `secret_xyz` |
| `BOX_REDIRECT_URL` | OAuth redirect URL | OAuth | `http://localhost:8000/callback` |
| `BOX_SUBJECT_TYPE` | CCG subject type | CCG | `enterprise` or `user` |
| `BOX_SUBJECT_ID` | CCG subject ID | CCG | `12345678` |
| `BOX_PUBLIC_KEY_ID` | JWT public key ID | JWT | `abcd1234` |
| `BOX_PRIVATE_KEY` | JWT private key contents | JWT | `-----BEGIN ENCRYPTED PRIVATE KEY-----...` |
| `BOX_PRIVATE_KEY_PASSPHRASE` | JWT private key passphrase | JWT | `mypassphrase` |
| `BOX_JWT_CONFIG_FILE` | Path to JWT config file | JWT (alternative) | `config/jwt_config.json` |

### MCP Server Authentication

| Variable | Description | Required For | Example |
|----------|-------------|-------------|---------|
| `BOX_MCP_SERVER_AUTH_TOKEN` | Bearer token for MCP server auth | `--mcp-auth-type token` | `my-secret-token-123` |
| `OAUTH_PROTECTED_RESOURCES_CONFIG_FILE` | Path to OAuth protected resources config | `--mcp-auth-type oauth` | `.oauth-protected-resource.json` |

### Tool Filtering

| Variable | Description | Example |
|----------|-------------|---------|
| `TOOL_GROUPS_DISABLE` | Comma-separated tool groups to disable (blocklist) | `ai,doc_gen,shared_link` |
| `TOOL_GROUPS_ENABLE` | Comma-separated tool groups to enable (allowlist) | `search,file,folder` |
| `TOOLS_DISABLE` | Comma-separated tool function names to disable | `box_file_delete_tool,box_file_move_tool` |
| `TOOLS_ENABLE` | Comma-separated tool function names to enable | `box_search_tool,box_ai_ask_file_single_tool` |

> **Note**: Allowlist (`*_ENABLE`) always takes precedence over blocklist (`*_DISABLE`). Individual tool filtering is applied after group filtering.

---

## Deploying to Azure Container Registry & Container Apps

### Building and Pushing the Docker Image to ACR

The Azure Container Registry environment is **`custommcps`**. Version your images with a tag when pushing updates.

```sh
# Log in to ACR
az acr login --name custommcps

# Build and tag the image with a version
# From root folder
docker build -t custommcps.azurecr.io/mcp-server-box:v1 .

# Push both tags
docker push custommcps.azurecr.io/mcp-server-box:v1

# Update Image in Azure Container Registry without Building Locally
az acr build --registry custommcps --image mcp-server-box:v1-http .  
```

### Updating the Azure Container App

The Container App endpoint is:
```
https://box-mcp-http.purpleplant-bb9db0cb.eastus2.azurecontainerapps.io/mcp
```

To update the container to use a new image version:

```sh
az containerapp update \
  --name box-mcp-http \
  --resource-group <your-resource-group> \
  --image custommcps.azurecr.io/mcp-server-box:v1.1.0
```

To verify the update:

```sh
az containerapp show \
  --name box-mcp-http \
  --resource-group <your-resource-group> \
  --query "properties.template.containers[0].image"
```

You can also update the container through the Azure Portal, by going to Container Apps --> 
box-mcp-http --> Application --> Containers

Once updated, the MCP server is accessible at the endpoint above. Clients (e.g., Claude Desktop in HTTP mode) should connect to:
```
https://box-mcp-http.purpleplant-bb9db0cb.eastus2.azurecontainerapps.io/mcp
```

---

## EQT - Box AI PDF & PowerPoint Parser

### Overview

The `box_ai_parse_pdf_powerpoint` tool is an EQT-specific addition that uses a **Box AI Agent** to extract full structured text content from PDF and PowerPoint files, including text embedded in images, charts, and diagrams.

This tool is designed for use cases such as parsing vision decks, investment memos, and other structured documents stored in Box.

### How It Works

1. The tool receives a **Box file ID** and an optional custom prompt
2. It calls the Box AI Agent (default agent ID: `66136138`) via the `box-ai-agents-toolkit`
3. The AI Agent processes the file slide-by-slide (PowerPoint) or page-by-page (PDF)
4. It returns structured text extraction with the following per-slide/page:
   - **Slide Number** - Metadata identifier
   - **Title** - Top-most prominent text element
   - **Text** - All visible text, preserved exactly as shown
   - **Tables** - Table content and structure
   - **Charts** - Chart type, title, axes, legend, and visible values
   - **Visuals** - Diagrams, org charts, images/screenshots, and icons with semantic meaning

### Key Behaviors

- Content is **never summarized or paraphrased** - all text is returned verbatim
- Each slide/page is treated **independently** - no merging across slides
- Decorative backgrounds and design elements are **ignored**
- Title detection is **position-based** (top-most text), not inferred from meaning

### Usage

The tool is registered under the `ai` tool group. To ensure it is available, make sure the `ai` group is not disabled:

```sh
# Enable only specific groups including ai
TOOL_GROUPS_ENABLE=ai,search,file

# Or enable just this specific tool
TOOLS_ENABLE=box_ai_pdf_powerpoint_parser_tool
```

### Connection to Box AI Agent

The tool connects to a **Box AI Agent** configured in the Box platform. The default agent ID (`66136138`) is an agent set up to handle document parsing with vision capabilities. To use a different agent, pass a custom `ai_agent_id` parameter when calling the tool.

Box AI Agents can be managed in the Box Admin Console under **Platform > AI Agents**.

---

## Box Community MCP Server Operations Details

### Command line interface parameters
To run the MCP server with specific configurations, you can use the following command line parameters:
```sh
uv run src/mcp_server_box.py --help
```
```
usage: mcp_server_box.py [-h] [--transport {stdio,sse,http}] [--host HOST] [--port PORT] [--mcp-auth-type {oauth,token,none}] [--box-auth-type {oauth,ccg,jwt,mcp_client}]

Box Community MCP Server

options:
  -h, --help            show this help message and exit
  --transport {stdio,sse,http}
                        Transport type (default: stdio)
  --host HOST           Host for SSE/HTTP transport (default: localhost)
  --port PORT           Port for SSE/HTTP transport (default: 8005)
  --mcp-auth-type {oauth,token,none}
                        Authentication type for MCP server (default: token)
  --box-auth-type {oauth,ccg,jwt,mcp_client}
                        Authentication type for Box API (default: oauth)
  ```

For detailed information about authentication types, configurations, and use cases, see the [Authentication Guide](docs/authentication.md).

### Claude Desktop Configuration

#### STDIO mode
Edit your `claude_desktop_config.json`:

```code ~/Library/Application\ Support/Claude/claude_desktop_config.json```

Add the configuration:
```json
{
    "mcpServers": {
        "mcp-server-box": {
            "command": "uv",
            "args": [
                "--directory",
                "/path/to/mcp-server-box",
                "run",
                "src/mcp_server_box.py"
            ]
        }
    }
}
```

Restart Claude if it is running.

#### HTTP Mode

Assuming your MCP server is running on `https://mcp.myserver.com/mcp`

1. Go to Claude -> Settings -> Connectors
2. Select `Add custom connector`
3. Configurations:
    1. Give it a name
    2. Enter the URL e.g. `https://mcp.myserver.com/mcp`
    3. Optionally enter the `client id` and `client secret`
4. Click add
5. Click connect. The OAuth flow should start. Complete the flow
6. Back in Claude, click Configure. You should see all the tools available.