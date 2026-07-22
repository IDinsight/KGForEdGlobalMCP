"""This module contains the entry point for building or dry-running deterministic
**pending** graph-package manifests.

Invoke from the backend directory with either a build specification:

    python -m kgfegmcp.cli.build_manifests --spec PATH

or explicit package inputs:

    python -m kgfegmcp.cli.build_manifests build \
        --profile-id PROFILE_ID \
        --profile-version PROFILE_VERSION \
        --version-token VERSION_TOKEN \
        --jurisdiction-type JURISDICTION_TYPE \
        --nodes PATH \
        --relationships PATH \
        --output-root PATH
"""

# Future Library
from __future__ import annotations

# Standard Library
import json

from collections.abc import Sequence
from pathlib import Path

# Third Party Library
import typer

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

cli = typer.Typer(
    help=(
        "Construct deterministic pending graph packages from selected profiles and "
        "accepted artifacts."
    ),
    no_args_is_help=True,
)


def _build_explicit_spec(
    *,
    additional_artifact: Sequence[str],
    detailed_artifact: Sequence[Path],
    detailed_artifacts_directory: Path | None,
    jurisdiction_type: str | None,
    nodes: Path | None,
    output_root: Path | None,
    profile_id: str | None,
    profile_version: str | None,
    relationships: Path | None,
    snapshot_relation: Sequence[str],
    source_document: Path | None,
    source_publication_date: str | None,
    version_token: str | None,
) -> PackageBuildSpec:
    """Build and validate a specification from explicit CLI values.

    Parameters
    ----------
    additional_artifact
        Repeated explicit nonstandard artifact declarations.
    detailed_artifact
        Repeated recognized detailed artifact paths.
    detailed_artifacts_directory
        Optional directory containing recognized detailed artifacts.
    jurisdiction_type
        Operator-approved jurisdiction type.
    nodes
        Accepted canonical node delivery artifact.
    output_root
        Graph-packages output root.
    profile_id
        Selected curriculum profile identifier.
    profile_version
        Selected curriculum profile version.
    relationships
        Accepted canonical relationship delivery artifact.
    snapshot_relation
        Repeated approved snapshot-relation JSON objects.
    source_document
        Optional source document whose checksum is recorded.
    source_publication_date
        Optional authoritative source publication date.
    version_token
        Authoritative immutable snapshot version token.

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

    values = {
        "additional_artifacts": _parse_additional_artifacts(additional_artifact),
        "detailed_artifacts": tuple(detailed_artifact),
        "detailed_artifacts_directory": detailed_artifacts_directory,
        "jurisdiction_type": jurisdiction_type,
        "nodes": nodes,
        "output_root": output_root,
        "profile_id": profile_id,
        "profile_version": profile_version,
        "relationships": relationships,
        "snapshot_relations": _parse_snapshot_relations(snapshot_relation),
        "source_document": source_document,
        "source_publication_date": source_publication_date,
        "version_token": version_token,
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
        Object preserving the source order without duplicate keys.

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


def _explicit_inputs_present(
    *,
    additional_artifact: Sequence[str],
    detailed_artifact: Sequence[Path],
    detailed_artifacts_directory: Path | None,
    jurisdiction_type: str | None,
    nodes: Path | None,
    output_root: Path | None,
    profile_id: str | None,
    profile_version: str | None,
    relationships: Path | None,
    snapshot_relation: Sequence[str],
    source_document: Path | None,
    source_publication_date: str | None,
    version_token: str | None,
) -> bool:
    """Return whether explicit build inputs accompany a specification file.

    Parameters
    ----------
    additional_artifact
        Repeated explicit nonstandard artifact declarations.
    detailed_artifact
        Repeated recognized detailed artifact paths.
    detailed_artifacts_directory
        Optional directory containing recognized detailed artifacts.
    jurisdiction_type
        Operator-approved jurisdiction type.
    nodes
        Accepted canonical node delivery artifact.
    output_root
        Graph-packages output root.
    profile_id
        Selected curriculum profile identifier.
    profile_version
        Selected curriculum profile version.
    relationships
        Accepted canonical relationship delivery artifact.
    snapshot_relation
        Repeated approved snapshot-relation JSON objects.
    source_document
        Optional source document whose checksum is recorded.
    source_publication_date
        Optional authoritative source publication date.
    version_token
        Authoritative immutable snapshot version token.

    Returns
    -------
    bool
        ``True`` when at least one explicit build value was supplied.
    """

    scalar_values = (
        detailed_artifacts_directory,
        jurisdiction_type,
        nodes,
        output_root,
        profile_id,
        profile_version,
        relationships,
        source_document,
        source_publication_date,
        version_token,
    )
    return bool(
        additional_artifact
        or detailed_artifact
        or snapshot_relation
        or any(value is not None for value in scalar_values)
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
        If the document is unreadable, malformed, duplicated, or not an object.
    ValidationError
        If the established build specification rejects the document.
    """

    try:
        payload = json.loads(
            object_pairs_hook=_duplicate_key_object, s=path.read_bytes()
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


def _missing_explicit_options(
    *,
    jurisdiction_type: str | None,
    nodes: Path | None,
    output_root: Path | None,
    profile_id: str | None,
    profile_version: str | None,
    relationships: Path | None,
    version_token: str | None,
) -> tuple[str, ...]:
    """Return required explicit options that were not supplied.

    Parameters
    ----------
    jurisdiction_type
        Operator-approved jurisdiction type.
    nodes
        Accepted canonical node delivery artifact.
    output_root
        Graph-packages output root.
    profile_id
        Selected curriculum profile identifier.
    profile_version
        Selected curriculum profile version.
    relationships
        Accepted canonical relationship delivery artifact.
    version_token
        Authoritative immutable snapshot version token.

    Returns
    -------
    tuple[str, ...]
        Missing command-line option names in deterministic order.
    """

    values = {
        "--jurisdiction-type": jurisdiction_type,
        "--nodes": nodes,
        "--output-root": output_root,
        "--profile-id": profile_id,
        "--profile-version": profile_version,
        "--relationships": relationships,
        "--version-token": version_token,
    }
    return tuple(name for name, value in values.items() if value is None)


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
        If a declaration is malformed or a logical name is repeated.
    """

    artifacts: dict[str, Path] = {}
    normalized_names: set[str] = set()

    for value in values:
        logical_name, separator, raw_path = value.partition("=")
        normalized_name = logical_name.casefold()

        if not separator or not logical_name or not raw_path:
            raise ManifestBuildError(
                details={"additional_artifact": value},
                message="Each additional artifact must use LOGICAL_NAME=PATH.",
            )

        if normalized_name in normalized_names:
            raise ManifestBuildError(
                details={"logical_name": logical_name},
                message=(
                    "Additional artifact logical names must be case-insensitively unique."
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
        Repeated JSON objects matching the existing SnapshotRelation model.

    Returns
    -------
    tuple[SnapshotRelation, ...]
        Validated snapshot relation records in supplied order.

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
            payload = json.loads(object_pairs_hook=_duplicate_key_object, s=value)
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
        Stable lower-camel-case JSON summary containing the pending manifest.
    """

    payload = result.model_dump(by_alias=True, mode="json")
    return json.dumps(ensure_ascii=False, indent=2, obj=payload, sort_keys=True)


def _render_validation_error(error: ValidationError) -> str:
    """Render Pydantic failures without echoing supplied input values.

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


def _settings_for_project_dir(project_dir: Path | None) -> BackendSettings:
    """Load settings with an optional explicit repository-root override.

    Parameters
    ----------
    project_dir
        Optional repository root used to resolve project-relative paths.

    Returns
    -------
    BackendSettings
        Validated environment-backed repository settings.
    """

    if project_dir is None:
        return load_settings()

    return BackendSettings(project_dir=project_dir.expanduser().resolve(strict=False))


@cli.command()
def build(  # pylint: disable=R0917
    additional_artifact: list[str] = typer.Option(
        None,
        "--additional-artifact",
        help=(
            "Explicit nonstandard artifact as LOGICAL_NAME=PATH. Repeat for each artifact."
        ),
        metavar="NAME=PATH",
    ),
    detailed_artifact: list[Path] = typer.Option(
        None,
        "--detailed-artifact",
        dir_okay=False,
        exists=True,
        file_okay=True,
        help="Explicit recognized detailed as_* artifact. Repeat as needed.",
        metavar="PATH",
        readable=True,
        resolve_path=True,
    ),
    detailed_artifacts_directory: Path | None = typer.Option(
        None,
        "--detailed-root",
        "--detailed-artifacts-directory",
        dir_okay=True,
        exists=True,
        file_okay=False,
        help="Directory from which recognized detailed as_* artifacts are used.",
        metavar="PATH",
        readable=True,
        resolve_path=True,
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Display the proposed manifest and paths without writing files.",
    ),
    jurisdiction_type: str | None = typer.Option(
        None,
        "--jurisdiction-type",
        help="Operator-approved jurisdiction type for framework metadata.",
    ),
    nodes: Path | None = typer.Option(
        None,
        "--nodes",
        dir_okay=False,
        exists=True,
        file_okay=True,
        help="Accepted canonical as_nodes_XXX.jsonl artifact.",
        metavar="PATH",
        readable=True,
        resolve_path=True,
    ),
    output_root: Path | None = typer.Option(
        None,
        "--output-root",
        dir_okay=True,
        file_okay=False,
        help="Graph-packages output root.",
        metavar="PATH",
        resolve_path=True,
    ),
    profile_id: str | None = typer.Option(
        None, "--profile-id", help="Selected versioned curriculum profile identifier."
    ),
    profile_version: str | None = typer.Option(
        None, "--profile-version", help="Selected immutable curriculum profile version."
    ),
    project_dir: Path | None = typer.Option(
        None,
        "--project-dir",
        dir_okay=True,
        exists=True,
        file_okay=False,
        help="Repository root used to resolve project-relative paths.",
        metavar="PATH",
        readable=True,
        resolve_path=True,
    ),
    relationships: Path | None = typer.Option(
        None,
        "--relationships",
        dir_okay=False,
        exists=True,
        file_okay=True,
        help="Accepted canonical as_relationships_XXX.jsonl artifact.",
        metavar="PATH",
        readable=True,
        resolve_path=True,
    ),
    snapshot_relation: list[str] = typer.Option(
        None,
        "--snapshot-relation",
        help="Approved SnapshotRelation JSON object. Repeat for each relation.",
        metavar="JSON",
    ),
    source_document: Path | None = typer.Option(
        None,
        "--source-document",
        dir_okay=False,
        exists=True,
        file_okay=True,
        help="Optional source document whose exact-byte checksum is recorded.",
        metavar="PATH",
        readable=True,
        resolve_path=True,
    ),
    source_publication_date: str | None = typer.Option(
        None,
        "--source-publication-date",
        help="Optional authoritative source publication date in YYYY-MM-DD form.",
    ),
    spec: Path | None = typer.Option(
        None,
        "--spec",
        dir_okay=False,
        exists=True,
        file_okay=True,
        help="Path to one PackageBuildSpec JSON document.",
        metavar="PATH",
        readable=True,
        resolve_path=True,
    ),
    version_token: str | None = typer.Option(
        None, "--version-token", help="Authoritative immutable snapshot version token."
    ),
) -> None:
    """Build or dry-run one deterministic pending graph package.

    Supply either ``--spec`` or the required explicit build options. A specification
    file cannot be combined with explicit package inputs. ``--project-dir`` and
    ``--dry-run`` control execution and may accompany either input mode.

    Raises
    ------
    typer.Exit
        If input validation or graph-package construction fails.
    """

    explicit_inputs_present = _explicit_inputs_present(
        additional_artifact=additional_artifact,
        detailed_artifact=detailed_artifact,
        detailed_artifacts_directory=detailed_artifacts_directory,
        jurisdiction_type=jurisdiction_type,
        nodes=nodes,
        output_root=output_root,
        profile_id=profile_id,
        profile_version=profile_version,
        relationships=relationships,
        snapshot_relation=snapshot_relation,
        source_document=source_document,
        source_publication_date=source_publication_date,
        version_token=version_token,
    )

    if spec is not None and explicit_inputs_present:
        raise typer.BadParameter(
            "--spec may not be combined with explicit build inputs."
        )

    if spec is None:
        missing_options = _missing_explicit_options(
            jurisdiction_type=jurisdiction_type,
            nodes=nodes,
            output_root=output_root,
            profile_id=profile_id,
            profile_version=profile_version,
            relationships=relationships,
            version_token=version_token,
        )

        if missing_options:
            raise typer.BadParameter(
                "Missing required explicit inputs: " + ", ".join(missing_options) + "."
            )

    try:
        build_spec = (
            _load_spec(spec)
            if spec is not None
            else _build_explicit_spec(
                additional_artifact=additional_artifact,
                detailed_artifact=detailed_artifact,
                detailed_artifacts_directory=detailed_artifacts_directory,
                jurisdiction_type=jurisdiction_type,
                nodes=nodes,
                output_root=output_root,
                profile_id=profile_id,
                profile_version=profile_version,
                relationships=relationships,
                snapshot_relation=snapshot_relation,
                source_document=source_document,
                source_publication_date=source_publication_date,
                version_token=version_token,
            )
        )
        settings = _settings_for_project_dir(project_dir)
        result = build_graph_package(
            dry_run=dry_run, settings=settings, spec=build_spec
        )
    except ValidationError as error:
        typer.echo(_render_validation_error(error), err=True)
        raise typer.Exit(code=1) from error
    except KGFEGMCPError as error:
        typer.echo(
            json.dumps(
                ensure_ascii=False, indent=2, obj=error.public_payload(), sort_keys=True
            ),
            err=True,
        )
        raise typer.Exit(code=1) from error

    typer.echo(_render_result(result))


if __name__ == "__main__":
    cli()
