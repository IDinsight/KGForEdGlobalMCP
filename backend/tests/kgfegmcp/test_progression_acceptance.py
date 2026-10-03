"""Independent negative graph/evidence acceptance and finite request contracts."""

# Standard Library
from typing import Any

# Third Party Library
import pytest

from pydantic import ValidationError

# Package Library
from kgfegmcp.bootstrap import AppState
from kgfegmcp.errors import ManifestBuildError
from kgfegmcp.packages.lp_graph import validate_learning_progression_graph
from kgfegmcp.packages.lp_validation import validate_learning_progression_evidence
from kgfegmcp.packages.normalization_sources import read_json_object
from kgfegmcp.services.lp_models import (
    GetLearningProgressionPathsRequest,
    SearchLearningProgressionsRequest,
    TraverseLearningProgressionsRequest,
)
from tests.fixtures.progression_fixtures import selector


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("count", "lp_manifest_count_mismatch"),
        ("duplicate", "lp_pair_conflict"),
        ("endpoint", "lp_endpoint_mismatch"),
        ("cycle", "lp_builds_towards_cycle"),
        ("identity", "lp_identity_mismatch"),
    ],
)
def test_graph_rejects_invalid_lp_independently(
    accepted_state: AppState, mutation: str, code: str
) -> None:
    """Reject one LP defect without changing hierarchy or accepted source records."""
    package = accepted_state.catalog_load_result.package_runtimes[0].loaded_package
    base = next(e for e in package.relationships if e.label == "buildsTowards")
    if mutation == "count":
        counts = package.manifest.counts.model_copy(
            update={"builds_towards_relationships": 0}
        )
        altered = package.model_copy(
            update={"manifest": package.manifest.model_copy(update={"counts": counts})}
        )
    elif mutation == "duplicate":
        altered = package.model_copy(
            update={"relationships": (*package.relationships, base)}
        )
    elif mutation == "endpoint":
        replacement = base.model_copy(
            update={"source_node_id": package.framework_root.node_id}
        )
        altered = package.model_copy(
            update={
                "relationships": tuple(
                    replacement if e is base else e for e in package.relationships
                )
            }
        )
    elif mutation == "identity":
        replacement = base.model_copy(update={"property_identifier": "foreign"})
        altered = package.model_copy(
            update={
                "relationships": tuple(
                    replacement if e is base else e for e in package.relationships
                )
            }
        )
    else:
        first, second, third = package.item_nodes[:3]
        cycle = tuple(
            base.model_copy(
                update={
                    "relationship_id": f"cycle{i}",
                    "property_identifier": f"cycle{i}",
                    "source_node_id": source.node_id,
                    "target_node_id": target.node_id,
                    "source_entity_value": source.case_identifier_uuid,
                    "target_entity_value": target.case_identifier_uuid,
                }
            )
            for i, (source, target) in enumerate(
                [(first, second), (second, third), (third, first)]
            )
        )
        altered = package.model_copy(
            update={
                "relationships": tuple(
                    e for e in package.relationships if e.label != "buildsTowards"
                )
                + cycle
            }
        )
    findings = validate_learning_progression_graph(altered)
    assert code in {finding.code for finding in findings}
    assert not any("has_child" in finding.code for finding in findings)
    assert validate_learning_progression_graph(package) == ()


@pytest.mark.parametrize(
    "logical,data",
    [("learningProgressionSummary", b"{}"), ("learningProgressionProvenance", b"{}")],
)
def test_evidence_rejects_missing_required_content(
    accepted_state: AppState, logical: str, data: bytes
) -> None:
    """Reject malformed required summary and absent original provenance membership."""
    package = accepted_state.catalog_load_result.package_runtimes[0].loaded_package
    captured = {
        str(ref.logical_name): ref.resolved_path.read_bytes()
        for ref in package.artifacts
    }
    captured[logical] = data
    projection, findings = validate_learning_progression_evidence(
        captured_contents=captured, package=package
    )
    assert projection is None and findings
    assert all(finding.code.startswith("lp_") for finding in findings)


@pytest.mark.parametrize("data", [b'{"a":1,"a":2}', b'{"a":1e9999}'])
def test_source_json_is_strict(data: bytes) -> None:
    """Reject duplicate members and nonfinite numeric evidence before normalization."""
    with pytest.raises(ManifestBuildError):
        read_json_object(data=data, label="isolated negative evidence")


