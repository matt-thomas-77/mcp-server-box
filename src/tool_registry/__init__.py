# src/tool_registry/__init__.py
import logging
from typing import Callable, List

from mcp.server.fastmcp import FastMCP

logger = logging.getLogger(__name__)

ToolRegistrar = Callable[[FastMCP], None]


def register_all_tools(
    mcp: FastMCP,
    registrars: List[ToolRegistrar],
    enabled_tools: set[str] | None = None,
    disabled_tools: set[str] | None = None,
):
    """Register tools from provided registrars, with optional per-tool filtering.

    Args:
        mcp: The FastMCP server instance.
        registrars: List of group registrar functions to call.
        enabled_tools: If set, only tools whose function name is in this set
            are registered (allowlist). Takes precedence over disabled_tools.
        disabled_tools: Tools whose function name is in this set are skipped
            (blocklist). Ignored if enabled_tools is set.
    """
    if enabled_tools and disabled_tools:
        logger.warning(
            "Both TOOLS_ENABLE and TOOLS_DISABLE are set. "
            "TOOLS_ENABLE takes precedence; TOOLS_DISABLE is ignored.",
        )

    if not enabled_tools and not disabled_tools:
        for registrar in registrars:
            registrar(mcp)
        return

    # Wrap mcp.tool() to intercept and filter individual tool registrations
    original_tool = mcp.tool

    def filtered_tool(*args, **kwargs):
        decorator = original_tool(*args, **kwargs)

        def wrapper(func):
            name = func.__name__
            if enabled_tools:
                if name not in enabled_tools:
                    logger.debug("Skipping tool %s (not in TOOLS_ENABLE)", name)
                    return func
            elif disabled_tools and name in disabled_tools:
                logger.debug("Skipping tool %s (in TOOLS_DISABLE)", name)
                return func
            return decorator(func)

        return wrapper

    mcp.tool = filtered_tool
    try:
        for registrar in registrars:
            registrar(mcp)
    finally:
        mcp.tool = original_tool
