"""This module contains functionalities for building or dry-running deterministic
pending graph-package manifests.
"""

# Future Library
from __future__ import annotations

# Standard Library
import argparse
import json
import sys

from collections.abc import Sequence
from pathlib import Path

# Third Party Library
from pydantic import ValidationError

# Package Library
from kgfegmcp.config import BackendSettings, load_settings
from kgfegmcp.errors import KGFEGMCPError, ManifestBuildError
from kgfegmcp.packages.builder import build_graph_package
from kgfegmcp.packages.models import (
    PackageBuildResult,
    PackageBuildSpec,
    SnapshotRelation,
)


def _build_parser() -> argparse.ArgumentParser:
    """Create the manifest-build command-line parser.

    Returns
    -------
    argparse.ArgumentParser
        Parser supporting JSON build specifications and explicit build inputs.
    """

    parser = argparse.ArgumentParser(
        description=(
            "Construct a deterministic pending graph package from a selected profile "
            "and accepted as_* artifacts."
        )
    )
    parser.add_argument(
        "--additional-artifact",
        action="append",
        default=[],
        help=(
            "Explicit nonstandard artifact as LOGICAL_NAME=PATH. Repeat for each "
            "artifact."
        ),
        metavar="NAME=PATH",
    )
    parser.add_argument(
        "--detailed-artifact",
        action="append",
        default=[],
        help="Explicit recognized detailed as_* artifact. Repeat as needed.",
        metavar="PATH",
    )
    parser.add_argument(
        "--detailed-root",
        "--detailed-artifacts-directory",
        dest="detailed_artifacts_directory",
        help="Directory from which only recognized detailed as_* artifacts are used.",
        metavar="PATH",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Display the proposed manifest and output paths without writing files.",
    )
    parser.add_argument(
        "--jurisdiction-type",
        help="Operator-approved jurisdiction type for framework metadata.",
    )
    parser.add_argument(
        "--nodes",
        help="Accepted canonical as_nodes_XXX.jsonl artifact.",
        metavar="PATH",
    )
    parser.add_argument(
        "--output-root",
        help="Graph-packages output root.",
        metavar="PATH",
    )
    parser.add_argument(
        "--profile-id",
        help="Selected versioned curriculum profile identifier.",
    )
    parser.add_argument(
        "--profile-version",
        help="Selected immutable curriculum profile version.",
    )
    parser.add_argument(
        "--project-dir",
        help="Repository root used to resolve project-relative paths.",
        metavar="PATH",
    )
    parser.add_argument(
        "--relationships",
        help="Accepted canonical as_relationships_XXX.jsonl artifact.",
        metavar="PATH",
    )
    parser.add_argument(
        "--snapshot-relation",
        action="append",
        default=[],
        help=(
            "Operator-approved SnapshotRelation JSON object. Repeat for each relation."
        ),
        metavar="JSON",
    )
    parser.add_argument(
        "--source-document",
        help="Optional source document whose exact-byte checksum is recorded.",
        metavar="PATH",
    )
    parser.add_argument(
        "--source-publication-date",
        help="Optional authoritative source publication date in YYYY-MM-DD form.",
    )
    parser.add_argument(
        "--spec",
        help="Path to one PackageBuildSpec JSON document.",
        metavar="PATH",
    )
    parser.add_argument(
        "--version-token",
        help="Authoritative immutable snapshot version token.",
    )
    return parser


def _build_explicit_spec(namespace: argparse.Namespace) -> PackageBuildSpec:
    """Build and validate a specification from explicit CLI values.

    Parameters
    ----------
    namespace
        Parsed command-line namespace.

    Returns
    -------
    PackageBuildSpec
        Validated operator build specification.

    Raises
    ------
    ManifestBuildError
        If an additional artifact or snapshot relation is malformed.
    ValidationError
        If the established build specification rejects explicit values.
    """

    additional_artifacts = _parse_additional_artifacts(namespace.additional_artifact)
    snapshot_relations = _parse_snapshot_relations(namespace.snapshot_relation)
    values = {
        "additional_artifacts": additional_artifacts,
        "detailed_artifacts": tuple(
            Path(value) for value in namespace.detailed_artifact
        ),
        "detailed_artifacts_directory": (
            None
            if namespace.detailed_artifacts_directory is None
            else Path(namespace.detailed_artifacts_directory)
        ),
        "jurisdiction_type": namespace.jurisdiction_type,
        "nodes": None if namespace.nodes is None else Path(namespace.nodes),
        "output_root": (
            None if namespace.output_root is None else Path(namespace.output_root)
        ),
        "profile_id": namespace.profile_id,
        "profile_version": namespace.profile_version,
        "relationships": (
            None if namespace.relationships is None else Path(namespace.relationships)
        ),
        "snapshot_relations": snapshot_relations,
        "source_document": (
            None
            if namespace.source_document is None
            else Path(namespace.source_document)
        ),
        "source_publication_date": namespace.source_publication_date,
        "version_token": namespace.version_token,
    }
    return PackageBuildSpec.model_validate(values)


