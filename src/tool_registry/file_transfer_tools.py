from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations

from tools.box_tools_file_transfer import (
    box_file_download_tool,
    box_file_upload_tool,
)


def register_file_transfer_tools(mcp: FastMCP):
    mcp.tool(
        annotations=ToolAnnotations(
            name="box_file_download_tool",
            description="Tool for downloading files from Box.",
            idempotentHint=True,
            destructiveHint=False,
            readOnlyHint=True,
            openWorldHint=False,
        )
    )(box_file_download_tool)
    mcp.tool()(box_file_upload_tool)
