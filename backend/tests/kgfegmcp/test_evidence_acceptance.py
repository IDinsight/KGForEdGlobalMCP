"""Acceptance against archived full evidence, exercised without the real archive.

Each scenario runs the production builder, validator, evidence verifier or CLI on a
synthetic full-evidence input set (``tests/fixtures/evidence_fixtures.py``), so a plain
checkout covers the evidence tier: a passing package, missing, altered and unreadable
archives, slim artifacts that do not match their derivation, and archive verification.
"""

# Standard Library
import copy
import hashlib
import json

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import cast

# Third Party Library
import pytest

from typer.testing import CliRunner

# Package Library
from kgfegmcp.cli import validate_packages, verify_evidence_archive
from kgfegmcp.domain.enums import InvalidPackagePolicy
from kgfegmcp.errors import EvidenceArchiveUnavailableError
from kgfegmcp.packages import slim
from kgfegmcp.packages.evidence_models import FullEvidenceView
from kgfegmcp.packages.lp_validation import validate_learning_progression_evidence
from kgfegmcp.packages.models import DeclaredArtifactReference, LoadedGraphPackage
from tests.fixtures.evidence_fixtures import (
    SyntheticProject,
    build_synthetic_package,
    canonical_json,
    qualified_sha256,
    rebuild_synthetic_package,
    shard_number,
)

_RECORD_PATH = "evidence/evidence_archive_record.json"
_REMOVED_LP_FIELDS = (
    "claim.candidate.admissible_decisions",
    "claim.candidate.evidence",
    "claim.provenance.producer_judgment",
)


# Helpers.
def _cli_environment(
    *, monkeypatch: pytest.MonkeyPatch, project: SyntheticProject
) -> None:
    """Point CLI settings at a synthetic project and clear competing overrides.

    Parameters
    ----------
    monkeypatch
        Pytest monkeypatch fixture.
    project
        Synthetic project the CLI should use as its repository root.
    """

    for name in (
        "KGFEGMCP_CONFIG_ROOT",
        "KGFEGMCP_DATA_ROOT",
        "KGFEGMCP_GRAPH_PACKAGES_ROOT",
        "KGFEGMCP_INVALID_PACKAGE_POLICY",
        "KGFEGMCP_PROFILE_ROOT",
    ):
        monkeypatch.delenv(name, raising=False)

    monkeypatch.setenv("PATHS_PROJECT_DIR", str(project.project_dir))


def _faulty_lc(derived: dict[str, bytes]) -> dict[str, bytes]:
    """Emit learning-component provenance that is not JSON, as a broken build might.

    Parameters
    ----------
    derived
        Correct slim artifacts by logical name.

    Returns
    -------
    dict[str, bytes]
        Artifacts with a malformed slim LC document.
    """

    return {**derived, "learningComponentProvenance": b"not json\n"}


def _faulty_lp(derived: dict[str, bytes]) -> dict[str, bytes]:
    """Prefix one slim LP rationale and rebind the slim index to the changed shard.

    Parameters
    ----------
    derived
        Correct slim artifacts by logical name.

    Returns
    -------
    dict[str, bytes]
        Artifacts whose shard no longer matches the archived original record.
    """

    name, content = next(
        (name, content)
        for name, content in sorted(derived.items())
        if name.startswith("learningProgressionProvenanceShard") and content != b"{}\n"
    )
    shard = json.loads(content)
    record_id = min(shard)
    judgment = shard[record_id]["claim"]["judgment"]
    # Prepend, so the bounded rationale excerpt in the projection changes too.
    judgment["rationale"] = "Altered by a faulty build. " + judgment["rationale"]
    changed = canonical_json(shard)
    index = json.loads(derived["learningProgressionProvenanceIndex"])
    index["partitions"][name]["sha256"] = qualified_sha256(changed)
    return {
        **derived,
        name: changed,
        "learningProgressionProvenanceIndex": canonical_json(index),
    }


