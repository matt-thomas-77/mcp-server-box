from config import McpAuthConfig
from mcp_auth.auth_box import box_auth_validate_token
from mcp_auth.auth_token import auth_validate_token
from middleware import MCP_ACCEPT_HEADER_VALUE, _ensure_mcp_accept_header


def test_auth_validate_token_accepts_string_header_types():
    scope = {
        "type": "http",
        "path": "/mcp",
        "method": "POST",
        "headers": [("Authorization", "Bearer expected-token")],
    }

    response = auth_validate_token(scope=scope, config=McpAuthConfig(auth_token="expected-token"))

    assert response is None


def test_auth_validate_token_accepts_api_key_header():
    scope = {
        "type": "http",
        "path": "/mcp",
        "method": "POST",
        "headers": [(b"api-key", b"expected-token")],
    }

    response = auth_validate_token(scope=scope, config=McpAuthConfig(auth_token="expected-token"))

    assert response is None


def test_auth_validate_token_accepts_x_api_key_header():
    scope = {
        "type": "http",
        "path": "/mcp",
        "method": "POST",
        "headers": [(b"x-api-key", b"expected-token")],
    }

    response = auth_validate_token(scope=scope, config=McpAuthConfig(auth_token="expected-token"))

    assert response is None


def test_auth_validate_token_accepts_query_string_code():
    scope = {
        "type": "http",
        "path": "/mcp",
        "method": "POST",
        "query_string": b"code=expected-token",
        "headers": [],
    }

    response = auth_validate_token(scope=scope, config=McpAuthConfig(auth_token="expected-token"))

    assert response is None


def test_auth_validate_token_accepts_query_string_api_key():
    scope = {
        "type": "http",
        "path": "/mcp",
        "method": "POST",
        "query_string": b"api-key=expected-token",
        "headers": [],
    }

    response = auth_validate_token(scope=scope, config=McpAuthConfig(auth_token="expected-token"))

    assert response is None


def test_box_auth_validate_token_accepts_string_header_types():
    scope = {
        "type": "http",
        "path": "/mcp",
        "method": "POST",
        "headers": [("Authorization", "Bearer oauth-token")],
    }

    response = box_auth_validate_token(scope=scope)

    assert response is None
    assert scope["oauth_token"] == "oauth-token"


def test_ensure_mcp_accept_header_appends_when_missing():
    scope = {
        "type": "http",
        "path": "/mcp",
        "method": "POST",
        "headers": [(b"authorization", b"Bearer token")],
    }

    normalized_scope = _ensure_mcp_accept_header(scope)

    assert (b"accept", MCP_ACCEPT_HEADER_VALUE) in normalized_scope["headers"]


def test_ensure_mcp_accept_header_replaces_wildcard_value():
    scope = {
        "type": "http",
        "path": "/mcp",
        "method": "POST",
        "headers": [(b"accept", b"*/*")],
    }

    normalized_scope = _ensure_mcp_accept_header(scope)

    assert normalized_scope["headers"][0] == (b"accept", MCP_ACCEPT_HEADER_VALUE)


def test_ensure_mcp_accept_header_keeps_compatible_value():
    compatible_value = b"application/json, text/event-stream"
    scope = {
        "type": "http",
        "path": "/mcp",
        "method": "POST",
        "headers": [(b"accept", compatible_value)],
    }

    normalized_scope = _ensure_mcp_accept_header(scope)

    assert normalized_scope["headers"][0] == (b"accept", compatible_value)
