"""This module contains the entry point for verifying a restored evidence archive.

Each runtime-only package declares an evidence archive record that binds its complete
full-evidence set by repository-relative local path, size and SHA-256. This command
reads only that record and the local files it names, and reports each entry as
``ok``, ``missing`` or ``mismatch``. It never contacts the archive, downloads or
uploads anything, or changes any file.

The ``one`` command verifies one exact framework snapshot. The ``all`` command
verifies every package beneath the configured graph-packages root. Run it after
restoring an input set from the evidence archive, before rebuilding or accepting a
package:

    python -m kgfegmcp.cli.verify_evidence_archive all

The command exits with status 0 when every entry is ``ok``, 1 when any entry is
missing or mismatched or a package has no readable record, and 2 for invocation or
configuration errors.
"""

# Future Library
from __future__ import annotations

# Standard Library
import json

from pathlib import Path
from typing import Annotated

# Third Party Library
import typer

from pydantic import TypeAdapter, ValidationError

# Package Library
from kgfegmcp.config import BackendSettings
from kgfegmcp.domain.identifiers import FrameworkId, SnapshotId
from kgfegmcp.errors import KGFEGMCPError, ManifestBuildError, PackageValidationError
from kgfegmcp.packages.checksums import calculate_file_sha256
from kgfegmcp.packages.evidence_models import (
    EVIDENCE_ARCHIVE_LOCATION,
    EvidenceArchiveEntry,
    EvidenceArchiveRecord,
)
from kgfegmcp.packages.normalization_sources import read_json_object
from kgfegmcp.packages.repository import GraphPackageCandidate, GraphPackageRepository
from kgfegmcp.packages.slim import EVIDENCE_ARCHIVE_RECORD_PATH

_FRAMEWORK_ID_ADAPTER: TypeAdapter[FrameworkId] = TypeAdapter(FrameworkId)
_SNAPSHOT_ID_ADAPTER: TypeAdapter[SnapshotId] = TypeAdapter(SnapshotId)

cli = typer.Typer(
    help="Verify restored archived evidence against package evidence records.",
    no_args_is_help=True,
)


def _entry_report(
    *, entry: EvidenceArchiveEntry, name: str, project_dir: Path
) -> dict[str, object]:
    """Compare one record entry with its local file.

    Parameters
    ----------
    entry
        Evidence archive record entry.
    name
        Full-evidence logical name.
    project_dir
        Repository root that local paths are relative to.

    Returns
    -------
    dict[str, object]
        Entry report with status ``ok``, ``missing`` or ``mismatch``.
    """

    path = project_dir / str(entry.local_path)
    report: dict[str, object] = {
        "expectedSha256": str(entry.sha256),
        "expectedSizeBytes": entry.size_bytes,
        "localPath": str(entry.local_path),
        "logicalName": name,
    }

    if not path.is_file():
        return {**report, "status": "missing"}

    actual_sha256 = calculate_file_sha256(path)
    actual_size = path.stat().st_size
    matches = actual_sha256 == entry.sha256 and actual_size == entry.size_bytes
    return {
        **report,
        "actualSha256": str(actual_sha256),
        "actualSizeBytes": actual_size,
        "status": "ok" if matches else "mismatch",
    }


def _package_report(
    *, candidate: GraphPackageCandidate, project_dir: Path
) -> dict[str, object]:
    """Verify every entry of one package's evidence archive record.

    Parameters
    ----------
    candidate
        Discovered package.
    project_dir
        Repository root that local paths are relative to.

    Returns
    -------
    dict[str, object]
        Package report with entry reports, counts and an overall status of ``ok``,
        ``incomplete`` or ``record_unavailable``.
    """

    report: dict[str, object] = {
        "frameworkId": str(candidate.framework_id),
        "snapshotId": str(candidate.snapshot_id),
    }

    try:
        record = EvidenceArchiveRecord.model_validate(
            read_json_object(
                data=(
                    candidate.package_path / EVIDENCE_ARCHIVE_RECORD_PATH
                ).read_bytes(),
                label="evidence record",
            )
        )
    except (ManifestBuildError, OSError, ValidationError):
        return {**report, "status": "record_unavailable"}

    if record.framework_id != candidate.framework_id:
        return {**report, "status": "record_unavailable"}

    entries = [
        _entry_report(entry=entry, name=name, project_dir=project_dir)
        for name, entry in sorted(record.evidence_artifacts.items())
    ]
    counts = {
        status: sum(entry["status"] == status for entry in entries)
        for status in ("missing", "mismatch", "ok")
    }
    return {
        **report,
        "counts": counts,
        "entries": entries,
        "status": "ok" if counts["ok"] == len(entries) else "incomplete",
    }


