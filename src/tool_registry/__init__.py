# src/tool_registry/__init__.py
import functools
import inspect
import logging
from typing import Callable, List

from mcp.server.fastmcp import FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from redaction import redact_exception

logger = logging.getLogger(__name__)

ToolRegistrar = Callable[[FastMCP], None]


def redact_tool_errors(func: Callable) -> Callable:
    """Wrap a tool so credentials cannot leak through its error message.

    Box SDK errors quote the failed HTTP request, which for a token request
    contains the client secret. FastMCP passes any exception message straight
    to the MCP client, so the message is scrubbed here and the original
    exception is dropped (``from None``) to keep it out of the logs too.
    """

    if inspect.iscoroutinefunction(func):

        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as exc:
                message = redact_exception(exc)
                logger.debug("Tool %s failed: %s", func.__name__, message)
                raise ToolError(message) from None

        return async_wrapper

    @functools.wraps(func)
    def sync_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as exc:
            message = redact_exception(exc)
            logger.debug("Tool %s failed: %s", func.__name__, message)
            raise ToolError(message) from None

    return sync_wrapper


def register_all_tools(
    mcp: FastMCP,
    registrars: List[ToolRegistrar],
    enabled_tools: set[str] | None = None,
    disabled_tools: set[str] | None = None,
):
    """Register tools from provided registrars, with optional per-tool filtering.

    Every registered tool is wrapped so that error messages are redacted before
    they reach the client.

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

    # Wrap mcp.tool() to filter individual tool registrations and to redact
    # errors raised by the tools that do get registered.
    original_tool = mcp.tool
    had_own_tool_attribute = "tool" in vars(mcp)

    def wrapped_tool(*args, **kwargs):
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

            decorator(redact_tool_errors(func))
            return func

        return wrapper

    mcp.tool = wrapped_tool
    try:
        for registrar in registrars:
            registrar(mcp)
    finally:
        if had_own_tool_attribute:
            mcp.tool = original_tool
        else:
            # Drop the patch entirely rather than leaving a bound method
            # shadowing the class attribute.
            del mcp.tool
