"""This module builds and verifies the MCP Bundle distributed to local desktop MCP
hosts.

This module assembles the existing generic server runtime and its required
configuration and data files into a clean MCPB staging directory. It excludes
development-only files, rejects unsafe filesystem entries, and confirms that the MCPB
manifest agrees with the locked Python project metadata.

After staging, the module delegates manifest validation and archive creation to the
official ``mcpb`` command. It then independently inspects the resulting archive to
confirm that all required files are present, no unexpected or unsafe entries were
added, and every packaged file matches the staged source byte for byte.

This module only prepares the deployment package. It does not alter or implement
curriculum, graph, comparison, search, prompt, resource, or other domain behavior.

The command assembles a temporary bundle root from the repository's generic runtime
source, locked backend project metadata, framework profiles, prompt configurations, and
accepted graph packages. It then delegates manifest validation and archive creation to
the official ``mcpb`` command and verifies the resulting ZIP-compatible archive before
reporting success.

Invoke from the backend directory:

    python -m kgfegmcp.cli.build_mcpb

Use ``--stage-output`` to retain the assembled bundle directory for manual review or a
subsequent STDIO smoke run.
"""

# Future Library
from __future__ import annotations

# Standard Library
import json
import shutil
import stat
import subprocess
import tempfile
import tomllib
import zipfile

from collections.abc import Sequence
from pathlib import Path, PurePosixPath
from typing import Annotated

# Third Party Library
import typer

cli = typer.Typer(
    help=(
        "Assemble, validate, and pack the local Curriculum Knowledge Graph MCP bundle."
    ),
    no_args_is_help=False,
)

_EXPECTED_ENTRY_POINT = "src/kgfegmcp/mcpb_server.py"
_EXPECTED_MCP_CONFIG_ARGS = (
    "run",
    "--directory",
    "${__dirname}",
    "--locked",
    "--no-dev",
    "python",
    "-m",
    "kgfegmcp.mcpb_server",
)
_EXPECTED_MCP_CONFIG_ENV = {
    "KGFEGMCP_CONFIG_ROOT": "${__dirname}/config",
    "KGFEGMCP_DATA_ROOT": "${__dirname}/data",
    "KGFEGMCP_ENV": "local",
    "KGFEGMCP_GRAPH_PACKAGES_ROOT": "${__dirname}/data/graph_packages",
    "KGFEGMCP_INVALID_PACKAGE_POLICY": "fail",
    "KGFEGMCP_LOG_LEVEL": "INFO",
    "KGFEGMCP_PROFILE_ROOT": "${__dirname}/config/profiles",
    "KGFEGMCP_PROMPT_ROOT": "${__dirname}/config/prompts",
    "PATHS_PROJECT_DIR": "${__dirname}",
}
_IGNORED_NAMES = frozenset(
    {
        ".DS_Store",
        ".mypy_cache",
        ".pytest_cache",
        ".ruff_cache",
        ".venv",
        "__MACOSX",
        "__pycache__",
    }
)
_REQUIRED_ARCHIVE_PATHS = frozenset(
    {
        "README.md",
        "config/profiles",
        "config/prompts",
        "data/graph_packages",
        "fastmcp.json",
        "manifest.json",
        "pyproject.toml",
        "src/kgfegmcp/mcpb_server.py",
        "uv.lock",
    }
)


def _build_from_stage(*, mcpb_command: str, output: Path, stage_root: Path) -> None:
    """Validate, pack, and verify one assembled staging directory.

    Parameters
    ----------
    mcpb_command
        Official MCPB CLI executable name or absolute path.
    output
        Destination archive path.
    stage_root
        Assembled bundle directory.
    """

    manifest = _load_json_object(stage_root / "manifest.json")
    resolved_output = output.resolve(strict=False)
    resolved_stage_root = stage_root.resolve(strict=True)

    if resolved_output.is_relative_to(resolved_stage_root):
        raise ValueError("MCPB archive output may not be inside the staging root.")

    output.parent.mkdir(exist_ok=True, parents=True)

    if output.exists():
        output.unlink()

    _run_command(arguments=(mcpb_command, "validate", str(stage_root)), cwd=stage_root)
    _run_command(
        arguments=(mcpb_command, "pack", str(stage_root), str(output)), cwd=stage_root
    )
    _verify_bundle(
        bundle_path=output, expected_manifest=manifest, stage_root=stage_root
    )