def _duplicate_key_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Construct one JSON object while rejecting duplicate member names.

    Parameters
    ----------
    pairs
        Source-ordered JSON object member pairs.

    Returns
    -------
    dict[str, object]
        Object preserving the final source order without duplicate keys.

    Raises
    ------
    ValueError
        If a JSON member name appears more than once.
    """

    result: dict[str, object] = {}

    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON member '{key}'.")

        result[key] = value

    return result


def _explicit_inputs_present(namespace: argparse.Namespace) -> bool:
    """Return whether any explicit build input accompanies a specification file.

    Parameters
    ----------
    namespace
        Parsed command-line namespace.

    Returns
    -------
    bool
        ``True`` when at least one non-specification build value was supplied.
    """

    scalar_names = (
        "detailed_artifacts_directory",
        "jurisdiction_type",
        "nodes",
        "output_root",
        "profile_id",
        "profile_version",
        "relationships",
        "source_document",
        "source_publication_date",
        "version_token",
    )
    return bool(
        namespace.additional_artifact
        or namespace.detailed_artifact
        or namespace.snapshot_relation
        or any(getattr(namespace, name) is not None for name in scalar_names)
    )


def _load_spec(path: Path) -> PackageBuildSpec:
    """Read one strict JSON build specification through the established model.

    Parameters
    ----------
    path
        Operator-supplied specification document.

    Returns
    -------
    PackageBuildSpec
        Validated package build specification.

    Raises
    ------
    ManifestBuildError
        If the document is unreadable, malformed, duplicated, or not a JSON object.
    ValidationError
        If the established build specification rejects the document.
    """

    try:
        payload = json.loads(
            object_pairs_hook=_duplicate_key_object,
            s=path.read_bytes(),
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, ValueError) as error:
        raise ManifestBuildError(
            details={"spec_path": str(path)},
            message=f"Build specification '{path.name}' is unreadable or malformed.",
        ) from error

    if not isinstance(payload, dict):
        raise ManifestBuildError(
            details={"spec_path": str(path)},
            message=f"Build specification '{path.name}' must contain one JSON object.",
        )

    return PackageBuildSpec.model_validate(payload)


def _parse_additional_artifacts(values: Sequence[str]) -> dict[str, Path]:
    """Parse repeated logical-name to path declarations without losing duplicates.

    Parameters
    ----------
    values
        Repeated ``LOGICAL_NAME=PATH`` command-line values.

    Returns
    -------
    dict[str, Path]
        Explicit additional artifact mapping.

    Raises
    ------
    ManifestBuildError
        If a declaration is malformed or a logical name is repeated case-insensitively.
    """

    artifacts: dict[str, Path] = {}
    normalized_names: set[str] = set()

    for value in values:
        logical_name, separator, raw_path = value.partition("=")
        normalized_name = logical_name.casefold()

        if not separator or not logical_name or not raw_path:
            raise ManifestBuildError(
                details={"additional_artifact": value},
                message=(
                    "Each additional artifact must use the form LOGICAL_NAME=PATH."
                ),
            )

        if normalized_name in normalized_names:
            raise ManifestBuildError(
                details={"logical_name": logical_name},
                message=(
                    "Additional artifact logical names must be case-insensitively "
                    "unique."
                ),
            )

        artifacts[logical_name] = Path(raw_path)
        normalized_names.add(normalized_name)

    return artifacts


def _parse_snapshot_relations(values: Sequence[str]) -> tuple[SnapshotRelation, ...]:
    """Parse repeated operator-approved snapshot relation JSON objects.

    Parameters
    ----------
    values
        Repeated JSON object strings matching the existing SnapshotRelation model.

    Returns
    -------
    tuple[SnapshotRelation, ...]
        Validated snapshot relation records in operator-supplied order.

    Raises
    ------
    ManifestBuildError
        If a relation is malformed or not a JSON object.
    ValidationError
        If the established SnapshotRelation contract rejects a value.
    """

    relations: list[SnapshotRelation] = []

    for index, value in enumerate(iterable=values, start=1):
        try:
            payload = json.loads(
                object_pairs_hook=_duplicate_key_object,
                s=value,
            )
        except (json.JSONDecodeError, ValueError) as error:
            raise ManifestBuildError(
                details={"relation_index": index},
                message=f"Snapshot relation {index} is malformed JSON.",
            ) from error

        if not isinstance(payload, dict):
            raise ManifestBuildError(
                details={"relation_index": index},
                message=f"Snapshot relation {index} must contain one JSON object.",
            )

        relations.append(SnapshotRelation.model_validate(payload))

    return tuple(relations)


def _render_result(result: PackageBuildResult) -> str:
    """Serialize a complete deterministic CLI build summary.

    Parameters
    ----------
    result
        Proposed, created, or existing-identical package result.

    Returns
    -------
    str
        Stable lower-camel-case JSON summary containing the full pending manifest.
    """

    payload = result.model_dump(by_alias=True, mode="json")
    return json.dumps(
        ensure_ascii=False,
        indent=2,
        obj=payload,
        sort_keys=True,
    )


def _render_validation_error(error: ValidationError) -> str:
    """Render Pydantic failures without echoing operator-supplied input values.

    Parameters
    ----------
    error
        Validation failure from an established repository contract.

    Returns
    -------
    str
        Concise field-location and validation-message summary.
    """

    messages = []

    for item in error.errors(include_input=False, include_url=False):
        location = ".".join(str(part) for part in item["loc"])
        messages.append(f"{location}: {item['msg']}")

    return "Build inputs are invalid: " + "; ".join(messages)


def _settings_for_namespace(namespace: argparse.Namespace) -> BackendSettings:
    """Load settings with an optional explicit repository-root override.

    Parameters
    ----------
    namespace
        Parsed command-line namespace.

    Returns
    -------
    BackendSettings
        Validated environment-backed repository settings.
    """

    if namespace.project_dir is None:
        return load_settings()

    project_dir = Path(namespace.project_dir).expanduser().resolve(strict=False)
    return BackendSettings(project_dir=project_dir)


def main(argv: Sequence[str] | None = None) -> int:
    """Execute one manifest build or dry-run command.

    Parameters
    ----------
    argv
        Optional argument sequence excluding the executable name.

    Returns
    -------
    int
        Process status code: zero for success and one for a typed build failure.
    """

    parser = _build_parser()
    namespace = parser.parse_args(args=argv)

    if namespace.spec is not None and _explicit_inputs_present(namespace):
        parser.error("--spec may not be combined with explicit build inputs.")

    if namespace.spec is None:
        required_names = (
            "jurisdiction_type",
            "nodes",
            "output_root",
            "profile_id",
            "profile_version",
            "relationships",
            "version_token",
        )
        missing_names = [
            name for name in required_names if getattr(namespace, name) is None
        ]

        if missing_names:
            options = ", ".join(f"--{name.replace('_', '-')}" for name in missing_names)
            parser.error(f"Missing required explicit inputs: {options}.")

    try:
        spec = (
            _load_spec(Path(namespace.spec))
            if namespace.spec is not None
            else _build_explicit_spec(namespace)
        )
        settings = _settings_for_namespace(namespace)
        result = build_graph_package(
            dry_run=namespace.dry_run,
            settings=settings,
            spec=spec,
        )
    except ValidationError as error:
        print(_render_validation_error(error), file=sys.stderr)
        return 1
    except KGFEGMCPError as error:
        payload = error.public_payload()
        print(
            json.dumps(
                ensure_ascii=False,
                indent=2,
                obj=payload,
                sort_keys=True,
            ),
            file=sys.stderr,
        )
        return 1

    print(_render_result(result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