def test_strict_integer_properties() -> None:
    """Generate bounded field/value mutations for one strict finite-integer property."""
    cases: list[tuple[Any, dict[str, Any], dict[str, int]]] = [
        (
            TraverseLearningProgressionsRequest,
            {"framework_id": "synthetic", "identifier": selector("a")},
            {"max_depth": 12, "max_nodes": 250, "max_edges": 100},
        ),
        (
            GetLearningProgressionPathsRequest,
            {
                "framework_id": "synthetic",
                "source_identifier": selector("a"),
                "target_identifier": selector("t"),
            },
            {"max_depth": 12, "max_paths": 20},
        ),
        (
            SearchLearningProgressionsRequest,
            {"framework_id": "synthetic"},
            {"limit": 100},
        ),
    ]
    for model, base, bounds in cases:
        for field, maximum in bounds.items():
            for bad in [True, False, 0, maximum + 1, 1.0, "1"]:
                with pytest.raises(ValidationError) as failure:
                    model.model_validate({**base, field: bad})
                assert any(error["loc"] == (field,) for error in failure.value.errors())
            assert (
                getattr(model.model_validate({**base, field: maximum}), field)
                == maximum
            )


def test_closed_enum_property() -> None:
    """Closed LP labels/scopes never admit hierarchy or arbitrary directions."""
    updates: list[dict[str, Any]] = [
        {"relationship_types": ("hasChild",)},
        {"endpoint_scope": "ancestors"},
    ]
    for update in updates:
        with pytest.raises(ValidationError):
            SearchLearningProgressionsRequest.model_validate(
                {"framework_id": "synthetic", **update}
            )
    with pytest.raises(ValidationError):
        TraverseLearningProgressionsRequest.model_validate(
            {
                "framework_id": "synthetic",
                "identifier": selector("a"),
                "direction": "both",
            }
        )


def test_array_ceiling_property() -> None:
    """All facet arrays and exact selectors have finite public schema bounds."""
    for field in [
        "local_grade_labels",
        "normalized_grades",
        "statement_types",
        "normalized_statement_types",
    ]:
        with pytest.raises(ValidationError):
            SearchLearningProgressionsRequest.model_validate(
                {"framework_id": "synthetic", field: [str(i) for i in range(33)]}
            )
    with pytest.raises(ValidationError):
        SearchLearningProgressionsRequest(
            framework_id="synthetic",
            standard_identifiers=tuple(selector(str(i)) for i in range(21)),
        )


def test_cursor_text_ceiling() -> None:
    """Reject oversized cursor text before decoding or scanning candidates."""
    with pytest.raises(ValidationError):
        SearchLearningProgressionsRequest(framework_id="synthetic", cursor="a" * 4097)


def test_approved_request_defaults() -> None:
    """Default requests retain the contract's finite route-independent ceilings."""
    walk = TraverseLearningProgressionsRequest(
        framework_id="synthetic", identifier=selector("a")
    )
    path = GetLearningProgressionPathsRequest(
        framework_id="synthetic",
        source_identifier=selector("a"),
        target_identifier=selector("t"),
    )
    assert (walk.max_depth, walk.max_nodes, walk.max_edges, walk.direction) == (
        8,
        100,
        100,
        "downstream",
    )
    assert (path.max_depth, path.max_paths) == (6, 3)
    assert SearchLearningProgressionsRequest(framework_id="synthetic").limit == 25


def test_copied_package_checksum_rejected(
    accepted_state: AppState, tmp_path: Any
) -> None:
    """Reject changed declared LP bytes in an isolated copy without persistence."""
    # Standard Library
    import shutil

    # Package Library
    from kgfegmcp.domain.enums import InvalidPackagePolicy
    from kgfegmcp.packages.loader import GraphPackageLoader
    from kgfegmcp.packages.repository import GraphPackageRepository
    from kgfegmcp.packages.validator import GraphPackageValidator
    from kgfegmcp.profiles.repository import ProfileRepository

    package = accepted_state.catalog_load_result.package_runtimes[0].loaded_package
    destination = (
        tmp_path
        / str(package.manifest.framework_id)
        / str(package.manifest.snapshot_id)
    )
    shutil.copytree(package.package_root, destination)
    reference = package.artifact("learningProgressionSummary")
    assert reference
    (destination / str(reference.package_path)).write_bytes(b"{}")
    repository = GraphPackageRepository(graph_packages_root=tmp_path)
    loader = GraphPackageLoader(
        profile_repository=ProfileRepository(
            profile_root=accepted_state.settings.profile_root
        ),
        repository=repository,
    )
    validator = GraphPackageValidator(loader=loader, repository=repository)
    candidate = repository.candidate(
        framework_id=package.manifest.framework_id,
        snapshot_id=package.manifest.snapshot_id,
    )
    outcome = validator.validate_candidate(
        candidate=candidate,
        invalid_package_policy=InvalidPackagePolicy.FAIL,
        read_only=True,
    )
    result = outcome.result
    assert not result.is_valid and not result.persisted
    assert any("checksum" in finding.code for finding in result.findings)
