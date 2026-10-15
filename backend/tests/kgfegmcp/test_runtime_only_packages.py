"""Runtime-only (manifest 1.2) packages served from committed runtime files alone.

These scenarios need no archive: they read the seven accepted packages, isolated copies
of them, or the runtime tier directly, and cover the declared runtime set, manifest
rules, runtime-tier rejections, startup without archived evidence, and slim entity
provenance resources.
"""

# Standard Library
import builtins
import json
import os
import shutil

from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace
from typing import Any, cast

# Third Party Library
import pytest

# Package Library
from kgfegmcp.bootstrap import AppState, bootstrap_application
from kgfegmcp.domain.enums import InvalidPackagePolicy
from kgfegmcp.errors import ResourceAccessDeniedError
from kgfegmcp.packages.loader import GraphPackageLoader
from kgfegmcp.packages.lp_runtime import validate_runtime_evidence
from kgfegmcp.packages.models import LoadedGraphPackage
from kgfegmcp.packages.repository import GraphPackageRepository
from kgfegmcp.packages.validator import GraphPackageValidator
from kgfegmcp.profiles.repository import ProfileRepository
from kgfegmcp.resources.repository import ResourceRepository
from kgfegmcp.resources.service import ResourceService
from tests.fixtures.evidence_fixtures import canonical_json, shard_number
from tests.fixtures.progression_fixtures import package_route as route

INDEX_PATH = "slim/lp_relationship_provenance_index.json"
RECORD_PATH = "evidence/evidence_archive_record.json"
ARCHIVE_ONLY_NAMES = frozenset(
    {
        "academicStandardsBundle",
        "learningComponentsBundle",
        "learningProgressionBuildsTowards",
        "learningProgressionFinalClaims",
        "learningProgressionProvenance",
        "learningProgressionRelatesTo",
        "relationshipsHasChild",
        "standardsFrameworkItems",
    }
)
# Interfaces 1 runtime set: logical name to package path (delivery paths vary).
RUNTIME_PATHS: dict[str, str | None] = {
    "entityProvenance": "slim/as_entity_provenance.json",
    "evidenceArchiveRecord": "evidence/evidence_archive_record.json",
    "learningComponentDedupGroups": "detailed/lc_dedup_groups.json",
    "learningComponentProvenance": "slim/lc_entity_provenance.json",
    "learningComponentSummary": "detailed/lc_generation_summary.json",
    "learningProgressionNormalization": "detailed/lp_normalization_receipt.json",
    "learningProgressionProvenanceIndex": "slim/lp_relationship_provenance_index.json",
    "learningProgressionSummary": "detailed/lp_generation_summary.json",
    "learningProgressionUnresolved": "detailed/lp_unresolved_items.json",
    "learningProgressionValidation": "detailed/lp_validation_report.json",
    "nodes": None,
    "relationships": None,
    "standardsFramework": "detailed/as_standards_framework.json",
    "unresolvedItems": "detailed/as_unresolved_items.json",
    "validationReport": "detailed/as_lc_validation_report.json",
    **{
        f"learningProgressionProvenanceShard{n:02d}": (
            f"slim/lp_relationship_provenance_shard_{n:02d}.json"
        )
        for n in range(64)
    },
}


# Helpers.
def _copy_package(*, package: LoadedGraphPackage, root: Path) -> Path:
    """Copy one accepted package into an isolated graph-package root.

    Parameters
    ----------
    package
        Accepted loaded package.
    root
        Isolated graph-package root.

    Returns
    -------
    Path
        Copied snapshot directory.
    """

    destination = (
        root / str(package.manifest.framework_id) / str(package.manifest.snapshot_id)
    )
    shutil.copytree(package.package_root, destination)
    return destination


