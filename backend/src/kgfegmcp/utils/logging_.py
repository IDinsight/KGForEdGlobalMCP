"""This module provides explicit Loguru configuration and optional function-call
logging helpers.
"""

# Future Library
from __future__ import annotations

# Standard Library
import functools
import inspect
import logging
import sys

from collections.abc import Callable, Mapping
from pathlib import Path
from typing import TYPE_CHECKING, Any, ParamSpec, TypeVar, cast

# Third Party Library
from loguru import logger

# Package Library
from kgfegmcp.config import LogLevel, RuntimeEnvironment
from kgfegmcp.utils.general import Valid, recurse_replace, redact_tokens

if TYPE_CHECKING:
    # Third Party Library
    from loguru import (
        AsyncHandlerConfig,
        BasicHandlerConfig,
        FileHandlerConfig,
        Logger,
        Record,
    )
else:
    Logger = type(logger)

_CUSTOM_LEVELS: tuple[tuple[str, int | None, str, str], ...] = (
    ("DEBUG", None, "<white>", "🐞"),
    ("INFO", None, "<cyan>", "ℹ️"),
    ("WARNING", None, "<bold><magenta>", "⚠️"),
    ("ERROR", None, "<bold><red>", "❗"),
    ("ATTN", 35, "<bold><yellow>", "🚨"),
    ("CHAT", 15, "<bold><blue>", "💬"),
    ("CELEBRATE", 25, "<bold><green>", "🎉"),
)
_RUNTIME_ENVIRONMENTS: frozenset[str] = frozenset({"dev", "local", "prod", "testing"})
P = ParamSpec("P")
R = TypeVar("R")
LogDecorator = Callable[[Callable[P, R]], Callable[P, R]]


class InterceptHandler(logging.Handler):
    """Forward standard-library logging records to the configured Loguru logger."""

    def emit(self, record: logging.LogRecord) -> None:
        """Forward one standard-library record without changing its exception context.

        Parameters
        ----------
        record
            Record emitted by the standard-library logging system.
        """

        try:
            level: int | str = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame = logging.currentframe()
        depth = 2

        while (
            frame is not None
            and frame.f_back is not None
            and frame.f_code.co_filename == logging.__file__
        ):
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def _default_handlers(
    *,
    environment: RuntimeEnvironment,
    log_fp: str | Path | None,
    logging_level: LogLevel,
) -> list[BasicHandlerConfig | FileHandlerConfig | AsyncHandlerConfig]:
    """Build the default Loguru handlers for explicit application initialization.

    Parameters
    ----------
    environment
        Validated runtime environment.
    log_fp
        Optional JSON log destination.
    logging_level
        Validated Loguru threshold.

    Returns
    -------
    list[BasicHandlerConfig | FileHandlerConfig | AsyncHandlerConfig]
        Handler declarations accepted by ``logger.configure``.
    """

    diagnose = environment == "local"
    stderr_handler: BasicHandlerConfig = {
        "backtrace": True,
        "colorize": True,
        "diagnose": diagnose,
        "enqueue": True,
        "filter": cast(Callable[[Record], bool], _redact_log_record),
        "format": (
            "<g>{time:YYYY-MM-DD HH:mm:ss}</g> | "
            "<level>{level.icon} {message}</level>"
        ),
        "level": logging_level,
        "serialize": False,
        "sink": sys.stderr,
    }
    handlers: list[BasicHandlerConfig | FileHandlerConfig | AsyncHandlerConfig] = [
        stderr_handler
    ]

    if log_fp is not None:
        file_handler: FileHandlerConfig = {
            "backtrace": True,
            "delay": True,
            "diagnose": diagnose,
            "encoding": "utf-8",
            "enqueue": True,
            "filter": cast(Callable[[Record], bool], _redact_log_record),
            "level": logging_level,
            "rotation": "10 MB",
            "serialize": True,
            "sink": log_fp,
        }
        handlers.append(file_handler)

    return handlers


