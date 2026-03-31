"""MCP server configuration and initialization."""

import logging
from pathlib import Path

import tomli
from mcp.server.fastmcp import FastMCP

from config import AppConfig, ServerConfig, TransportType
from middleware import add_auth_middleware
from server_context import (
    box_lifespan_ccg,
    box_lifespan_jwt,
    box_lifespan_mcp_oauth,
    box_lifespan_oauth,
)
from tool_registry import register_all_tools
from tool_registry.ai_tools import register_ai_tools
from tool_registry.collaboration_tools import register_collaboration_tools
from tool_registry.doc_gen_tools import register_doc_gen_tools
from tool_registry.file_text_representation import register_file_representation_tools
from tool_registry.file_tools import register_file_tools
from tool_registry.file_transfer_tools import register_file_transfer_tools
from tool_registry.folder_tools import register_folder_tools
from tool_registry.generic_tools import register_generic_tools
from tool_registry.group_tools import register_group_tools
from tool_registry.metadata_tools import register_metadata_tools
from tool_registry.search_tools import register_search_tools
from tool_registry.shared_link_tools import register_shared_link_tools
from tool_registry.tasks_tools import register_tasks_tools
from tool_registry.user_tools import register_user_tools
from tool_registry.web_link_tools import register_web_link_tools

logger = logging.getLogger(__name__)


TOOL_GROUP_REGISTRARS = {
    "generic": register_generic_tools,
    "search": register_search_tools,
    "ai": register_ai_tools,
    "doc_gen": register_doc_gen_tools,
    "file_transfer": register_file_transfer_tools,
    "file": register_file_tools,
    "file_representation": register_file_representation_tools,
    "folder": register_folder_tools,
    "metadata": register_metadata_tools,
    "user": register_user_tools,
    "group": register_group_tools,
    "collaboration": register_collaboration_tools,
    "web_link": register_web_link_tools,
    "shared_link": register_shared_link_tools,
    "tasks": register_tasks_tools,
}


def get_version() -> str:
    """Read version from pyproject.toml."""
    try:
        pyproject_path = Path(__file__).parent.parent / "pyproject.toml"
        with open(pyproject_path, "rb") as f:
            pyproject_data = tomli.load(f)
        return pyproject_data.get("project", {}).get("version", "unknown")
    except Exception:
        return "unknown"


def create_mcp_server(
    app_config: AppConfig,
) -> FastMCP:
    """
    Create and configure the MCP server.

    Args:
        app_config: Complete application configuration

    Returns:
        FastMCP: Configured MCP server instance
    """

    # Select appropriate lifespan based on auth type
    if app_config.server.box_auth == "oauth":

        def lifespan(server):
            return box_lifespan_oauth(server, app_config.box_api)
    elif app_config.server.box_auth == "ccg":

        def lifespan(server):
            return box_lifespan_ccg(server, app_config.box_api)
    elif app_config.server.box_auth == "jwt":

        def lifespan(server):
            return box_lifespan_jwt(server, app_config.box_api)
    elif app_config.server.box_auth == "mcp_client":
        lifespan = box_lifespan_mcp_oauth
    else:
        raise ValueError(f"Unsupported Box auth type: {app_config.server.box_auth}")

    # Create MCP server with appropriate transport
    if app_config.server.transport == TransportType.STDIO.value:
        mcp = FastMCP(name=app_config.server.server_name, lifespan=lifespan)
    else:
        mcp = FastMCP(
            name=app_config.server.server_name,
            stateless_http=True,
            host=app_config.server.host,
            port=app_config.server.port,
            lifespan=lifespan,
        )
        # Add authentication middleware for HTTP/SSE transports
        add_auth_middleware(mcp, app_config)

    return mcp


def _get_enabled_registrars(
    disabled_groups: set[str],
    enabled_groups: set[str] | None = None,
):
    """Return registrars after filtering by enabled/disabled tool groups.

    If enabled_groups is set, only those groups are enabled (allowlist mode)
    and disabled_groups is ignored. Otherwise, disabled_groups is used as a
    blocklist.
    """
    valid_groups = set(TOOL_GROUP_REGISTRARS.keys())

    if enabled_groups:
        if disabled_groups:
            logger.warning(
                "Both TOOL_GROUPS_ENABLE and TOOL_GROUPS_DISABLE are set. "
                "TOOL_GROUPS_ENABLE takes precedence; TOOL_GROUPS_DISABLE is ignored.",
            )
        invalid_groups = sorted(enabled_groups - valid_groups)
        if invalid_groups:
            logger.warning(
                "Ignoring unknown tool group(s) in TOOL_GROUPS_ENABLE: %s",
                ", ".join(invalid_groups),
            )
        enabled_groups = enabled_groups & valid_groups
        return [
            registrar
            for group_name, registrar in TOOL_GROUP_REGISTRARS.items()
            if group_name in enabled_groups
        ]

    invalid_groups = sorted(disabled_groups - valid_groups)
    if invalid_groups:
        logger.warning(
            "Ignoring unknown tool group(s) in TOOL_GROUPS_DISABLE: %s",
            ", ".join(invalid_groups),
        )

    disabled_groups = disabled_groups & valid_groups
    return [
        registrar
        for group_name, registrar in TOOL_GROUP_REGISTRARS.items()
        if group_name not in disabled_groups
    ]


def register_tools(
    mcp: FastMCP,
    disabled_groups: set[str] | None = None,
    enabled_groups: set[str] | None = None,
    disabled_tools: set[str] | None = None,
    enabled_tools: set[str] | None = None,
) -> None:
    """Register all enabled tools with the MCP server."""
    disabled_groups = disabled_groups or set()
    enabled_groups = enabled_groups or set()
    register_all_tools(
        mcp,
        _get_enabled_registrars(disabled_groups, enabled_groups or None),
        enabled_tools=enabled_tools or None,
        disabled_tools=disabled_tools or None,
    )


def create_server_info_tool(
    mcp: FastMCP,
    config: ServerConfig,
) -> None:
    """Create and register the server info tool."""

    @mcp.tool()
    def mcp_server_info():
        """Returns information about the MCP server."""
        info = {
            "server_name": mcp.name,
            "version": get_version(),
            "transport": config.transport,
            "mcp auth": config.mcp_auth_type,
            "box auth": config.box_auth,
            "tool_groups_disable": sorted(config.tool_groups_disable),
            "tool_groups_enable": sorted(config.tool_groups_enable),
            "tools_disable": sorted(config.tools_disable),
            "tools_enable": sorted(config.tools_enable),
        }

        if config.transport != TransportType.STDIO.value:
            info["host"] = config.host
            info["port"] = str(config.port)

        return info