def _full_view(
    *, loaded: LoadedGraphPackage, project: SyntheticProject
) -> FullEvidenceView:
    """Assemble a full-evidence view from the record, as acceptance does.

    Parameters
    ----------
    loaded
        Runtime-tier loaded package.
    project
        Synthetic project holding the input set.

    Returns
    -------
    FullEvidenceView
        View in the full-evidence namespace with every file's bytes.
    """

    record = _read_json(project.package_dir / _RECORD_PATH)
    references: list[DeclaredArtifactReference] = []
    contents: dict[str, bytes] = {}

    for name, entry in sorted(
        cast(dict[str, dict[str, object]], record["evidenceArtifacts"]).items()
    ):
        path = (
            project.package_dir / str(entry["packagePath"])
            if entry["runtime"]
            else project.project_dir / str(entry["localPath"])
        )
        content = path.read_bytes()
        contents[name] = content
        references.append(
            DeclaredArtifactReference(
                logical_name=name,
                package_path=str(entry["packagePath"]),
                resolved_path=path,
                sha256=qualified_sha256(content),
                size_bytes=len(content),
            )
        )

    counts = loaded.manifest.counts
    return FullEvidenceView(
        artifacts=tuple(references),
        builds_towards_relationships=counts.builds_towards_relationships,
        contents=contents,
        framework_id=loaded.manifest.framework_id,
        framework_root=loaded.framework_root,
        included_graph_types=loaded.manifest.included_graph_types,
        item_nodes=loaded.item_nodes,
        relates_to_relationships=counts.relates_to_relationships,
        relationships=loaded.relationships,
    )


def _load_runtime_only(project: SyntheticProject) -> LoadedGraphPackage:
    """Load the synthetic package through the runtime tier only.

    Parameters
    ----------
    project
        Synthetic project.

    Returns
    -------
    LoadedGraphPackage
        Loaded package with runtime projections.
    """

    outcome = project.validator(evidence=False).validate_candidate(
        candidate=project.candidate(),
        invalid_package_policy=InvalidPackagePolicy.FAIL,
        read_only=True,
    )
    assert outcome.result.is_valid and outcome.loaded_package is not None
    return outcome.loaded_package


def _read_json(path: Path) -> dict[str, object]:
    """Parse one JSON object file.

    Parameters
    ----------
    path
        JSON file.

    Returns
    -------
    dict[str, object]
        Parsed object.
    """

    return cast(dict[str, object], json.loads(path.read_bytes()))


def _record_sha256(value: object) -> str:
    """Hash canonical JSON without a trailing newline, as the slim contract defines.

    Parameters
    ----------
    value
        Original JSON entry.

    Returns
    -------
    str
        Qualified ``sha256:<hex>`` digest.
    """

    text = json.dumps(
        allow_nan=False,
        ensure_ascii=False,
        obj=value,
        separators=(",", ":"),
        sort_keys=True,
    )
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _status(project: SyntheticProject) -> str:
    """Return the persisted validation status of the synthetic package.

    Parameters
    ----------
    project
        Synthetic project.

    Returns
    -------
    str
        Manifest ``validation.status``.
    """

    return str(cast(dict[str, object], project.manifest()["validation"])["status"])


