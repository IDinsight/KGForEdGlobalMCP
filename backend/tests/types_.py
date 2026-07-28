"""This module defines types used across the test suite."""

# Standard Library
from types import ModuleType
from typing import Any, Protocol, TypedDict


class LogCall(TypedDict, total=False):
    """TypedDict for a call to a logging function."""

    level: int | str
    message: str
    opt_kwargs: dict[str, Any]  # e.g., {"depth": 3, "exception": None}


class InstallLoguruMock(Protocol):
    """Protocol for the `mock_loguru` fixture installer function."""

    def __call__(
        self,
        target_module: ModuleType,
        *,
        fixed_level_name: str | None = None,
        raise_on_level: bool = False,
    ) -> list[LogCall]:
        """Patch `target_module.logger` with a stub that implements `.level()` and
        `.opt(...).log(...)`.

        Parameters
        ----------
        target_module
            The module where to patch `logger`.
        fixed_level_name
            If provided, `.level(...)` always returns this name.
        raise_on_level
            If True, `.level(...)` raises KeyError to test fallback paths.

        Returns
        -------
        list[LogCall]
            A live list of captured LogCall dicts (one per `.log(...)` invocation).
        """
