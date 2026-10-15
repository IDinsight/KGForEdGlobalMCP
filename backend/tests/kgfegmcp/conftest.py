"""Accepted local evidence fixtures and explicit offline isolation."""

# Standard Library
import socket

from pathlib import Path
from typing import Any

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState, bootstrap_application
from tests.fixtures.evidence_fixtures import (
    SyntheticProject,
    build_synthetic_project,
    copy_synthetic_project,
)


@pytest.fixture(scope="session")
def accepted_state() -> AppState:
    """Bootstrap the actual seven local packages once for acceptance checks."""
    return bootstrap_application()


@pytest.fixture(autouse=True)
def forbid_network(monkeypatch: pytest.MonkeyPatch) -> None:
    """Reject network use rather than substituting live model responses."""

    def reject(*_args: Any, **_kwargs: Any) -> None:
        """Reject an attempted connection."""
        raise AssertionError("Offline verification attempted a network connection.")

    monkeypatch.setattr(socket.socket, "connect", reject)
    monkeypatch.setattr(socket.socket, "connect_ex", reject)


@pytest.fixture(scope="function")
def synthetic_project(
    synthetic_template: SyntheticProject, tmp_path: Path
) -> SyntheticProject:
    """Copy the pristine synthetic project so one test may alter or persist it.

    Parameters
    ----------
    synthetic_template
        Session-wide pristine synthetic project.
    tmp_path
        Per-test temporary directory.

    Returns
    -------
    SyntheticProject
        Private copy with its input set and pending package.
    """

    return copy_synthetic_project(
        project_dir=tmp_path / "project", source=synthetic_template
    )


@pytest.fixture(scope="session")
def synthetic_template(tmp_path_factory: pytest.TempPathFactory) -> SyntheticProject:
    """Build one synthetic full-evidence input set and pending package per session.

    Parameters
    ----------
    tmp_path_factory
        Session temporary-directory factory.

    Returns
    -------
    SyntheticProject
        Pristine project; tests copy it through ``synthetic_project``.
    """

    return build_synthetic_project(
        project_dir=tmp_path_factory.mktemp("synthetic") / "project"
    )
