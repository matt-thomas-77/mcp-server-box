"""Redaction of credentials from text that leaves the server.

Box SDK errors quote the HTTP request that failed. For a request to
``/oauth2/token`` that quote contains the full form body, including
``client_id`` and ``client_secret``. FastMCP turns any exception raised by a
tool into a client-visible message, so that text has to be scrubbed before it
reaches an MCP client or the logs.
"""

import logging
import os
import re
import traceback

REDACTED = "[REDACTED]"

# Environment variables whose literal values must never leave the server.
SECRET_ENV_VARS = (
    "BOX_CLIENT_SECRET",
    "BOX_PRIVATE_KEY",
    "BOX_PRIVATE_KEY_PASSPHRASE",
    "BOX_MCP_SERVER_AUTH_TOKEN",
)

# Literal values shorter than this are ignored, so a short placeholder cannot
# blank out unrelated parts of a message.
_MIN_LITERAL_LENGTH = 8

# Keys that carry a credential in query strings, form bodies, JSON payloads and
# the dict dumps the Box SDK includes in its error messages.
_SENSITIVE_KEYS = (
    "client_secret",
    "client_id",
    "access_token",
    "refresh_token",
    "id_token",
    "subject_token",
    "client_assertion",
    "assertion",
    "api_key",
    "passphrase",
    "password",
    "private_key",
)

# The value must not start with "[", so an already redacted value is left
# alone instead of being wrapped a second time.
_KEY_VALUE_RE = re.compile(
    r"(?i)\b(" + "|".join(_SENSITIVE_KEYS) + r")\b"
    r"([\"']?\s*[=:]\s*[\"']?)"
    r"([^\"'\s,&}\])\[]+)"
)

# Handled separately from the keys above so the whole header value is dropped
# rather than just the scheme token.
_AUTH_HEADER_RE = re.compile(
    r"(?i)\b(authorization[\"']?\s*[=:]\s*[\"']?)"
    r"((?:bearer|basic|token)\s+)?"
    r"([^\"'\r\n,}]+)"
)

_BEARER_RE = re.compile(r"(?i)\b(bearer\s+)([A-Za-z0-9._~+/=-]{8,})")

_PEM_RE = re.compile(
    r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?-----END [A-Z ]*PRIVATE KEY-----",
    re.DOTALL,
)


def _literal_secrets() -> list[str]:
    """Literal secret values from the environment, longest first."""
    values = {
        value.strip()
        for value in (os.getenv(name) for name in SECRET_ENV_VARS)
        if value and len(value.strip()) >= _MIN_LITERAL_LENGTH
    }
    return sorted(values, key=len, reverse=True)


def redact(text: str) -> str:
    """Replace anything that looks like a credential in ``text``."""
    if not text:
        return text

    redacted = _PEM_RE.sub(REDACTED, text)

    # Known secret values are removed even when they appear without a label.
    for value in _literal_secrets():
        redacted = redacted.replace(value, REDACTED)

    redacted = _AUTH_HEADER_RE.sub(
        lambda match: f"{match.group(1)}{match.group(2) or ''}{REDACTED}", redacted
    )
    redacted = _BEARER_RE.sub(lambda match: f"{match.group(1)}{REDACTED}", redacted)
    redacted = _KEY_VALUE_RE.sub(
        lambda match: f"{match.group(1)}{match.group(2)}{REDACTED}", redacted
    )

    return redacted


def redact_exception(exc: BaseException) -> str:
    """Render an exception as a message that is safe to return to a client."""
    return redact(f"{type(exc).__name__}: {exc}")


class RedactingFilter(logging.Filter):
    """Scrub credentials from log records before they are emitted.

    Errors that carry credentials reach the logs by paths the tool wrapper does
    not cover, such as a Box client that fails while the lifespan starts up.
    """

    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = ()

        if record.exc_info:
            # Pre-rendering exc_text stops the formatter from writing the
            # unredacted traceback itself.
            record.exc_text = redact(
                "".join(traceback.format_exception(*record.exc_info))
            )

        return True
