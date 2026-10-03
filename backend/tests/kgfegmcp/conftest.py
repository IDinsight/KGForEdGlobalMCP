"""Accepted local evidence fixtures and explicit offline isolation."""

# Standard Library
import socket

from typing import Any

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState, bootstrap_application


@pytest.fixture(scope="session")
def accepted_state() -> AppState:
    """Bootstrap the actual six local packages once for acceptance checks."""
    return bootstrap_application()


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject network use rather than substituting live model responses."""

    def reject(*_args: Any, **_kwargs: Any) -> None:
        """Reject an attempted connection."""
        raise AssertionError("Offline verification attempted a network connection.")

    monkeypatch.setattr(socket.socket, "connect", reject)
    monkeypatch.setattr(socket.socket, "connect_ex", reject)