def _declared(manifest: dict[str, object]) -> dict[str, str]:
    """Flatten a manifest's dedicated and additional artifact declarations.

    Parameters
    ----------
    manifest
        Parsed manifest JSON.

    Returns
    -------
    dict[str, str]
        Package path by logical name.
    """

    artifacts = cast(dict[str, object], manifest["artifacts"])
    declared = {
        name: value for name, value in artifacts.items() if isinstance(value, str)
    }
    declared.update(cast(dict[str, str], artifacts.get("additionalArtifacts") or {}))
    return declared


def _keys(value: object) -> set[str]:
    """Collect every object key in a JSON value, at any depth.

    Parameters
    ----------
    value
        Parsed JSON value.

    Returns
    -------
    set[str]
        All keys.
    """

    if isinstance(value, dict):
        return set(value) | {key for item in value.values() for key in _keys(item)}

    if isinstance(value, list):
        return {key for item in value for key in _keys(item)}

    return set()


def _read_json(path: Path) -> dict[str, Any]:
    """Parse one JSON object file.

    Parameters
    ----------
    path
        JSON file.

    Returns
    -------
    dict[str, Any]
        Parsed object.
    """

    return cast(dict[str, Any], json.loads(path.read_bytes()))


def _validator(*, root: Path, state: AppState) -> GraphPackageValidator:
    """Construct a runtime-tier validator over an isolated graph-package root.

    Parameters
    ----------
    root
        Isolated graph-package root.
    state
        Accepted application state supplying the profile root.

    Returns
    -------
    GraphPackageValidator
        Validator without an evidence verifier, as startup loads packages.
    """

    repository = GraphPackageRepository(graph_packages_root=root)
    loader = GraphPackageLoader(
        profile_repository=ProfileRepository(profile_root=state.settings.profile_root),
        repository=repository,
    )
    return GraphPackageValidator(loader=loader, repository=repository)


# Scenarios.
def test_accepted_manifests_declare_only_runtime_files(
    accepted_state: AppState,
) -> None:
    """Each accepted manifest is 1.2 and declares exactly the runtime set.

    Parameters
    ----------
    accepted_state
        Application state bootstrapped from the seven accepted packages.
    """

    runtimes = accepted_state.catalog_load_result.package_runtimes
    assert len(runtimes) == 7

    for runtime in runtimes:
        package = runtime.loaded_package
        manifest = _read_json(package.manifest_path)
        declared = _declared(manifest)
        record = _read_json(package.package_root / RECORD_PATH)
        archived = {
            name
            for name, entry in record["evidenceArtifacts"].items()
            if entry["runtime"] is False
        }
        assert manifest["manifestVersion"] == "1.2"
        assert manifest["validation"]["status"] == "passed"
        assert set(declared) == set(RUNTIME_PATHS)
        assert all(
            path is None or declared[name] == path
            for name, path in RUNTIME_PATHS.items()
        )
        assert declared["nodes"].startswith("delivery/")
        assert declared["relationships"].startswith("delivery/")
        assert not _keys(manifest) & ARCHIVE_ONLY_NAMES
        assert ARCHIVE_ONLY_NAMES <= archived


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("manifest-version", "manifest_version_unsupported"),
        ("archive-only-null-field", "manifest_invalid"),
        ("archive-only-additional", "manifest_invalid"),
        ("record-undeclared", "manifest_invalid"),
    ],
)
def test_manifest_rejects_retired_contracts(
    accepted_state: AppState, code: str, mutation: str, tmp_path: Path
) -> None:
    """Version 1.1, archive-only declarations and a missing record are rejected.

    Parameters
    ----------
    accepted_state
        Application state bootstrapped from the seven accepted packages.
    code
        Blocking finding the loader must report.
    mutation
        Manifest change applied to an isolated copy.
    tmp_path
        Per-test temporary directory used as the graph-package root.
    """

    package = accepted_state.catalog_load_result.package_runtimes[0].loaded_package
    manifest = _read_json(package.manifest_path)
    artifacts = manifest["artifacts"]

    if mutation == "manifest-version":
        manifest["manifestVersion"] = "1.1"
    elif mutation == "archive-only-null-field":
        artifacts["learningProgressionFinalClaims"] = None
    elif mutation == "archive-only-additional":
        artifacts["additionalArtifacts"][
            "standardsFrameworkItems"
        ] = "additional/as_standards_framework_items.jsonl"
    else:
        del artifacts["additionalArtifacts"]["evidenceArchiveRecord"]

    destination = (
        tmp_path
        / str(package.manifest.framework_id)
        / str(package.manifest.snapshot_id)
    )
    destination.mkdir(parents=True)
    (destination / "package_manifest.json").write_text(
        json.dumps(manifest), encoding="utf-8"
    )
    validator = _validator(root=tmp_path, state=accepted_state)
    outcome = validator.validate_candidate(
        candidate=validator.repository.candidate(
            framework_id=package.manifest.framework_id,
            snapshot_id=package.manifest.snapshot_id,
        ),
        invalid_package_policy=InvalidPackagePolicy.FAIL,
        read_only=True,
    )
    assert not outcome.result.is_valid and outcome.loaded_package is None
    assert code in {finding.code for finding in outcome.result.findings}


