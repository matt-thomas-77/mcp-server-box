import logging

import pytest
from mcp.server.fastmcp import Context, FastMCP
from mcp.server.fastmcp.exceptions import ToolError

from redaction import REDACTED, RedactingFilter, redact, redact_exception
from tool_registry import register_all_tools

# Shaped like the message the Box SDK raises when a CCG token request fails.
BOX_TOKEN_ERROR = """
Message: 400 ; Request ID:
Request:
\tMethod: POST
\tURL: https://api.box.com/oauth2/token
\tBody:
'grant_type=client_credentials&client_id=abc123clientid&client_secret=s3cr3tvalue0000&box_subject_type=enterprise&box_subject_id=20299075'
Response:
\tBody:
{       'error': 'unauthorized_client'}
"""


def test_redacts_urlencoded_client_secret():
    result = redact(BOX_TOKEN_ERROR)

    assert "s3cr3tvalue0000" not in result
    assert "abc123clientid" not in result
    assert f"client_secret={REDACTED}" in result


def test_keeps_non_secret_context():
    result = redact(BOX_TOKEN_ERROR)

    # The parts an operator needs to diagnose the failure survive.
    assert "https://api.box.com/oauth2/token" in result
    assert "unauthorized_client" in result
    assert "box_subject_type=enterprise" in result
    assert "box_subject_id=20299075" in result


def test_redacts_json_style_secret():
    result = redact("{'client_secret': 's3cr3tvalue0000', 'grant_type': 'refresh'}")

    assert "s3cr3tvalue0000" not in result
    assert "'grant_type': 'refresh'" in result


def test_redacts_authorization_header_and_bearer_token():
    result = redact("{'Authorization': 'Bearer abcdef1234567890'}")

    assert "abcdef1234567890" not in result
    # The scheme is kept so the failure is still recognizable.
    assert "Bearer" in result

    assert "abcdef1234567890" not in redact("sent Bearer abcdef1234567890 upstream")


def test_redacts_private_key_block():
    text = (
        "private_key: -----BEGIN RSA PRIVATE KEY-----\n"
        "MIIEowIBAAKCAQEA1234\nabcd\n"
        "-----END RSA PRIVATE KEY-----"
    )

    result = redact(text)

    assert "MIIEowIBAAKCAQEA1234" not in result
    assert "BEGIN RSA PRIVATE KEY" not in result


def test_redacts_literal_env_secret_without_a_label(monkeypatch):
    monkeypatch.setenv("BOX_CLIENT_SECRET", "unlabeled-secret-value")

    result = redact("the request failed using unlabeled-secret-value somewhere")

    assert "unlabeled-secret-value" not in result
    assert REDACTED in result


def test_short_env_secret_is_not_used_for_literal_matching(monkeypatch):
    monkeypatch.setenv("BOX_CLIENT_SECRET", "short")

    assert redact("a short message") == "a short message"


def test_ordinary_error_text_is_untouched():
    text = "Message: 404 Not Found; file 11.7 Test Station Design.docx does not exist"

    assert redact(text) == text


def test_redaction_is_idempotent(monkeypatch):
    # The literal pass replaces the value first; the key/value pass must not
    # then wrap the placeholder again.
    monkeypatch.setenv("BOX_CLIENT_SECRET", "s3cr3tvalue0000")

    once = redact(BOX_TOKEN_ERROR)

    assert f"client_secret={REDACTED}&" in once
    assert redact(once) == once


def test_redact_exception_includes_type_name():
    message = redact_exception(ValueError("client_secret=s3cr3tvalue0000"))

    assert message.startswith("ValueError: ")
    assert "s3cr3tvalue0000" not in message


def _register(mcp: FastMCP, func) -> None:
    register_all_tools(mcp, [lambda server: server.tool()(func)])


@pytest.mark.asyncio
async def test_tool_error_is_redacted():
    async def leaky_tool(ctx: Context, file_id: str) -> str:
        """A tool that fails the way the Box SDK does."""
        raise RuntimeError(BOX_TOKEN_ERROR)

    mcp = FastMCP("test")
    _register(mcp, leaky_tool)

    with pytest.raises(ToolError) as exc_info:
        await mcp._tool_manager.call_tool("leaky_tool", {"file_id": "123"})

    message = str(exc_info.value)
    assert "s3cr3tvalue0000" not in message
    assert REDACTED in message


@pytest.mark.asyncio
async def test_sync_tool_error_is_redacted():
    def leaky_sync_tool() -> str:
        """A synchronous tool that leaks a secret."""
        raise RuntimeError("client_secret=s3cr3tvalue0000")

    mcp = FastMCP("test")
    _register(mcp, leaky_sync_tool)

    with pytest.raises(ToolError) as exc_info:
        await mcp._tool_manager.call_tool("leaky_sync_tool", {})

    assert "s3cr3tvalue0000" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_wrapping_preserves_schema_and_results():
    async def echo_tool(ctx: Context, query: str, limit: int = 5) -> dict:
        """Echo the arguments back."""
        return {"query": query, "limit": limit}

    mcp = FastMCP("test")
    _register(mcp, echo_tool)

    tool = mcp._tool_manager.get_tool("echo_tool")
    assert tool is not None
    assert tool.is_async
    assert tool.description == "Echo the arguments back."
    assert set(tool.parameters["properties"]) == {"query", "limit"}
    # The context parameter stays out of the client-facing schema.
    assert tool.context_kwarg == "ctx"

    result = await mcp._tool_manager.call_tool("echo_tool", {"query": "box"})
    assert result == {"query": "box", "limit": 5}


def test_logging_filter_redacts_message_and_traceback():
    record = logging.LogRecord(
        name="test",
        level=logging.ERROR,
        pathname=__file__,
        lineno=1,
        msg="failed with client_secret=%s",
        args=("s3cr3tvalue0000",),
        exc_info=None,
    )

    assert RedactingFilter().filter(record) is True
    assert "s3cr3tvalue0000" not in record.getMessage()

    try:
        raise RuntimeError("client_secret=s3cr3tvalue0000")
    except RuntimeError as exc:
        exc_record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="boom",
            args=(),
            exc_info=(type(exc), exc, exc.__traceback__),
        )

    assert RedactingFilter().filter(exc_record) is True
    assert "s3cr3tvalue0000" not in exc_record.exc_text
