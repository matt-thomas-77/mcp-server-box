from mcp.server.fastmcp import FastMCP

from tool_registry import register_all_tools


def _make_registrar(*tool_names):
    """Create a registrar that registers dummy tools with the given names."""
    tools = []
    for name in tool_names:
        def tool_func():
            pass
        tool_func.__name__ = name
        tools.append(tool_func)

    def registrar(mcp: FastMCP):
        for func in tools:
            mcp.tool()(func)

    return registrar


def _get_registered_tool_names(mcp: FastMCP) -> set[str]:
    """Get the set of tool names registered on the MCP server."""
    return set(mcp._tool_manager._tools.keys())


def test_no_filtering_registers_all_tools():
    mcp = FastMCP("test")
    registrars = [_make_registrar("tool_a", "tool_b", "tool_c")]

    register_all_tools(mcp, registrars)

    assert _get_registered_tool_names(mcp) == {"tool_a", "tool_b", "tool_c"}


def test_tools_enable_allowlist():
    mcp = FastMCP("test")
    registrars = [_make_registrar("tool_a", "tool_b", "tool_c")]

    register_all_tools(mcp, registrars, enabled_tools={"tool_a", "tool_c"})

    assert _get_registered_tool_names(mcp) == {"tool_a", "tool_c"}


def test_tools_disable_blocklist():
    mcp = FastMCP("test")
    registrars = [_make_registrar("tool_a", "tool_b", "tool_c")]

    register_all_tools(mcp, registrars, disabled_tools={"tool_b"})

    assert _get_registered_tool_names(mcp) == {"tool_a", "tool_c"}


def test_tools_enable_takes_precedence_over_disable():
    mcp = FastMCP("test")
    registrars = [_make_registrar("tool_a", "tool_b", "tool_c")]

    register_all_tools(
        mcp, registrars, enabled_tools={"tool_a"}, disabled_tools={"tool_a"}
    )

    assert _get_registered_tool_names(mcp) == {"tool_a"}


def test_mcp_tool_restored_after_filtering():
    mcp = FastMCP("test")
    original_tool = mcp.tool
    registrars = [_make_registrar("tool_a")]

    register_all_tools(mcp, registrars, enabled_tools={"tool_a"})

    assert mcp.tool is original_tool