# Scenarios.
def test_altered_archive_file_fails_acceptance(
    monkeypatch: pytest.MonkeyPatch, synthetic_project: SyntheticProject
) -> None:
    """An altered archive-only file is a blocking finding that fails the package.

    Parameters
    ----------
    monkeypatch
        Pytest monkeypatch fixture.
    synthetic_project
        Private synthetic project with a pending package.
    """

    _cli_environment(monkeypatch=monkeypatch, project=synthetic_project)
    bundle = synthetic_project.input_dir / "detailed" / "as_kg_bundle.json"
    bundle.write_bytes(bundle.read_bytes() + b" ")
    result = CliRunner().invoke(
        validate_packages.cli,
        [
            "one",
            "--framework-id",
            synthetic_project.framework_id,
            "--snapshot-id",
            synthetic_project.snapshot_id,
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 1 and payload["persisted"] is True
    assert [(f["code"], f["artifactName"]) for f in payload["findings"]] == [
        ("evidence_archive_checksum_mismatch", "academicStandardsBundle")
    ]
    assert _status(synthetic_project) == "failed"


def test_archive_verification_reports_each_entry(
    monkeypatch: pytest.MonkeyPatch, synthetic_project: SyntheticProject
) -> None:
    """The verify command reports ok, missing and mismatched entries and exits nonzero.

    Parameters
    ----------
    monkeypatch
        Pytest monkeypatch fixture.
    synthetic_project
        Private synthetic project with its restored input set.
    """

    _cli_environment(monkeypatch=monkeypatch, project=synthetic_project)
    arguments = [
        "one",
        "--framework-id",
        synthetic_project.framework_id,
        "--snapshot-id",
        synthetic_project.snapshot_id,
    ]
    complete = CliRunner().invoke(verify_evidence_archive.cli, arguments)
    (package,) = json.loads(complete.stdout)["packages"]
    assert complete.exit_code == 0 and package["status"] == "ok"
    assert package["counts"] == {"mismatch": 0, "missing": 0, "ok": 86}

    detailed = synthetic_project.input_dir / "detailed"
    (detailed / "lp_final_claims.json").unlink()
    shard = (
        synthetic_project.input_dir
        / "additional"
        / "lp_relationship_provenance_shard_10.json"
    )
    shard.write_bytes(shard.read_bytes() + b"\n")
    damaged = CliRunner().invoke(verify_evidence_archive.cli, arguments)
    report = json.loads(damaged.stdout)
    (package,) = report["packages"]
    statuses = {e["logicalName"]: e for e in package["entries"] if e["status"] != "ok"}
    assert (
        damaged.exit_code == 1 and report["archiveLocation"] == "IDinsight Google Drive"
    )
    assert package["counts"] == {"mismatch": 1, "missing": 1, "ok": 84}
    assert statuses["learningProgressionFinalClaims"]["status"] == "missing"
    assert statuses["learningProgressionFinalClaims"]["reason"] == "absent"
    assert statuses["learningProgressionProvenanceShard10"]["status"] == "mismatch"


def test_evidence_tier_accepts_synthetic_full_evidence(
    monkeypatch: pytest.MonkeyPatch, synthetic_project: SyntheticProject
) -> None:
    """Acceptance with complete, consistent evidence persists ``passed``.

    Parameters
    ----------
    monkeypatch
        Pytest monkeypatch fixture.
    synthetic_project
        Private synthetic project with a pending package.
    """

    _cli_environment(monkeypatch=monkeypatch, project=synthetic_project)
    assert _status(synthetic_project) == "pending"
    result = CliRunner().invoke(
        validate_packages.cli,
        [
            "one",
            "--framework-id",
            synthetic_project.framework_id,
            "--snapshot-id",
            synthetic_project.snapshot_id,
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 0 and payload["isValid"] is True
    assert payload["findings"] == [] and payload["persisted"] is True
    assert _status(synthetic_project) == "passed"


@pytest.mark.parametrize(
    "logical_name", ["learningProgressionProvenance", "learningProgressionSummary"]
)
def test_evidence_view_runs_full_lp_checks(
    logical_name: str, synthetic_template: SyntheticProject
) -> None:
    """The full LP checks run on the evidence view and reject malformed evidence.

    Parameters
    ----------
    logical_name
        Full-evidence artifact replaced by an empty JSON object.
    synthetic_template
        Pristine synthetic project; read only.
    """

    loaded = _load_runtime_only(synthetic_template)
    view = _full_view(loaded=loaded, project=synthetic_template)
    projection, findings = validate_learning_progression_evidence(view=view)
    assert not findings and projection == loaded.learning_progression_evidence

    broken = replace(view, contents={**view.contents, logical_name: b"{}"})
    projection, findings = validate_learning_progression_evidence(view=broken)
    assert projection is None and findings
    assert all(finding.code.startswith("lp_") for finding in findings)


@pytest.mark.parametrize(
    "mutate,expected",
    [
        (
            _faulty_lp,
            {
                ("slim_derivation_mismatch", "learningProgressionProvenanceIndex"),
                ("slim_projection_mismatch", None),
            },
        ),
        (
            _faulty_lc,
            {
                ("slim_derivation_mismatch", "learningComponentProvenance"),
                ("slim_entity_coverage_mismatch", "learningComponentProvenance"),
            },
        ),
    ],
    ids=["lp-shard", "lc-document"],
)
def test_faulty_slim_artifact_fails_acceptance(
    expected: set[tuple[str, str | None]],
    monkeypatch: pytest.MonkeyPatch,
    mutate: Callable[[dict[str, bytes]], dict[str, bytes]],
    synthetic_project: SyntheticProject,
) -> None:
    """A slim artifact that differs from its derivation passes runtime, fails acceptance.

    Parameters
    ----------
    expected
        Findings (code, artifact) that must be among the blocking findings.
    monkeypatch
        Pytest monkeypatch fixture.
    mutate
        Faulty-build transformation of the correct slim artifacts.
    synthetic_project
        Private synthetic project whose package is rebuilt by a faulty builder.
    """

    derive = slim.derive_slim_artifacts

    with monkeypatch.context() as patch:
        patch.setattr(
            "kgfegmcp.packages.builder.derive_slim_artifacts",
            lambda contents: mutate(derive(contents)),
        )
        faulty = rebuild_synthetic_package(project=synthetic_project)

    assert faulty.snapshot_id != synthetic_project.snapshot_id
    _load_runtime_only(faulty)

    outcome = faulty.validator(evidence=True).validate_candidate(
        candidate=faulty.candidate(),
        invalid_package_policy=InvalidPackagePolicy.FAIL,
        read_only=False,
    )
    findings = {(f.code, f.artifact_name) for f in outcome.result.findings}
    assert not outcome.result.is_valid and expected <= findings
    assert {code for code, _ in findings} <= {
        "slim_derivation_mismatch",
        "slim_entity_coverage_mismatch",
        "slim_projection_mismatch",
    }
    assert outcome.result.persisted and _status(faulty) == "failed"


def test_missing_archive_file_blocks_acceptance(
    monkeypatch: pytest.MonkeyPatch, synthetic_project: SyntheticProject
) -> None:
    """A missing archive-only file stops acceptance with no status transition.

    Parameters
    ----------
    monkeypatch
        Pytest monkeypatch fixture.
    synthetic_project
        Private synthetic project with a pending package.
    """

    _cli_environment(monkeypatch=monkeypatch, project=synthetic_project)
    (synthetic_project.input_dir / "detailed" / "lp_final_claims.json").unlink()
    result = CliRunner().invoke(
        validate_packages.cli,
        [
            "one",
            "--framework-id",
            synthetic_project.framework_id,
            "--snapshot-id",
            synthetic_project.snapshot_id,
        ],
    )
    assert result.exit_code == 2 and result.stdout == ""
    error = json.loads(result.stderr)
    assert error["code"] == "evidence_archive_unavailable"
    assert _status(synthetic_project) == "pending"


def test_pending_batch_skips_terminal_packages(
    synthetic_project: SyntheticProject,
) -> None:
    """Batch acceptance never needs a terminal package's archive.

    Parameters
    ----------
    synthetic_project
        Private synthetic project with a pending package.
    """

    validator = synthetic_project.validator(evidence=True)
    accepted = validator.validate_candidate(
        candidate=synthetic_project.candidate(),
        invalid_package_policy=InvalidPackagePolicy.FAIL,
        read_only=False,
    )
    assert accepted.result.is_valid and _status(synthetic_project) == "passed"

    (synthetic_project.input_dir / "detailed" / "lp_final_claims.json").unlink()
    outcomes = validator.validate_pending(
        invalid_package_policy=InvalidPackagePolicy.FAIL, read_only=False
    )
    assert outcomes == () and _status(synthetic_project) == "passed"


def test_pending_batch_stops_without_partial_transitions(
    synthetic_project: SyntheticProject,
) -> None:
    """An unavailable archive later in a batch leaves earlier packages pending.

    Parameters
    ----------
    synthetic_project
        Private synthetic project; a second pending package is built beside it.
    """

    second = build_synthetic_package(
        edges_per_type=1,
        input_set="synthetic_second",
        project_dir=synthetic_project.project_dir,
    )
    projects = {p.snapshot_id: p for p in (synthetic_project, second)}
    order = [c.snapshot_id for c in synthetic_project.repository().discover()]
    assert sorted(order) == sorted(projects)

    # The package validated first would pass; the later one lacks its archive.
    first, last = (projects[snapshot] for snapshot in order)
    (last.input_dir / "detailed" / "lp_final_claims.json").unlink()

    with pytest.raises(EvidenceArchiveUnavailableError):
        synthetic_project.validator(evidence=True).validate_pending(
            invalid_package_policy=InvalidPackagePolicy.FAIL, read_only=False
        )

    assert _status(first) == _status(last) == "pending"


def test_rebuild_reproduces_snapshot(synthetic_project: SyntheticProject) -> None:
    """The same spec and inputs rebuild the same snapshot ID and artifact bytes.

    Parameters
    ----------
    synthetic_project
        Private synthetic project whose package is rebuilt.
    """

    before = {
        path.relative_to(synthetic_project.package_dir): path.read_bytes()
        for path in synthetic_project.package_dir.rglob("*")
        if path.is_file()
    }
    manifest = synthetic_project.manifest()
    rebuilt = rebuild_synthetic_package(project=synthetic_project)
    after = {
        path.relative_to(rebuilt.package_dir): path.read_bytes()
        for path in rebuilt.package_dir.rglob("*")
        if path.is_file()
    }
    manifest_path = Path("package_manifest.json")
    assert rebuilt.snapshot_id == synthetic_project.snapshot_id
    assert {k: v for k, v in after.items() if k != manifest_path} == {
        k: v for k, v in before.items() if k != manifest_path
    }
    assert {k: v for k, v in rebuilt.manifest().items() if k != "createdAt"} == {
        k: v for k, v in manifest.items() if k != "createdAt"
    }


def test_record_binds_every_input_file(synthetic_template: SyntheticProject) -> None:
    """The archive record binds every full-evidence input by path, size and hash.

    Parameters
    ----------
    synthetic_template
        Pristine synthetic project; read only.
    """

    project = synthetic_template
    record = _read_json(project.package_dir / _RECORD_PATH)
    entries = cast(dict[str, dict[str, object]], record["evidenceArtifacts"])
    inputs = {
        str(path.relative_to(project.project_dir)): path.read_bytes()
        for path in project.input_dir.rglob("*")
        if path.is_file() and path.name != "package_build.json"
    }
    manifest = project.manifest()
    declared = cast(
        dict[str, str],
        cast(dict[str, object], manifest["artifacts"])["additionalArtifacts"],
    )
    declared |= {
        name: value
        for name, value in cast(dict[str, object], manifest["artifacts"]).items()
        if isinstance(value, str)
    }
    prefix = f"{project.input_dir.relative_to(project.project_dir)}/"

    assert record["archive"] == {"location": "IDinsight Google Drive"}
    assert (
        record["formatVersion"] == "1.0"
        and record["frameworkId"] == project.framework_id
    )
    assert {str(e["localPath"]) for e in entries.values()} == set(inputs)

    for name, entry in entries.items():
        content = inputs[str(entry["localPath"])]
        assert entry["sizeBytes"] == len(content)
        assert entry["sha256"] == qualified_sha256(content)
        assert entry["packagePath"] == str(entry["localPath"]).removeprefix(prefix)
        carried = (
            declared.get(name) == entry["packagePath"]
            and (project.package_dir / str(entry["packagePath"])).read_bytes()
            == content
        )
        assert entry["runtime"] is carried


def test_runtime_only_validation_needs_no_archive(
    monkeypatch: pytest.MonkeyPatch, synthetic_project: SyntheticProject
) -> None:
    """Runtime-only validation passes from runtime files alone and never persists.

    Parameters
    ----------
    monkeypatch
        Pytest monkeypatch fixture.
    synthetic_project
        Private synthetic project whose archive-only files are removed.
    """

    _cli_environment(monkeypatch=monkeypatch, project=synthetic_project)
    record = _read_json(synthetic_project.package_dir / _RECORD_PATH)

    for entry in cast(
        dict[str, dict[str, object]], record["evidenceArtifacts"]
    ).values():
        if not entry["runtime"]:
            (synthetic_project.project_dir / str(entry["localPath"])).unlink()

    result = CliRunner().invoke(
        validate_packages.cli,
        [
            "one",
            "--framework-id",
            synthetic_project.framework_id,
            "--runtime-only",
            "--snapshot-id",
            synthetic_project.snapshot_id,
        ],
    )
    payload = json.loads(result.stdout)
    assert result.exit_code == 0 and payload["isValid"] is True
    assert payload["persisted"] is False and _status(synthetic_project) == "pending"


@pytest.mark.parametrize(
    "kind", ["entity", "learning-component", "learning-progression"]
)
def test_slim_artifacts_follow_the_contract(
    kind: str, synthetic_template: SyntheticProject
) -> None:
    """Slim artifacts are the originals minus the named fields plus original hashes.

    Parameters
    ----------
    kind
        Slim artifact family checked against an independent oracle.
    synthetic_template
        Pristine synthetic project; read only.
    """

    project = synthetic_template
    detailed = project.input_dir / "detailed"
    package = project.package_dir

    def read_slim(path: str) -> dict[str, object]:
        """Parse one slim file and require canonical encoding."""
        content = (package / path).read_bytes()
        value = cast(dict[str, object], json.loads(content))
        assert content == canonical_json(value)
        return value

    if kind == "entity":
        original_bytes = (detailed / "as_entity_provenance.json").read_bytes()
        original = cast(dict[str, object], json.loads(original_bytes))
        expected_items = {
            key: {
                **{n: v for n, v in item.items() if n != "candidate_source_refs"},
                "original_item_sha256": _record_sha256(item),
            }
            for key, item in cast(
                dict[str, dict[str, object]], original["items"]
            ).items()
        }
        assert read_slim("slim/as_entity_provenance.json") == {
            "formatVersion": "1.0",
            "items": expected_items,
            "originalSha256": qualified_sha256(original_bytes),
            "removedItemFields": ["candidate_source_refs"],
            "sourceDocument": original["framework"],
        }
    elif kind == "learning-component":
        original_bytes = (detailed / "lc_entity_provenance.json").read_bytes()
        original = cast(dict[str, object], json.loads(original_bytes))
        components = cast(dict[str, dict[str, object]], original["learning_components"])
        assert read_slim("slim/lc_entity_provenance.json") == {
            "formatVersion": "1.0",
            "learning_components": {
                key: {
                    **component,
                    "original_component_sha256": _record_sha256(component),
                }
                for key, component in components.items()
            },
            "originalSha256": qualified_sha256(original_bytes),
            "sourceDocument": {
                "doc_key": original["doc_key"],
                "pdf_name": original["pdf_name"],
            },
        }
    else:
        map_bytes = (detailed / "lp_relationship_provenance.json").read_bytes()
        originals = cast(dict[str, dict[str, object]], json.loads(map_bytes))
        index = read_slim("slim/lp_relationship_provenance_index.json")
        partitions = cast(dict[str, dict[str, object]], index["partitions"])
        assert {k: v for k, v in index.items() if k != "partitions"} == {
            "formatVersion": "2.0",
            "originalProvenanceIndexSha256": qualified_sha256(
                (detailed / "lp_relationship_provenance_index.json").read_bytes()
            ),
            "originalProvenanceSha256": qualified_sha256(map_bytes),
            "partitionAlgorithm": "SHA256(UTF8(relationship_id))[0] modulo 64",
            "partitionCount": 64,
            "recordFormatVersion": "1.0",
            "removedFields": list(_REMOVED_LP_FIELDS),
        }

        for number in range(64):
            path = f"slim/lp_relationship_provenance_shard_{number:02d}.json"
            shard = read_slim(path)
            expected: dict[str, object] = {}

            for identifier, original in originals.items():
                if shard_number(identifier) != number:
                    continue

                record = copy.deepcopy(original)
                claim = cast(dict[str, dict[str, object]], record["claim"])
                del claim["candidate"]["admissible_decisions"]
                del claim["candidate"]["evidence"]
                del claim["provenance"]["producer_judgment"]
                record["original_entry_sha256"] = _record_sha256(original)
                expected[identifier] = record

            assert shard == expected
            assert partitions[f"learningProgressionProvenanceShard{number:02d}"] == {
                "artifactPath": path,
                "entryCount": len(expected),
                "sha256": qualified_sha256((package / path).read_bytes()),
            }