def test_runtime_tier_never_reads_archived_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Startup under ``fail`` serves all seven packages without touching input sets.

    Parameters
    ----------
    monkeypatch
        Pytest monkeypatch fixture.
    """

    archive_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))),
        "data",
        "input_artifacts",
    )

    def guarded(original: Callable[..., Any]) -> Callable[..., Any]:
        """Wrap a filesystem entry point to fail on any input-set path."""

        def wrapper(path: Any, *args: Any, **kwargs: Any) -> Any:
            """Reject an input-set path, then delegate."""
            if isinstance(path, (str, os.PathLike)) and os.path.abspath(
                os.fspath(path)
            ).startswith(archive_root + os.sep):
                pytest.fail(f"Runtime loading touched archived evidence: {path}")
            return original(path, *args, **kwargs)

        return wrapper

    for owner, name in (
        (builtins, "open"),
        (os, "open"),
        (os, "stat"),
        (Path, "exists"),
        (Path, "is_file"),
        (Path, "open"),
        (Path, "read_bytes"),
        (Path, "stat"),
    ):
        monkeypatch.setattr(owner, name, guarded(getattr(owner, name)))

    monkeypatch.setenv("KGFEGMCP_INVALID_PACKAGE_POLICY", "fail")
    state = bootstrap_application()
    result = state.catalog_load_result
    assert len(result.package_runtimes) == 7
    assert {
        r.loaded_package.manifest.manifest_version for r in result.package_runtimes
    } == {"1.2"}
    assert all(
        r.loaded_package.learning_progression_evidence for r in result.package_runtimes
    )


@pytest.mark.parametrize(
    "mutation,code",
    [
        ("reinstated-field", "lp_slim_record_shape"),
        ("decision", "lp_slim_record_mismatch"),
        ("record-runtime", "evidence_record_runtime_mismatch"),
        ("record-key", "runtime_evidence_shape"),
    ],
)
def test_runtime_tier_rejects_inconsistent_slim_evidence(
    accepted_state: AppState, code: str, mutation: str
) -> None:
    """The runtime tier rejects slim records or records that disagree with delivery.

    Parameters
    ----------
    accepted_state
        Application state bootstrapped from the seven accepted packages.
    code
        Blocking finding the runtime tier must report.
    mutation
        Change applied to loader-verified bytes before the runtime tier runs.
    """

    package = accepted_state.catalog_load_result.package_runtimes[0].loaded_package
    captured = {
        str(reference.logical_name): reference.resolved_path.read_bytes()
        for reference in package.artifacts
    }
    control = validate_runtime_evidence(captured_contents=captured, package=package)
    assert not control.findings
    assert control.evidence == package.learning_progression_evidence

    edge = next(e for e in package.relationships if e.label == "buildsTowards")
    shard_name = (
        f"learningProgressionProvenanceShard{shard_number(edge.relationship_id):02d}"
    )
    shard = json.loads(captured[shard_name])
    claim = shard[edge.relationship_id]["claim"]

    if mutation == "reinstated-field":
        claim["candidate"]["evidence"] = []
        captured[shard_name] = canonical_json(shard)
    elif mutation == "decision":
        claim["judgment"]["decision"] = "relatesTo"
        captured[shard_name] = canonical_json(shard)
    elif mutation == "record-runtime":
        record = json.loads(captured["evidenceArchiveRecord"])
        record["evidenceArtifacts"]["learningProgressionFinalClaims"]["runtime"] = True
        captured["evidenceArchiveRecord"] = canonical_json(record)
    else:
        # A malformed logical-name key is a structured finding, not an exception.
        record = json.loads(captured["evidenceArchiveRecord"])
        entries = record["evidenceArtifacts"]
        entries["bad key"] = entries["learningProgressionFinalClaims"]
        captured["evidenceArchiveRecord"] = canonical_json(record)

    result = validate_runtime_evidence(captured_contents=captured, package=package)
    assert result.evidence is None
    assert [finding.code for finding in result.findings] == [code]


@pytest.mark.parametrize(
    "mutation,codes",
    [
        ("missing", {"artifact_missing", "package_declared_file_missing"}),
        ("extra", {"package_undeclared_file"}),
    ],
)
def test_runtime_tier_rejects_missing_and_extra_files(
    accepted_state: AppState, codes: set[str], mutation: str, tmp_path: Path
) -> None:
    """Runtime revalidation still rejects a missing or an extra runtime file.

    Parameters
    ----------
    accepted_state
        Application state bootstrapped from the seven accepted packages.
    codes
        Blocking findings the loader must report.
    mutation
        File change applied to an isolated package copy.
    tmp_path
        Per-test temporary directory used as the graph-package root.
    """

    package = accepted_state.catalog_load_result.package_runtimes[0].loaded_package
    destination = _copy_package(package=package, root=tmp_path)

    if mutation == "missing":
        (destination / "slim" / "lp_relationship_provenance_shard_00.json").unlink()
    else:
        # An archive-only file restored into the package tree is undeclared there.
        (destination / "detailed" / "lp_final_claims.json").write_bytes(b"{}")

    validator = _validator(root=tmp_path, state=accepted_state)
    outcome = validator.validate_candidate(
        candidate=validator.repository.candidate(
            framework_id=package.manifest.framework_id,
            snapshot_id=package.manifest.snapshot_id,
        ),
        invalid_package_policy=InvalidPackagePolicy.FAIL,
        read_only=True,
    )
    assert not outcome.result.is_valid and not outcome.result.persisted
    assert codes <= {finding.code for finding in outcome.result.findings}


@pytest.mark.parametrize(
    "kind,denied_right",
    [
        ("standard", "allow_full_text"),
        ("learning-component", "allow_standard_resources"),
    ],
)
def test_slim_entity_provenance_denies_before_reads(
    accepted_state: AppState,
    denied_right: str,
    kind: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Standard and component provenance refuse denied rights before any read.

    Parameters
    ----------
    accepted_state
        Application state bootstrapped from the seven accepted packages.
    denied_right
        Rights flag switched off for the package.
    kind
        Provenance resource family requested.
    monkeypatch
        Pytest monkeypatch fixture.
    """

    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    rights = runtime.catalog_package.rights.model_copy(update={denied_right: False})
    denied = SimpleNamespace(
        catalog_package=runtime.catalog_package.model_copy(update={"rights": rights}),
        graph_store=runtime.graph_store,
        loaded_package=runtime.loaded_package,
    )

    def reject(*_args: Any, **_kwargs: Any) -> None:
        """Fail if a denied request reads an artifact."""
        pytest.fail("Denied provenance attempted an artifact read")

    monkeypatch.setattr(ResourceService, "_package_runtime", lambda *_a, **_k: denied)
    monkeypatch.setattr(ResourceRepository, "read_artifact", reject)
    service = accepted_state.resource_service
    package = runtime.loaded_package

    with pytest.raises(ResourceAccessDeniedError):
        if kind == "standard":
            service.standard_provenance(
                **route(runtime), node_id=package.item_nodes[0].node_id
            )
        else:
            service.learning_component_provenance(
                **route(runtime), node_id=package.learning_component_nodes[0].node_id
            )