def _escape_angle_brackets(value: object) -> str:
    """Escape angle brackets before interpolating arbitrary values into Loguru markup.

    Parameters
    ----------
    value
        Value whose string representation will be logged.

    Returns
    -------
    str
        String representation with Loguru markup delimiters escaped.
    """

    opening_escaped = recurse_replace(new_str=r"\<", orig_str="<", x=str(value))
    return cast(str, recurse_replace(new_str=r"\>", orig_str=">", x=opening_escaped))


def _generate_entry_log_str(
    *,
    args: tuple[object, ...],
    extra_args: tuple[str, ...],
    kwargs: Mapping[str, object],
    name: str,
) -> str:
    """Build one deterministic function-entry message.

    Parameters
    ----------
    args
        Positional arguments supplied to the decorated callable.
    extra_args
        Attribute names to read from the first positional argument when available.
    kwargs
        Keyword arguments supplied to the decorated callable.
    name
        Qualified callable name.

    Returns
    -------
    str
        Escaped function-entry message.
    """

    owner = args[0] if args else None
    extra_lines = tuple(
        (
            f"{_escape_angle_brackets(attribute_name)}: "
            f"{_escape_angle_brackets(getattr(owner, attribute_name, 'N/A'))}"
        )
        for attribute_name in extra_args
    )
    extra_args_str = "\n".join(extra_lines)
    return (
        f"ENTERING: '{name}'\n\n"
        f"args:\n{_escape_angle_brackets(args)}\n\n"
        f"kwargs:\n{_escape_angle_brackets(kwargs)}\n\n"
        f"extra_args:\n{extra_args_str}"
    )


def _generate_exit_log_str(*, name: str, result: object) -> str:
    """Build one deterministic function-exit message.

    Parameters
    ----------
    name
        Qualified callable name.
    result
        Value returned by the decorated callable.

    Returns
    -------
    str
        Escaped function-exit message.
    """

    return f"EXITING: '{name}'\nresult={_escape_angle_brackets(result)}"


def initialize_logger(
    *,
    config: dict[str, Any] | None = None,
    environment: RuntimeEnvironment = "local",
    log_fp: str | Path | None = None,
    logging_level: LogLevel = "INFO",
) -> Logger:
    """Configure Loguru and standard-library interception explicitly.

    Parameters
    ----------
    config
        Optional complete keyword configuration for ``logger.configure``. When omitted,
        deterministic stderr and optional file handlers are constructed here.
    environment
        Runtime environment controlling diagnostic trace detail in default handlers.
    log_fp
        Optional JSON log destination used only with the default configuration.
    logging_level
        Validated root and Loguru logging threshold.

    Returns
    -------
    Logger
        Configured process-wide Loguru logger.

    Raises
    ------
    ValueError
        If the environment or logging level is unsupported, custom levels conflict, or
        ``config`` and ``log_fp`` are both set.
    """

    if environment not in _RUNTIME_ENVIRONMENTS:
        raise ValueError(
            f"Invalid runtime environment: {environment}. "
            f"Valid environments are: {tuple(sorted(_RUNTIME_ENVIRONMENTS))}"
        )

    if not Valid.is_valid_logging_level(logging_level=logging_level):
        raise ValueError(
            f"Invalid logging level: {logging_level}. "
            f"Valid logging levels are: {Valid().logging_levels}"
        )

    if config is not None and log_fp is not None:
        raise ValueError("log_fp may not be combined with an explicit logger config.")

    _register_log_levels()
    logger.remove()

    if config is None:
        handlers = _default_handlers(
            environment=environment,
            log_fp=log_fp,
            logging_level=logging_level,
        )
        logger.configure(handlers=handlers)
    else:
        logger.configure(**config)

    _install_standard_logging_intercept(logging_level=logging_level)
    return logger


def _install_standard_logging_intercept(*, logging_level: LogLevel) -> None:
    """Install one explicit process-wide standard-library logging intercept.

    Parameters
    ----------
    logging_level
        Root logging threshold established by the application entry point.
    """

    intercept_handler = InterceptHandler()
    logging.root.handlers.clear()
    logging.root.setLevel(logging_level)
    logging.root.addHandler(intercept_handler)

    for existing_logger in logging.root.manager.loggerDict.values():
        if isinstance(existing_logger, logging.PlaceHolder):
            continue

        existing_logger.handlers = [intercept_handler]
        existing_logger.propagate = False