def _report(
    *, candidates: tuple[GraphPackageCandidate, ...], project_dir: Path
) -> None:
    """Print the verification report and exit non-zero unless everything is ok.

    Parameters
    ----------
    candidates
        Packages to verify.
    project_dir
        Repository root that local paths are relative to.

    Raises
    ------
    typer.Exit
        With code 1 when any package is incomplete or has no readable record.
    """

    packages = [
        _package_report(candidate=candidate, project_dir=project_dir)
        for candidate in candidates
    ]
    typer.echo(
        json.dumps(
            ensure_ascii=False,
            indent=2,
            obj={"archiveLocation": EVIDENCE_ARCHIVE_LOCATION, "packages": packages},
            sort_keys=True,
        )
    )

    if any(package["status"] != "ok" for package in packages):
        raise typer.Exit(code=1)


def _write_error(error: KGFEGMCPError) -> None:
    """Write one public domain error to standard error.

    Parameters
    ----------
    error
        Expected typed backend failure.
    """

    typer.echo(
        err=True,
        message=json.dumps(
            ensure_ascii=False, indent=2, obj=error.public_payload(), sort_keys=True
        ),
    )


@cli.command("all")
def verify_all() -> None:
    """Verify the evidence archive of every package under the graph-packages root.

    Raises
    ------
    typer.Exit
        With code 1 when any entry is missing or mismatched, or code 2 for
        configuration or domain errors.
    """

    try:
        settings = BackendSettings()
        candidates = GraphPackageRepository(
            graph_packages_root=settings.graph_packages_root
        ).discover()
    except ValidationError as error:
        _write_error(
            PackageValidationError(
                details={
                    "validation_errors": error.errors(
                        include_input=False, include_url=False
                    )
                },
                message="Verification CLI settings are invalid.",
            )
        )
        raise typer.Exit(code=2) from error
    except KGFEGMCPError as error:
        _write_error(error)
        raise typer.Exit(code=2) from error

    _report(candidates=candidates, project_dir=settings.project_dir)


@cli.command("one")
def verify_one(
    *,
    framework_id: Annotated[
        str,
        typer.Option(
            "--framework-id",
            help="Stable framework identifier.",
            metavar="FRAMEWORK_ID",
        ),
    ],
    snapshot_id: Annotated[
        str,
        typer.Option(
            "--snapshot-id",
            help="Immutable snapshot identifier.",
            metavar="SNAPSHOT_ID",
        ),
    ],
) -> None:
    """Verify the evidence archive of one exact framework snapshot.

    Parameters
    ----------
    framework_id
        Stable framework identifier.
    snapshot_id
        Immutable snapshot identifier.

    Raises
    ------
    typer.Exit
        With code 1 when any entry is missing or mismatched, or code 2 for
        invocation or domain errors.
    """

    try:
        settings = BackendSettings()
        candidate = GraphPackageRepository(
            graph_packages_root=settings.graph_packages_root
        ).candidate(
            framework_id=_FRAMEWORK_ID_ADAPTER.validate_python(framework_id),
            snapshot_id=_SNAPSHOT_ID_ADAPTER.validate_python(snapshot_id),
        )
    except ValidationError as error:
        _write_error(
            PackageValidationError(
                details={
                    "validation_errors": error.errors(
                        include_input=False, include_url=False
                    )
                },
                message="A package identifier or CLI setting is invalid.",
            )
        )
        raise typer.Exit(code=2) from error
    except KGFEGMCPError as error:
        _write_error(error)
        raise typer.Exit(code=2) from error

    _report(candidates=(candidate,), project_dir=settings.project_dir)


if __name__ == "__main__":
    cli()