def _copy_file(*, destination: Path, source: Path) -> None:
    """Copy one required regular file into the bundle staging directory.

    Parameters
    ----------
    destination
        Target path beneath the staging directory.
    source
        Required repository source file.

    Raises
    ------
    ValueError
        If the source is missing, is not a regular file, or is a symlink.
    """

    if not source.is_file() or source.is_symlink():
        raise ValueError(f"Bundle source file is invalid: '{source}'.")

    destination.parent.mkdir(exist_ok=True, parents=True)
    shutil.copy2(dst=destination, src=source)


def _copy_tree(*, destination: Path, source: Path) -> None:
    """Copy one verified source tree into the bundle staging directory.

    Parameters
    ----------
    destination
        Target path beneath the staging directory.
    source
        Verified repository source directory.
    """

    _require_regular_tree(source)
    shutil.copytree(dst=destination, ignore=_ignore_copy_names, src=source)


def _default_output_path(*, project_root: Path, version: str) -> Path:
    """Return the default versioned MCPB output path.

    Parameters
    ----------
    project_root
        Repository root.
    version
        Package semantic version.

    Returns
    -------
    Path
        Default archive path beneath the repository ``dist`` directory.
    """

    return project_root / "dist" / f"kgfegmcp-{version}.mcpb"


def _duplicate_key_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    """Construct one JSON object while rejecting duplicate member names.

    Parameters
    ----------
    pairs
        Source-ordered JSON object member pairs.

    Returns
    -------
    dict[str, object]
        Object preserving source order without duplicate keys.

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


def _ignore_copy_names(directory: str, names: list[str]) -> set[str]:
    """Return development-only names excluded from the assembled bundle.

    Parameters
    ----------
    directory
        Current source directory supplied by ``shutil.copytree``.
    names
        Child names present in the current source directory.

    Returns
    -------
    set[str]
        Names that must not be copied into the bundle staging directory.
    """

    del directory
    return {
        name
        for name in names
        if name in _IGNORED_NAMES or name.endswith((".pyc", ".pyo"))
    }


def _load_json_object(path: Path) -> dict[str, object]:
    """Load one strict JSON object from disk.

    Parameters
    ----------
    path
        JSON document to read.

    Returns
    -------
    dict[str, object]
        Parsed object with duplicate keys rejected.

    Raises
    ------
    ValueError
        If the document is not a JSON object or contains duplicate keys.
    """

    payload = json.loads(object_pairs_hook=_duplicate_key_object, s=path.read_bytes())

    if not isinstance(payload, dict):
        raise ValueError(f"Expected a JSON object in '{path}'.")

    return payload


def _manifest_sections(
    manifest: dict[str, object],
) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    """Return the validated author, mcp_config, and server manifest objects.

    Parameters
    ----------
    manifest
        Parsed MCPB manifest template.

    Returns
    -------
    tuple[dict[str, object], dict[str, object], dict[str, object]]
        The manifest author object, the server ``mcp_config`` object, and the server
        object, in that order.

    Raises
    ------
    ValueError
        If the author, compatibility, server, or ``mcp_config`` object is missing or is
        not a JSON object.
    """

    author = manifest.get("author")
    compatibility = manifest.get("compatibility")
    server = manifest.get("server")

    if not isinstance(author, dict):
        raise ValueError("MCPB manifest is missing the author object.")

    if not isinstance(compatibility, dict):
        raise ValueError("MCPB manifest is missing the compatibility object.")

    if not isinstance(server, dict):
        raise ValueError("MCPB manifest is missing the server object.")

    mcp_config = server.get("mcp_config")

    if not isinstance(mcp_config, dict):
        raise ValueError("MCPB server is missing the mcp_config object.")

    return author, mcp_config, server


def _project_root() -> Path:
    """Return the repository root containing ``backend``, ``config``, and ``data``.

    Returns
    -------
    Path
        Canonical repository root inferred from this installed source file.
    """

    return Path(__file__).resolve().parents[4]


def _project_sections(
    project_metadata: dict[str, object],
) -> tuple[dict[str, object], dict[str, object]]:
    """Return the validated primary author and ``[project]`` table objects.

    Parameters
    ----------
    project_metadata
        Parsed packaged ``pyproject.toml`` document.

    Returns
    -------
    tuple[dict[str, object], dict[str, object]]
        The primary project author object and the ``[project]`` table, in that order.

    Raises
    ------
    ValueError
        If the ``[project]`` table or its authors are missing, or if the primary author
        is not a JSON object.
    """

    project = project_metadata.get("project")

    if not isinstance(project, dict):
        raise ValueError("Packaged pyproject.toml is missing the [project] table.")

    project_authors = project.get("authors")

    if not isinstance(project_authors, list) or not project_authors:
        raise ValueError("Packaged pyproject.toml is missing project authors.")

    if not isinstance(project_authors[0], dict):
        raise ValueError("Packaged pyproject.toml has an invalid primary author.")

    return project_authors[0], project


def _reject_archive_symlinks(infos: Sequence[zipfile.ZipInfo]) -> None:
    """Reject any archive member stored as a symbolic link.

    Parameters
    ----------
    infos
        Archive member metadata records to inspect.

    Raises
    ------
    ValueError
        If any member's stored Unix mode identifies a symbolic link.
    """

    for info in infos:
        mode = info.external_attr >> 16

        if stat.S_ISLNK(mode):
            raise ValueError(
                f"MCPB archive may not contain symlinks: '{info.filename}'."
            )


def _require_regular_tree(source: Path) -> None:
    """Reject symlinks and special filesystem entries beneath one source tree.

    Parameters
    ----------
    source
        Directory whose contents will be copied into the bundle.

    Raises
    ------
    ValueError
        If the source is missing, is not a directory, or contains a symlink or special
        filesystem entry.
    """

    if not source.is_dir() or source.is_symlink():
        raise ValueError(f"Bundle source directory is invalid: '{source}'.")

    for path in sorted(source.iterdir(), key=lambda candidate: candidate.name):
        if path.name in _IGNORED_NAMES or path.suffix in {".pyc", ".pyo"}:
            continue

        if path.is_symlink():
            raise ValueError(f"Bundle source may not contain symlinks: '{path}'.")

        if path.is_dir():
            _require_regular_tree(path)
            continue

        if not path.is_file():
            raise ValueError(
                f"Bundle source may not contain special entries: '{path}'."
            )


def _run_command(*, arguments: Sequence[str], cwd: Path) -> None:
    """Run one required external command and preserve its terminal output.

    Parameters
    ----------
    arguments
        Complete command and argument sequence.
    cwd
        Working directory for the child process.

    Raises
    ------
    RuntimeError
        If the executable is missing or the command exits unsuccessfully.
    """

    try:
        subprocess.run(args=tuple(arguments), check=True, cwd=cwd)
    except FileNotFoundError as error:
        raise RuntimeError(
            f"Required command '{arguments[0]}' was not found on PATH."
        ) from error
    except subprocess.CalledProcessError as error:
        raise RuntimeError(
            f"Command failed with exit code {error.returncode}: " + " ".join(arguments)
        ) from error


def _safe_archive_path(name: str) -> PurePosixPath:
    """Return one validated relative archive path.

    Parameters
    ----------
    name
        ZIP member name.

    Returns
    -------
    PurePosixPath
        Validated relative member path.

    Raises
    ------
    ValueError
        If the member is absolute or contains a parent traversal segment.
    """

    path = PurePosixPath(name)

    if (
        "\\" in name
        or path == PurePosixPath(".")
        or path.is_absolute()
        or ".." in path.parts
    ):
        raise ValueError(f"Unsafe path in MCPB archive: '{name}'.")

    return path


def _stage_bundle(*, destination: Path, project_root: Path) -> dict[str, object]:
    """Assemble the complete deterministic MCPB staging directory.

    Parameters
    ----------
    destination
        Empty directory that will become the bundle root.
    project_root
        Repository root containing runtime source and immutable inputs.

    Returns
    -------
    dict[str, object]
        Parsed and cross-checked manifest used for archive verification.

    Raises
    ------
    ValueError
        If the destination is not empty or any required source is invalid.
    """

    if destination.exists():
        if not destination.is_dir() or any(destination.iterdir()):
            raise ValueError(f"Bundle staging directory is not empty: '{destination}'.")

    backend_root = project_root / "backend"
    packaging_root = project_root / "packaging" / "mcpb"
    copied_trees = (
        backend_root / "src",
        project_root / "config" / "profiles",
        project_root / "config" / "prompts",
        project_root / "data" / "graph_packages",
    )
    resolved_destination = destination.resolve(strict=False)

    for source_tree in copied_trees:
        if resolved_destination.is_relative_to(source_tree.resolve(strict=False)):
            raise ValueError(
                f"Bundle staging directory may not be inside a copied source tree: "
                f"'{destination}'."
            )

    destination.mkdir(exist_ok=True, parents=True)

    _copy_file(
        destination=destination / ".mcpbignore", source=packaging_root / ".mcpbignore"
    )
    _copy_file(destination=destination / "README.md", source=backend_root / "README.md")
    _copy_file(
        destination=destination / "fastmcp.json", source=backend_root / "fastmcp.json"
    )
    _copy_file(
        destination=destination / "manifest.json",
        source=packaging_root / "manifest.json",
    )
    _copy_file(
        destination=destination / "pyproject.toml",
        source=backend_root / "pyproject.toml",
    )
    _copy_file(destination=destination / "uv.lock", source=backend_root / "uv.lock")
    _copy_tree(
        destination=destination / "config" / "profiles",
        source=project_root / "config" / "profiles",
    )
    _copy_tree(
        destination=destination / "config" / "prompts",
        source=project_root / "config" / "prompts",
    )
    _copy_tree(
        destination=destination / "data" / "graph_packages",
        source=project_root / "data" / "graph_packages",
    )
    _copy_tree(destination=destination / "src", source=backend_root / "src")

    manifest = _load_json_object(destination / "manifest.json")
    project_metadata = tomllib.loads(
        (destination / "pyproject.toml").read_text(encoding="utf-8")
    )
    _validate_manifest_contract(manifest=manifest, project_metadata=project_metadata)
    return manifest


def _staged_bundle_files(stage_root: Path) -> dict[str, Path]:
    """Return the staged bundle files keyed by POSIX-relative archive path.

    Parameters
    ----------
    stage_root
        Complete assembled source directory used by the packer.

    Returns
    -------
    dict[str, Path]
        Mapping of each staged regular file's POSIX-relative path to its absolute
        source path, excluding the packer-only ``.mcpbignore`` control file.
    """

    staged_files = {
        path.relative_to(stage_root).as_posix(): path
        for path in stage_root.rglob("*")
        if path.is_file()
    }
    staged_files.pop(".mcpbignore", None)
    return staged_files


def _validate_manifest_contract(
    *, manifest: dict[str, object], project_metadata: dict[str, object]
) -> None:
    """Require the MCPB manifest to agree with the packaged Python project.

    Parameters
    ----------
    manifest
        Parsed MCPB manifest template.
    project_metadata
        Parsed packaged ``pyproject.toml`` document.

    Raises
    ------
    ValueError
        If required manifest identity, version, or server fields are inconsistent.
    """

    author, mcp_config, server = _manifest_sections(manifest)
    primary_author, project = _project_sections(project_metadata)
    _validate_manifest_identity(
        author=author, manifest=manifest, primary_author=primary_author, project=project
    )
    _validate_manifest_server(mcp_config=mcp_config, server=server)


def _validate_manifest_identity(
    *,
    author: dict[str, object],
    manifest: dict[str, object],
    primary_author: dict[str, object],
    project: dict[str, object],
) -> None:
    """Require manifest identity and version fields to match the project.

    Parameters
    ----------
    author
        Author object declared in the MCPB manifest.
    manifest
        Parsed MCPB manifest template.
    primary_author
        Primary author object declared in the packaged project metadata.
    project
        Parsed ``[project]`` table from the packaged ``pyproject.toml``.

    Raises
    ------
    ValueError
        If the manifest version, name, project version, or author does not match the
        packaged project.
    """

    if manifest.get("manifest_version") != "0.4":
        raise ValueError("MCPB manifest_version must be exactly '0.4'.")

    if (
        manifest.get("name") != project.get("name")
        or manifest.get("name") != "kgfegmcp"
    ):
        raise ValueError("MCPB manifest name must match the backend project name.")

    if manifest.get("version") != project.get("version"):
        raise ValueError(
            "MCPB manifest version must match backend project version exactly."
        )

    if author != primary_author:
        raise ValueError("MCPB manifest author must match the primary project author.")


def _validate_manifest_server(
    *, mcp_config: dict[str, object], server: dict[str, object]
) -> None:
    """Require the manifest server and ``mcp_config`` to match the locked launch.

    Parameters
    ----------
    mcp_config
        Parsed ``mcp_config`` object from the MCPB manifest server.
    server
        Parsed server object from the MCPB manifest.

    Raises
    ------
    ValueError
        If the server entry point or type, or any ``mcp_config`` command, arguments,
        environment, or field set, differs from the approved launch.
    """

    if server.get("entry_point") != _EXPECTED_ENTRY_POINT:
        raise ValueError("MCPB server entry_point is not the approved STDIO module.")

    if server.get("type") != "uv":
        raise ValueError("MCPB server type must be 'uv'.")

    if mcp_config.get("command") != "uv":
        raise ValueError("MCPB mcp_config command must be 'uv'.")

    mcp_config_args = mcp_config.get("args")

    if (
        not isinstance(mcp_config_args, list)
        or tuple(mcp_config_args) != _EXPECTED_MCP_CONFIG_ARGS
    ):
        raise ValueError("MCPB mcp_config args differ from the approved locked launch.")

    if mcp_config.get("env") != _EXPECTED_MCP_CONFIG_ENV:
        raise ValueError("MCPB mcp_config environment differs from the approved roots.")

    if set(mcp_config) != {"args", "command", "env"}:
        raise ValueError("MCPB mcp_config contains unsupported fields.")


def _verify_archive_content(
    *, archive: zipfile.ZipFile, staged_files: dict[str, Path], stage_root: Path
) -> None:
    """Verify packaged file bytes match their staged sources exactly.

    Parameters
    ----------
    archive
        Opened MCPB archive to inspect.
    staged_files
        Mapping of staged file POSIX paths to their source paths.
    stage_root
        Complete assembled source directory used by the packer.

    Raises
    ------
    ValueError
        If any packaged file, or the optional ``.mcpbignore`` control file, differs
        from its staged source bytes.
    """

    for name, staged_path in sorted(staged_files.items()):
        if archive.read(name) != staged_path.read_bytes():
            raise ValueError(f"MCPB archive content differs from staged file '{name}'.")

    archive_names = set(archive.namelist())

    if (
        ".mcpbignore" in archive_names
        and archive.read(".mcpbignore") != (stage_root / ".mcpbignore").read_bytes()
    ):
        raise ValueError("MCPB archive content differs from staged file '.mcpbignore'.")


def _verify_archive_members(
    *, archive: zipfile.ZipFile, staged_files: dict[str, Path]
) -> None:
    """Verify archive member safety and file-name completeness.

    Parameters
    ----------
    archive
        Opened MCPB archive to inspect.
    staged_files
        Mapping of staged file POSIX paths to their source paths.

    Raises
    ------
    ValueError
        If members use unsafe or duplicate paths or symlinks, or if the archive omits
        staged files, adds unexpected files, or lacks a required path.
    """

    infos = tuple(archive.infolist())
    paths = tuple(_safe_archive_path(info.filename) for info in infos)

    if len(paths) != len(set(paths)):
        raise ValueError("MCPB archive contains duplicate member paths.")

    _reject_archive_symlinks(infos)

    member_names = {str(path).rstrip("/") for path in paths}
    archive_file_names = {
        str(path) for info, path in zip(infos, paths, strict=True) if not info.is_dir()
    }
    permitted_archive_files = set(staged_files) | {".mcpbignore"}
    missing_files = sorted(set(staged_files) - archive_file_names)
    unexpected_files = sorted(archive_file_names - permitted_archive_files)

    if missing_files:
        raise ValueError(
            "MCPB archive is missing staged file(s): " + ", ".join(missing_files)
        )

    if unexpected_files:
        raise ValueError(
            "MCPB archive contains unexpected file(s): " + ", ".join(unexpected_files)
        )

    _verify_required_paths(member_names)


def _verify_bundle(
    *, bundle_path: Path, expected_manifest: dict[str, object], stage_root: Path
) -> None:
    """Verify archive safety, completeness, and byte-preserving package content.

    Parameters
    ----------
    bundle_path
        Packed MCPB archive.
    expected_manifest
        Parsed staged manifest that must be retained exactly.
    stage_root
        Complete assembled source directory used by the packer.

    Raises
    ------
    ValueError
        If the archive is missing, malformed, unsafe, incomplete, contains unsupported
        member types, or differs from the staged bundle content.
    """

    if not bundle_path.is_file():
        raise ValueError(f"MCPB archive was not created: '{bundle_path}'.")

    staged_files = _staged_bundle_files(stage_root)

    with zipfile.ZipFile(bundle_path) as archive:
        _verify_archive_members(archive=archive, staged_files=staged_files)
        _verify_archive_content(
            archive=archive, staged_files=staged_files, stage_root=stage_root
        )
        archive_manifest = json.loads(
            object_pairs_hook=_duplicate_key_object, s=archive.read("manifest.json")
        )

    if archive_manifest != expected_manifest:
        raise ValueError("Packed MCPB manifest differs from the staged manifest.")


def _verify_required_paths(member_names: set[str]) -> None:
    """Require every mandatory bundle path to be present among archive members.

    Parameters
    ----------
    member_names
        Normalized archive member names without trailing separators.

    Raises
    ------
    ValueError
        If any required file or directory path is absent from the archive.
    """

    for required_path in _REQUIRED_ARCHIVE_PATHS:
        if not any(
            name == required_path or name.startswith(f"{required_path}/")
            for name in member_names
        ):
            raise ValueError(
                f"MCPB archive is missing required path '{required_path}'."
            )


@cli.command()
def build_mcpb(
    *,
    mcpb_command: Annotated[
        str,
        typer.Option(
            help="Official MCPB CLI executable name or absolute path.",
            metavar="COMMAND",
        ),
    ] = "mcpb",
    output: Annotated[
        Path | None,
        typer.Option(
            help="Destination .mcpb file. Defaults to dist/kgfegmcp-VERSION.mcpb.",
            metavar="PATH",
        ),
    ] = None,
    stage_output: Annotated[
        Path | None,
        typer.Option(
            help="Optional empty directory in which to retain the assembled bundle.",
            metavar="PATH",
        ),
    ] = None,
) -> None:
    """Assemble, validate, pack, and verify the local MCP Bundle.

    Parameters
    ----------
    mcpb_command
        Official MCPB CLI executable name or absolute path.
    output
        Optional destination archive path.
    stage_output
        Optional empty directory to retain after packing.

    Raises
    ------
    typer.Exit
        If staging, validation, packing, or archive verification fails.
    """

    project_root = _project_root()

    try:
        template_manifest = _load_json_object(
            project_root / "packaging" / "mcpb" / "manifest.json"
        )
        version = template_manifest.get("version")

        if not isinstance(version, str):
            raise ValueError("MCPB manifest version must be a string.")

        output_path = (
            output.expanduser().resolve(strict=False)
            if output is not None
            else _default_output_path(project_root=project_root, version=version)
        )

        if stage_output is not None:
            stage_root = stage_output.expanduser().resolve(strict=False)
            _stage_bundle(destination=stage_root, project_root=project_root)
            _build_from_stage(
                mcpb_command=mcpb_command, output=output_path, stage_root=stage_root
            )
        else:
            with tempfile.TemporaryDirectory(prefix="kgfegmcp-mcpb-") as temporary:
                stage_root = Path(temporary) / "bundle"
                _stage_bundle(destination=stage_root, project_root=project_root)
                _build_from_stage(
                    mcpb_command=mcpb_command, output=output_path, stage_root=stage_root
                )
    except (OSError, RuntimeError, ValueError, zipfile.BadZipFile) as error:
        typer.echo(err=True, message=f"MCPB build failed: {error}")
        raise typer.Exit(code=1) from error

    typer.echo(str(output_path))


if __name__ == "__main__":
    cli()
