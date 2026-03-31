import logging
from urllib.parse import parse_qs
from typing import Optional

from fastapi import status
from starlette.responses import JSONResponse

from config import McpAuthConfig

logger = logging.getLogger(__name__)


def _get_header_value(scope, header_name: str) -> str:
    """Return a case-insensitive HTTP header value from an ASGI scope."""
    header_name = header_name.lower()

    for key, value in scope.get("headers", []):
        key_str = key.decode("latin-1") if isinstance(key, bytes) else str(key)
        if key_str.lower() != header_name:
            continue

        return (value.decode("latin-1") if isinstance(value, bytes) else str(value)).strip()

    return ""


def _extract_request_token(scope) -> tuple[str, str]:
    """Extract access token from supported request headers.

    Returns:
        tuple[str, str]: token value and source header name.
    """
    auth_header = _get_header_value(scope, "authorization")
    if auth_header:
        if auth_header.startswith("Bearer "):
            return auth_header[len("Bearer ") :].strip(), "authorization"

        # Some clients send raw tokens in Authorization without a scheme.
        if " " not in auth_header.strip():
            return auth_header.strip(), "authorization"

    api_key_header = _get_header_value(scope, "api-key")
    if api_key_header:
        return api_key_header.strip(), "api-key"

    x_api_key_header = _get_header_value(scope, "x-api-key")
    if x_api_key_header:
        return x_api_key_header.strip(), "x-api-key"

    query_string = scope.get("query_string", b"")
    if isinstance(query_string, bytes):
        query_string = query_string.decode("latin-1")

    query_params = parse_qs(query_string, keep_blank_values=False)
    for query_key in ("api-key", "x-api-key", "key", "code", "token", "access_token"):
        query_values = query_params.get(query_key)
        if query_values and query_values[0].strip():
            return query_values[0].strip(), f"query:{query_key}"

    return "", ""


def auth_validate_token(scope, config: "McpAuthConfig") -> Optional[JSONResponse]:
    """
    Validate if the auth token is properly configured.

    Args:
        scope: ASGI scope containing request information
        config: McpAuthConfig containing the expected auth token

    Returns:
        Optional[JSONResponse]: Error response if validation fails, None if successful
    """

    path = scope["path"]
    logger.debug(f"Token validation processing: {scope['method']} {path}")

    expected_token = config.auth_token

    token, source_header = _extract_request_token(scope)

    # Validate authentication
    response = None

    if not expected_token:
        logger.error("BOX_MCP_SERVER_AUTH_TOKEN not configured")
        response = JSONResponse(
            content={
                "error": "invalid_token",
                "error_description": "Server authentication not properly configured",
            },
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
    elif not token:
        logger.warning(
            f"[Token] Missing authentication header for {scope['method']} {path}"
        )
        response = JSONResponse(
            content={
                "error": "invalid_request",
                "error_description": "Missing authentication header (Authorization, api-key, or x-api-key)",
            },
            status_code=status.HTTP_401_UNAUTHORIZED,
        )
    else:
        if token != expected_token:
            logger.warning(
                f"[Token] Invalid token for {scope['method']} {path} via {source_header or 'unknown'}"
            )
            response = JSONResponse(
                content={
                    "error": "invalid_token",
                    "error_description": "The access token is invalid or expired",
                },
                status_code=status.HTTP_401_UNAUTHORIZED,
            )
        else:
            logger.debug(
                f"[Token] Token authentication successful for {scope['method']} {path}"
            )
            return None

    return response
