"""This module translates application failures at FastMCP component boundaries.

This module provides the error boundary used by MCP tools and other exposed components.
Expected application-domain errors are converted into stable public FastMCP
``ToolError`` messages, while unexpected exceptions are logged internally and replaced
with a fixed message that does not disclose implementation details.

The boundary also preserves existing ``ToolError`` instances so that intentionally
public FastMCP failures are not translated a second time.
"""

# Future Library
from __future__ import annotations

# Standard Library
import logging

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Final
from uuid import uuid4

# Third Party Library
from fastmcp.exceptions import ToolError

# Package Library
from kgfegmcp.errors import KGFEGMCPError

_INTERNAL_ERROR_MESSAGE: Final[str] = (
    "internal_error: The server could not complete the request."
)
_LOGGER = logging.getLogger("fastmcp.kgfegmcp.mcp.errors")


@contextmanager
def tool_error_boundary(operation: str) -> Iterator[None]:
    """Translate backend failures into stable FastMCP tool errors.

    Parameters
    ----------
    operation
        Stable internal operation name used only for server-side diagnostics.

    Yields
    ------
    None
        Control to the protected MCP tool implementation.

    Raises
    ------
    ValueError
        If ``operation`` is empty.
    fastmcp.exceptions.ToolError
        Re-raises an existing tool error, translates an expected backend domain error,
        or masks an unexpected exception with a fixed public message.
    """

    normalized_operation = operation.strip()

    if not normalized_operation:
        raise ValueError("Tool operation names must be non-empty.")

    try:
        yield
    except ToolError:
        raise
    except KGFEGMCPError as error:
        detail_keys = tuple(sorted(error.details))
        _LOGGER.warning(
            msg=(
                f"Expected backend error translated at the MCP boundary: "
                f"detail_keys={detail_keys!r}, "
                f"error_code={error.error_code}, "
                f"error_type={type(error).__name__}, "
                f"operation={normalized_operation}."
            )
        )
        raise ToolError(f"{error.error_code}: {error.message}") from None
    except Exception as error:
        incident_id = uuid4().hex
        _LOGGER.exception(
            msg=(
                f"Unexpected backend error masked at the MCP boundary: "
                f"error_type={type(error).__name__}, "
                f"incident_id={incident_id}, "
                f"operation={normalized_operation}."
            )
        )
        raise ToolError(_INTERNAL_ERROR_MESSAGE) from None
