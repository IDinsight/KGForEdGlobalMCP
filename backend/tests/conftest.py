"""This module contains fixtures for backend tests.

NB: Fixtures provide a way to set up a consistent and isolated environment for tests.
They typically handle initialization, cleanup, etc. Mocks, on the other hand, are used
to simulate the behavior of real objects or dependencies that tests interact with,
especially when those dependencies are slow, complex, or external.
"""

# Standard Library
import sys

from pathlib import Path
from types import ModuleType, SimpleNamespace
from typing import Any, Generator

# Third Party Library
import pytest

# Append the framework path.
PACKAGE_PATH = Path(__file__).resolve().parents[2]
if PACKAGE_PATH / "backend" / "src" not in sys.path:
    print(f"Appending '{PACKAGE_PATH / 'backend' / 'src'}' to system path...")
    sys.path.append(str(PACKAGE_PATH / "backend" / "src"))
if PACKAGE_PATH / "backend" / "tests" not in sys.path:
    print(f"Appending '{PACKAGE_PATH / 'backend' / 'tests'}' to system path...")
    sys.path.append(str(PACKAGE_PATH / "backend" / "tests"))

# Package Library
from kgfegmcp.utils import logging_  # noqa: E402
from tests.types_ import InstallLoguruMock, LogCall  # noqa: E402


# Fixtures.
@pytest.fixture(scope="function")
def fixture_loguru_capture() -> Generator[list[str], None, None]:
    """Attach a simple sink to a module's loguru logger and collect messages.

    Yields
    ------
    Generator[list[str], None, None]
        The list of captured log messages.
    """

    captured_msg: list[str] = []

    def sink(msg: str) -> None:
        """A simple sink that appends messages to a list.

        NB: `msg` is a loguru Message whereas str(msg) includes formatted line.

        Parameters
        ----------
        msg
            The log message.
        """

        captured_msg.append(str(msg))

    sink_id = logging_.logger.add(sink, format="{message}", level="DEBUG")

    try:
        yield captured_msg
    finally:
        logging_.logger.remove(sink_id)


# Mocks.
@pytest.fixture(scope="function")
def mock_loguru_logger(monkeypatch: pytest.MonkeyPatch) -> InstallLoguruMock:
    """Mock `loguru` logger into a target module, capturing log calls.

    Usage:
        calls = mock_loguru_logger(target_module, raise_on_level=True)
        calls = mock_loguru_logger(target_module, fixed_level_name="INFO")

    Parameters
    ----------
    monkeypatch
        Pytest monkeypatch fixture.

    Returns
    -------
    InstallLoguruMock
        The installer function that patches `logger` in the target module.
    """

    def install(
        target_module: ModuleType,
        *,
        fixed_level_name: str | None = None,
        raise_on_level: bool = False,
    ) -> list[LogCall]:
        """Patch `target_module.logger` with a fake that captures log calls.

        Parameters
        ----------
        target_module
            The module where to patch `logger`.
        fixed_level_name
            If provided, all log calls will appear to use this level name.
        raise_on_level
            If True, calling `logger.level(name)` will raise a KeyError, simulating an
            unknown log level.

        Returns
        -------
        list[LogCall]
            The list that will capture the log calls.
        """

        calls: list[LogCall] = []

        class StubLogger:
            """A stub logger mimicking key loguru methods."""

            @staticmethod
            def exception(  # pylint: disable=unused-argument
                message: str,
                *args: Any,
                **kwargs: Any,
            ) -> None:
                """Capture the log call arguments for `logger.exception`.

                Parameters
                ----------
                message
                    The log message.
                args
                    Additional positional arguments (ignored).
                kwargs
                    Additional keyword arguments (ignored).
                """

                calls.append(
                    LogCall(
                        level="EXCEPTION",
                        message=message,
                        opt_kwargs={"exception": True},
                    )
                )

            @staticmethod
            def level(name: str) -> SimpleNamespace:
                """A stub for `logger.level(name)` that either raises KeyError or
                returns an object with a `.name` attribute.

                Parameters
                ----------
                name
                    The log level name.

                Returns
                -------
                Any
                    An object with a `.name` attribute.

                Raises
                ------
                KeyError
                    If `raise_on_level` is True, raises KeyError to simulate unknown
                    level.
                """

                if raise_on_level:
                    raise KeyError("unknown level")

                # Return an object with a `.name` attribute (loguru-like).
                lvl_name = fixed_level_name if fixed_level_name is not None else name

                return SimpleNamespace(name=lvl_name)

            @staticmethod
            def opt(**kwargs: dict[str, Any]) -> object:
                """A stub for `logger.opt(...)` that captures the kwargs and returns an
                object with a `.log(level, message)` method.

                Parameters
                ----------
                kwargs
                    Optional keyword arguments like `depth`, `exception`, etc.

                Returns
                -------
                object
                    An object with a `.log(level, message)` method.
                """

                opt_kwargs = dict(kwargs)

                class L:
                    """A stub logger with a `.log(level, message)` method."""

                    @staticmethod
                    def log(level: int | str, message: str) -> None:
                        """Capture the log call arguments.

                        Parameters
                        ----------
                        level
                            The log level (int or str).
                        message
                            The log message.
                        """

                        calls.append(
                            LogCall(level=level, message=message, opt_kwargs=opt_kwargs)
                        )

                return L()

        def _make_level(name: str) -> staticmethod:
            """Create a static method for a log level function.

            Parameters
            ----------
            name
                The log level name (e.g., 'info', 'error').

            Returns
            -------
            staticmethod
                A static method that captures log calls at this level.
            """

            def _fn(  # pylint: disable=unused-argument
                message: str,
                *args: Any,
                **kwargs: Any,
            ) -> None:
                """Capture the log call arguments.

                Parameters
                ----------
                message
                    The log message.
                args
                    Additional positional arguments (ignored).
                kwargs
                    Additional keyword arguments (ignored).
                """

                calls.append(
                    LogCall(level=name.upper(), message=message, opt_kwargs={})
                )

            return staticmethod(_fn)

        for _lvl in (
            "debug",
            "critical",
            "error",
            "info",
            "success",
            "trace",
            "warning",
        ):
            setattr(StubLogger, _lvl, _make_level(_lvl))

        monkeypatch.setattr(target_module, "logger", StubLogger())
        return calls

    return install


# Conftest helpers.
