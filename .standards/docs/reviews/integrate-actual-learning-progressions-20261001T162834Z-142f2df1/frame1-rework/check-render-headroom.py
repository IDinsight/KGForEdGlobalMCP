"""Reviewer diagnostic for the Frame 1 Desktop rework: rendered workflow headroom.

Independent supporting evidence for IMPLEMENTATION review, not formal Tester
verification. Renders all seven single-framework workflows for every accepted
package through ``render_workflow_instructions`` (the shared native/tool renderer)
with three caller-input profiles, and records each rendered message's UTF-8 size or
its typed failure. Run it once against the current source and once against an
archived pre-rework source tree (PYTHONPATH), then compare the two JSON receipts:
a case that renders before the rework and fails after it is a regression caused by
the rework's longer instructions.

Profiles (all values are inside the declared request bounds):

- ``typical``: the inputs the earlier review harness used.
- ``max_ascii``: every free-text caller field at its maximum length in ASCII;
  curriculum review also carries 20 statement-code selectors of 512 characters.
- ``max_multibyte``: the same lengths with a 3-byte UTF-8 character.
- ``real_ids_multibyte``: ``max_multibyte`` free text, but curriculum review uses
  20 real exact selectors with the package's longest identifiers (CASE URI when
  present, else node ID) and every focus is the short topic ``number``.

No network, model or paid service is used; the script only reads accepted packages.

Usage (repository root)::

    PATHS_PROJECT_DIR=$PWD [PYTHONPATH=<archived src>] backend/.venv/bin/python \
        .standards/docs/reviews/<cycle>/frame1-rework/check-render-headroom.py \
        > <receipt>.json
"""

# Standard Library
import json
import socket
import sys

from typing import Any

# Third Party Library
from pydantic import TypeAdapter

# Package Library
import kgfegmcp

from kgfegmcp.bootstrap import bootstrap_application
from kgfegmcp.errors import KGFEGMCPError
from kgfegmcp.prompts.workflow_instructions import (
    WorkflowInstructionsRequest,
    render_workflow_instructions,
)

LIMIT = 64 * 1024


def _reject(*_args: Any, **_kwargs: Any) -> None:
    raise AssertionError("network connection attempted")


def _text(char: str, length: int) -> str:
    """Return caller text of exactly ``length`` characters (non-whitespace)."""
    return (char * length)[:length]


def _requests(runtime: Any, profile: str) -> dict[str, dict[str, Any]]:
    """Build one camel-case request per workflow for one package and profile."""
    identity = runtime.catalog_package.package_identity
    package = runtime.loaded_package
    grades = [g.local_label for g in package.profile.grade_mappings]
    supported = sorted(
        {r.target_node_id for r in package.relationships if r.label == "supports"}
    )
    route = {
        "frameworkId": str(identity.framework_id),
        "snapshotId": str(identity.snapshot_id),
    }
    selector = {"identifierType": "node_id", "nodeId": str(supported[0])}
    extra: dict[str, Any] = {}
    review_extra: dict[str, Any] = {}
    focus = "number"

    if profile != "typical":
        char = "a" if profile == "max_ascii" else "学"
        context = _text(char, 4000)
        extra = {"localContext": context}
        review_extra = {
            "localContext": context,
            "standardIdentifiers": [
                {
                    "identifierType": "statement_code",
                    "statementCode": _text(char, 509) + f"{index:03d}",
                }
                for index in range(20)
            ],
        }
        focus = _text(char, 512)

    if profile == "real_ids_multibyte":
        # Realistic worst case: 20 real exact selectors using the longest identifier
        # the package actually has (CASE URI when present, else node ID).
        nodes = [
            node
            for node in package.item_nodes
            if getattr(node, "case_identifier_uri", None) or getattr(node, "node_id")
        ]
        nodes.sort(
            key=lambda node: (
                -len(str(getattr(node, "case_identifier_uri", None) or node.node_id)),
                str(node.node_id),
            )
        )
        review_extra["standardIdentifiers"] = [
            (
                {
                    "identifierType": "case_identifier_uri",
                    "caseIdentifierUri": str(node.case_identifier_uri),
                }
                if getattr(node, "case_identifier_uri", None)
                else {"identifierType": "node_id", "nodeId": str(node.node_id)}
            )
            for node in nodes[:20]
        ]
        focus = "number"

    learner = (
        {}
        if profile == "typical"
        else {"learnerContext": _text("a" if profile == "max_ascii" else "学", 2000)}
    )
    materials = (
        {}
        if profile == "typical"
        else {
            "availableMaterials": _text(
                "a" if profile == "max_ascii" else "学", 2000
            )
        }
    )
    return {
        "learning_progression_teaching_sequence": {
            **route,
            **extra,
            "topicOrStandard": focus,
        },
        "learning_progression_support_plan": {
            **route,
            **extra,
            "identifier": selector,
        },
        "learning_progression_curriculum_review": {**route, **review_extra},
        "teacher_guide_draft": {
            **route,
            **extra,
            **learner,
            **materials,
            "gradeOrStage": grades[0],
            "topicOrStandard": focus,
        },
        "student_study_support": {
            **route,
            **extra,
            "gradeOrStage": grades[0],
            "topicOrStandard": focus,
        },
        "student_handbook_section": {
            **route,
            **extra,
            "gradeOrStage": grades[0],
            "topicOrStandard": focus,
        },
        "multigrade_lesson_plan": {
            **route,
            **extra,
            **learner,
            "gradesInRoom": grades[:8] if len(grades) >= 2 else grades,
            "topicOrStandard": focus,
        },
    }


def main() -> dict[str, Any]:
    socket.socket.connect = _reject  # type: ignore[method-assign]
    state = bootstrap_application()
    adapter: TypeAdapter[Any] = TypeAdapter(WorkflowInstructionsRequest)
    cases: dict[str, Any] = {}

    for runtime in sorted(
        state.catalog_load_result.package_runtimes,
        key=lambda r: str(r.catalog_package.package_identity.framework_id),
    ):
        framework = str(runtime.catalog_package.package_identity.framework_id)

        for profile in ("typical", "max_ascii", "max_multibyte", "real_ids_multibyte"):
            for name, body in _requests(runtime, profile).items():
                key = f"{framework}|{profile}|{name}"
                try:
                    request = adapter.validate_python({**body, "workflowName": name})
                except Exception as error:  # pylint: disable=W0718
                    cases[key] = {"invalidRequest": str(error)[-400:]}
                    continue
                try:
                    result = render_workflow_instructions(
                        prompt_service=state.prompt_service, request=request
                    )
                except KGFEGMCPError as error:
                    cases[key] = {
                        "error": type(error).__name__,
                        "details": getattr(error, "details", None),
                    }
                    continue
                message = result.rendered.message
                cases[key] = {
                    "bytes": len(message.encode("utf-8")),
                    "headroom": LIMIT - len(message.encode("utf-8")),
                }

    return {"source": kgfegmcp.__file__, "limit": LIMIT, "cases": cases}


if __name__ == "__main__":
    json.dump(main(), sys.stdout, indent=1, sort_keys=True, default=str)
    sys.stdout.write("\n")