@pytest.mark.parametrize("kind", ["standard", "learning-component"])
def test_slim_entity_provenance_serves_attributed_entries(
    accepted_state: AppState, kind: str
) -> None:
    """Every entity has one slim entry, served with attribution and archive hashes.

    Parameters
    ----------
    accepted_state
        Application state bootstrapped from the seven accepted packages.
    kind
        Provenance resource family checked.
    """

    service = accepted_state.resource_service

    for runtime in accepted_state.catalog_load_result.package_runtimes:
        package = runtime.loaded_package
        record_reference = package.artifact("evidenceArchiveRecord")
        assert record_reference
        record = _read_json(record_reference.resolved_path)
        logical = (
            "entityProvenance" if kind == "standard" else "learningComponentProvenance"
        )
        reference = package.artifact(logical)
        assert reference
        document = _read_json(reference.resolved_path)

        # Standards are keyed by CASE UUID, components by outer node ID.
        if kind == "standard":
            entries = document["items"]
            node_ids = {
                str(node.case_identifier_uuid): node.node_id
                for node in package.item_nodes
                if node.case_identifier_uuid is not None
            }
        else:
            entries = document["learning_components"]
            node_ids = {
                str(node.node_id): node.node_id
                for node in package.learning_component_nodes
            }

        # Coverage is exact, and the archived identity is the record's original.
        assert set(entries) == set(node_ids)
        archived = record["evidenceArtifacts"][logical]
        assert (
            archived["runtime"] is False
            and archived["sha256"] == document["originalSha256"]
        )

        for key in sorted(node_ids)[:: max(1, len(node_ids) // 4)]:
            if kind == "standard":
                result = service.standard_provenance(
                    **route(runtime), node_id=node_ids[key]
                )
            else:
                result = service.learning_component_provenance(
                    **route(runtime), node_id=node_ids[key]
                )
            payload = json.loads(result.content)
            assert payload["provenance"] == entries[key]
            assert "candidate_source_refs" not in payload["provenance"]
            assert payload["sourceDocument"] == document["sourceDocument"]
            assert (
                payload["attributionStatement"]
                == package.manifest.rights.attribution_statement
            )
            assert payload["archivedProvenanceSha256"] == archived["sha256"]
            assert [
                (source.logical_name, source.sha256)
                for source in result.metadata.source_artifacts
            ] == [
                (logical, reference.sha256),
                ("evidenceArchiveRecord", record_reference.sha256),
            ]


def test_slim_shards_cover_every_lp_edge(accepted_state: AppState) -> None:
    """Each LP edge resolves through the index to one slim record in a bounded shard.

    Parameters
    ----------
    accepted_state
        Application state bootstrapped from the seven accepted packages.
    """

    limit = accepted_state.settings.max_resource_source_bytes

    for runtime in accepted_state.catalog_load_result.package_runtimes:
        package = runtime.loaded_package
        index = _read_json(package.package_root / INDEX_PATH)
        located: dict[str, str] = {}

        for name, partition in index["partitions"].items():
            reference = package.artifact(name)
            assert reference and reference.sha256 == partition["sha256"]
            assert str(reference.package_path) == partition["artifactPath"]
            assert reference.size_bytes <= limit
            shard = _read_json(reference.resolved_path)
            assert len(shard) == partition["entryCount"]

            for identifier in shard:
                assert identifier not in located and name.endswith(
                    f"{shard_number(identifier):02d}"
                )
                located[identifier] = name

        assert set(located) == {
            str(edge.relationship_id)
            for edge in package.relationships
            if edge.label in {"buildsTowards", "relatesTo"}
        }
