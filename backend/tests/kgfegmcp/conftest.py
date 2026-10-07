"""Accepted local evidence fixtures and explicit offline isolation."""

# Standard Library
import json
import socket

from pathlib import Path
from typing import Any

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState, bootstrap_application
from kgfegmcp.domain.enums import GraphType


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


@pytest.fixture(scope="session")
def lp_dataset_missing(accepted_state: AppState) -> tuple[str, ...]:
    """Detect pending LP migrations only after normal package validation succeeds."""
    baseline = json.loads(
        (
            Path(__file__).resolve().parents[1] / "fixtures/progression_baseline.json"
        ).read_text()
    )
    runtimes = accepted_state.catalog_load_result.package_runtimes
    expected = set(baseline)
    actual = {str(r.catalog_package.package_identity.framework_id) for r in runtimes}
    assert (
        len(runtimes) == len(expected) and actual == expected
    ), "Dataset acceptance requires exactly the six baseline framework packages."
    missing = []
    for runtime in runtimes:
        package = runtime.loaded_package
        if GraphType.LEARNING_PROGRESSIONS not in package.manifest.included_graph_types:
            missing.append(str(package.manifest.framework_id))
        else:
            # A declared but broken LP package must fail, never become a skip.
            assert runtime.catalog_package.capabilities.has_learning_progressions
            assert (
                runtime.catalog_package.capabilities.has_learning_progression_provenance
            )
            assert package.learning_progression_evidence is not None
    return tuple(sorted(missing))


@pytest.fixture(autouse=True)
def require_dataset_for_marked_tests(request: pytest.FixtureRequest) -> None:
    """Run dataset acceptance automatically after all six migrations are installed."""
    strict = request.config.getoption("--require-lp-dataset")
    if not strict and request.node.get_closest_marker("lp_dataset") is None:
        return
    missing = request.getfixturevalue("lp_dataset_missing")
    if not missing:
        return
    reason = (
        f"Complete LP dataset required ({6 - len(missing)}/6 migrated packages); "
        "use --require-lp-dataset to fail on an incomplete migration."
    )
    if strict:
        pytest.fail(reason + " Missing LP: " + ", ".join(missing))
    pytest.skip(reason)
