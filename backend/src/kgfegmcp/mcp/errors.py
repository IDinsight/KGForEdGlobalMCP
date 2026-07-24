"""This module translates application failures at FastMCP component boundaries.

Expected application-domain errors become stable public ``PromptError``,
``ResourceError``, or ``ToolError`` messages. Unexpected exceptions are logged
internally and replaced with fixed messages that disclose no paths or implementation
details. Existing FastMCP boundary errors pass through unchanged.
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
from fastmcp.exceptions import PromptError, ResourceError, ToolError

# Package Library
from kgfegmcp.errors import KGFEGMCPError

_INTERNAL_PROMPT_ERROR_MESSAGE: Final[str] = (
    "internal_error: The server could not render the prompt."
)
_INTERNAL_RESOURCE_ERROR_MESSAGE: Final[str] = (
    "internal_error: The server could not read the resource."
)
_INTERNAL_TOOL_ERROR_MESSAGE: Final[str] = (
    "internal_error: The server could not complete the request."
)
_LOGGER = logging.getLogger("fastmcp.kgfegmcp.mcp.errors")


def _log_unexpected_error(*, error: Exception, operation: str) -> None:
    """Record one unexpected boundary failure with an internal incident identifier.

    Parameters
    ----------
    error
        The unexpected exception raised by the MCP component implementation.
    operation
        Stable internal operation name used only for server diagnostics.
    """

    incident_id = uuid4().hex
    _LOGGER.exception(
        msg=(
            f"Unexpected backend error masked at the MCP boundary: "
            f"error_type={type(error).__name__}, "
            f"incident_id={incident_id}, "
            f"operation={operation}."
        )
    )


def _log_expected_error(*, error: KGFEGMCPError, operation: str) -> None:
    """Record one expected translated domain failure without sensitive values.

    Parameters
    ----------
    error
        The expected exception raised by the MCP component implementation.
    operation
        Stable internal operation name used only for server diagnostics.
    """

    detail_keys = tuple(sorted(error.details))
    _LOGGER.warning(
        msg=(
            f"Expected backend error translated at the MCP boundary: "
            f"detail_keys={detail_keys!r}, "
            f"error_code={error.error_code}, "
            f"error_type={type(error).__name__}, "
            f"operation={operation}."
        )
    )


def _normalized_operation(operation: str) -> str:
    """Return one validated internal MCP operation name.

    Parameters
    ----------
    operation
        Stable internal operation name used only for server diagnostics.

    Returns
    -------
    str
        Stripped non-empty operation name.

    Raises
    ------
    ValueError
        If the supplied operation name is empty.
    """

    normalized = operation.strip()

    if not normalized:
        raise ValueError("MCP operation names must be non-empty.")

    return normalized


@contextmanager
def prompt_error_boundary(operation: str) -> Iterator[None]:
    """Translate backend failures into stable FastMCP prompt errors.

    Parameters
    ----------
    operation
        Stable internal operation name used only for server diagnostics.

    Yields
    ------
    None
        Control to the protected MCP prompt implementation.

    Raises
    ------
    ValueError
        If ``operation`` is empty.
    fastmcp.exceptions.PromptError
        Re-raises an existing prompt error, translates an expected domain error, or
        masks an unexpected exception with a fixed public message.
    """

    normalized_operation = _normalized_operation(operation)

    try:
        yield
    except PromptError:
        raise
    except KGFEGMCPError as error:
        _log_expected_error(error=error, operation=normalized_operation)
        raise PromptError(f"{error.error_code}: {error.message}") from None
    except Exception as error:
        _log_unexpected_error(error=error, operation=normalized_operation)
        raise PromptError(_INTERNAL_PROMPT_ERROR_MESSAGE) from None


@contextmanager
def resource_error_boundary(operation: str) -> Iterator[None]:
    """Translate backend failures into stable FastMCP resource errors.

    Parameters
    ----------
    operation
        Stable internal operation name used only for server diagnostics.

    Yields
    ------
    None
        Control to the protected MCP resource implementation.

    Raises
    ------
    ValueError
        If ``operation`` is empty.
    fastmcp.exceptions.ResourceError
        Re-raises an existing resource error, translates an expected domain error, or
        masks an unexpected exception with a fixed public message.
    """

    normalized_operation = _normalized_operation(operation)

    try:
        yield
    except ResourceError:
        raise
    except KGFEGMCPError as error:
        _log_expected_error(error=error, operation=normalized_operation)
        raise ResourceError(f"{error.error_code}: {error.message}") from None
    except Exception as error:
        _log_unexpected_error(error=error, operation=normalized_operation)
        raise ResourceError(_INTERNAL_RESOURCE_ERROR_MESSAGE) from None


@contextmanager
def tool_error_boundary(operation: str) -> Iterator[None]:
    """Translate backend failures into stable FastMCP tool errors.

    Parameters
    ----------
    operation
        Stable internal operation name used only for server diagnostics.

    Yields
    ------
    None
        Control to the protected MCP tool implementation.

    Raises
    ------
    ValueError
        If ``operation`` is empty.
    fastmcp.exceptions.ToolError
        Re-raises an existing tool error, translates an expected domain error, or masks
        an unexpected exception with a fixed public message.
    """

    normalized_operation = _normalized_operation(operation)

    try:
        yield
    except ToolError:
        raise
    except KGFEGMCPError as error:
        _log_expected_error(error=error, operation=normalized_operation)
        raise ToolError(f"{error.error_code}: {error.message}") from None
    except Exception as error:
        _log_unexpected_error(error=error, operation=normalized_operation)
        raise ToolError(_INTERNAL_TOOL_ERROR_MESSAGE) from None