def _log_message(*, level: str | int, message: str) -> None:
    """Write one already-rendered message through Loguru's dynamic-level API.

    Parameters
    ----------
    level
        Loguru level name or number.
    message
        Fully rendered message.
    """

    logger.opt(depth=2).log(level, message)


def _redact_log_record(record: dict[str, Any]) -> bool:
    """Redact sensitive tokens in one Loguru record and retain the record.

    Parameters
    ----------
    record
        Mutable Loguru record supplied to a handler filter.

    Returns
    -------
    bool
        Always ``True`` so the redacted record remains eligible for emission.
    """

    redacted_record = redact_tokens(record)
    record.clear()
    record.update(redacted_record)
    return True


def _register_log_levels() -> None:
    """Register or update application Loguru levels during explicit initialization.

    Raises
    ------
    ValueError
        If an existing custom level uses a different numeric severity.
    """

    for name, number, color, icon in _CUSTOM_LEVELS:
        try:
            existing_level = logger.level(name)
        except ValueError:
            if number is None:
                raise ValueError(
                    f"Required standard Loguru level is unavailable: {name}."
                ) from None

            logger.level(color=color, icon=icon, name=name, no=number)
            continue

        if number is not None and existing_level.no != number:
            raise ValueError(
                f"Existing Loguru level {name} uses severity "
                f"{existing_level.no}, expected {number}."
            )

        logger.level(color=color, icon=icon, name=name)


def log_func_call(
    *,
    entry: bool = True,
    exit_: bool = True,
    extra_args: tuple[str, ...] | None = None,
    level: str | int = "INFO",
) -> LogDecorator[P, R]:
    """Decorate a synchronous or asynchronous callable with entry and exit logging.

    Parameters
    ----------
    entry
        Whether to emit an entry message.
    exit_
        Whether to emit an exit message.
    extra_args
        Optional attribute names read from the first positional argument.
    level
        Loguru level name or number.

    Returns
    -------
    LogDecorator[P, R]
        Signature-preserving decorator for the supplied callable.
    """

    logged_attributes = extra_args or ()

    def decorator(func: Callable[P, R]) -> Callable[P, R]:
        """Wrap one callable while preserving its public signature metadata.

        Parameters
        ----------
        func
            Synchronous or asynchronous callable to wrap.

        Returns
        -------
        Callable[P, R]
            Wrapped callable with optional entry and exit logging.
        """

        name = func.__qualname__

        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapped(*args: P.args, **kwargs: P.kwargs) -> Any:
                """Log and await one asynchronous decorated callable.

                Parameters
                ----------
                args
                    Positional arguments supplied to the decorated callable.
                kwargs
                    Keyword arguments supplied to the decorated callable.

                Returns
                -------
                Any
                    Result of the decorated callable.
                """

                if entry:
                    _log_message(
                        level=level,
                        message=_generate_entry_log_str(
                            args=cast(tuple[object, ...], args),
                            extra_args=logged_attributes,
                            kwargs=cast(Mapping[str, object], kwargs),
                            name=name,
                        ),
                    )

                result = await func(*args, **kwargs)

                if exit_:
                    _log_message(
                        level=level,
                        message=_generate_exit_log_str(name=name, result=result),
                    )

                return result

            return cast(Callable[P, R], async_wrapped)

        @functools.wraps(func)
        def sync_wrapped(*args: P.args, **kwargs: P.kwargs) -> R:
            """Log and call one synchronous decorated callable.

            Parameters
            ----------
            args
                Positional arguments supplied to the decorated callable.
            kwargs
                Keyword arguments supplied to the decorated callable.

            Returns
            -------
            R
                Result of the decorated callable.
            """

            if entry:
                _log_message(
                    level=level,
                    message=_generate_entry_log_str(
                        args=cast(tuple[object, ...], args),
                        extra_args=logged_attributes,
                        kwargs=cast(Mapping[str, object], kwargs),
                        name=name,
                    ),
                )

            result = func(*args, **kwargs)

            if exit_:
                _log_message(
                    level=level,
                    message=_generate_exit_log_str(name=name, result=result),
                )

            return result

        return sync_wrapped

    return decorator
