"""Bounded stored-evidence retrieval instructions without executing any model."""

# Standard Library
import json

from types import SimpleNamespace
from typing import Any, cast

# Third Party Library
import pytest

from fastmcp import Client
from pydantic import TypeAdapter, ValidationError

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import AppState
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.catalog.service import CatalogService
from kgfegmcp.domain.enums import DerivativeGenerationPolicy
from kgfegmcp.domain.identifiers import LanguageTag
from kgfegmcp.errors import PromptAccessDeniedError
from kgfegmcp.prompts.learning_progressions import (
    LearningProgressionCurriculumReviewRequest,
    render_optional_progression_workflow,
)
from kgfegmcp.prompts.models import (
    LearningProgressionTeachingSequenceRequest,
    PromptFocusMode,
    StudyDifficulty,
)
from kgfegmcp.services.lp_models import (
    GetLearningProgressionPathsRequest,
    GetLearningProgressionRequest,
    GetStandardProgressionsRequest,
    ProgressionCollectionResult,
    SearchLearningProgressionsRequest,
    TraverseLearningProgressionsRequest,
)
from kgfegmcp.services.models import GetFrameworkStatisticsRequest
from tests.fixtures.progression_fixtures import selector

# Superseded fixed-count promises: a size-limited page may return fewer edges.
FIXED_COUNT_PROMISES = ("page of 25", "pages of 25", "three of 25", "at most 75")
DIRECT_KINDS = ["outgoing_builds", "incoming_builds", "related"]


def templates(message: str) -> list[dict[str, Any]]:
    """Read actual nested request examples from rendered workflow instructions."""
    return [
        json.loads(line)["request"]
        for line in message.splitlines()
        if line.startswith('{"request":')
    ]


def assert_per_kind_direct_calls(message: str, placeholder: str) -> None:
    """Check one single-page direct call per kind, in order, with no all-kind call."""
    directs = [call for call in templates(message) if "connectionKind" in call]
    assert [call["connectionKind"] for call in directs] == DIRECT_KINDS
    for call in directs:
        GetStandardProgressionsRequest.model_validate(call)
        assert call["limit"] == 25 and "cursor" not in call
        assert call["identifier"] == {
            "identifierType": "node_id",
            "nodeId": placeholder,
        }
    assert "at most 9" in message
    assert "limit 25 is the maximum requested" in message
    assert "may return fewer" in message and "do not follow nextCursor" in message
    assert "kind is incomplete for that standard" in message
    assert "deduplicate relationship IDs across calls and standards" in message
    assert not any(promise in message for promise in FIXED_COUNT_PROMISES)


def test_teaching_sequence_workflow(accepted_state: AppState) -> None:
    """Six-package samples preserve bounded teaching retrieval, identity and notices."""
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        result = accepted_state.prompt_service.learning_progression_teaching_sequence(
            focus_mode=PromptFocusMode.TOPIC,
            framework_id=identity.framework_id,
            local_context="Teacher observation; not measured mastery.",
            local_grade_labels=(),
            normalized_grades=(),
            output_language=TypeAdapter(LanguageTag).validate_python("fr"),
            snapshot_id=identity.snapshot_id,
            topic_or_standard="mathematics",
        )
        message = result.message
        calls = templates(message)
        walk = next(call for call in calls if "direction" in call)
        paths = next(call for call in calls if "sourceIdentifier" in call)
        assert (
            walk["direction"],
            walk["maxDepth"],
            walk["maxNodes"],
            walk["maxEdges"],
        ) == ("downstream", 8, 30, 40)
        GetLearningProgressionPathsRequest.model_validate(paths)
        assert (paths["maxDepth"], paths["maxPaths"]) == (6, 3)
        # Frame 2 per-kind calls replace the single connectionKind all page.
        assert_per_kind_direct_calls(message, "<selected-node-id>")
        assert "never sequence hops" in message
        assert any(call.get("limit") == 10 for call in calls)
        assert (
            "at most 3 selected standards" in message
            and "at most 5 returned supporting" in message
        )
        assert "at most 10 distinct full provenance" in message
        assert "EVIDENCE ACCESS" in message and "at most 32" in message
        assert (
            "scopeComplete" in message
            and "graphExhausted" in message
            and "truncationReasons" in message
        )
        assert (
            "not a mandatory prerequisite" in message and "caller-reported" in message
        )
        assert (
            result.snapshot_id == identity.snapshot_id
            and result.prompt_version == "1.4.0"
        )
        assert str(identity.profile_sha256) in message
        for call in calls:
            assert call.get("snapshotId") == str(identity.snapshot_id) or call.get(
                "snapshotIds"
            ) == [str(identity.snapshot_id)]


def test_support_plan_workflow(accepted_state: AppState) -> None:
    """Exact-target support respects independent incoming/related/upstream budgets."""
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        node = runtime.loaded_package.item_nodes[0]
        result = accepted_state.prompt_service.learning_progression_support_plan(
            framework_id=identity.framework_id,
            identifier=selector(node.node_id),
            local_context="A teacher reports difficulty; no diagnosis.",
            output_language=None,
            snapshot_id=identity.snapshot_id,
        )
        calls = templates(result.message)
        walks = [call for call in calls if "direction" in call]
        directs = [call for call in calls if "connectionKind" in call]
        assert len(walks) == 1
        assert (
            walks[0]["direction"],
            walks[0]["maxDepth"],
            walks[0]["maxNodes"],
            walks[0]["maxEdges"],
        ) == ("upstream", 3, 20, 30)
        assert {call["connectionKind"] for call in directs} == {
            "incoming_builds",
            "related",
        }
        assert all(call["limit"] == 25 and "cursor" not in call for call in directs)
        assert result.message.count("limit 25 is the maximum requested") == 2
        assert "incoming builds are incomplete for the target" in result.message
        assert "related concepts are incomplete for the target" in result.message
        assert not any(p in result.message for p in FIXED_COUNT_PROMISES)
        assert (
            "at most 3 supporting standards" in result.message
            and "at most 10 distinct full" in result.message
        )
        assert (
            "diagnos" in result.message.lower() and "measured mastery" in result.message
        )
        for call in walks:
            TraverseLearningProgressionsRequest.model_validate(call)
        for call in directs:
            GetStandardProgressionsRequest.model_validate(call)


def test_curriculum_review_workflow(accepted_state: AppState) -> None:
    """Review exposes matching scope and a finite subset instead of a coverage claim."""
    for runtime in accepted_state.catalog_load_result.package_runtimes:
        identity = runtime.catalog_package.package_identity
        edge = next(
            e
            for e in runtime.loaded_package.relationships
            if e.label == "buildsTowards"
        )
        result = accepted_state.prompt_service.learning_progression_curriculum_review(
            framework_id=identity.framework_id,
            snapshot_id=identity.snapshot_id,
            endpoint_scope="source",
            standard_identifiers=(selector(edge.source_node_id),),
        )
        calls = templates(result.message)
        # Omitted relationship_types: one single-type scan per type, fixed order.
        assert len(calls) == 4
        GetFrameworkStatisticsRequest.model_validate(calls[0])
        scans = calls[1:3]
        assert [scan["relationshipTypes"] for scan in scans] == [
            ["buildsTowards"],
            ["relatesTo"],
        ]
        assert {
            key: value for key, value in scans[0].items() if key != "relationshipTypes"
        } == {
            key: value for key, value in scans[1].items() if key != "relationshipTypes"
        }
        for scan in scans:
            query = SearchLearningProgressionsRequest.model_validate(scan)
            assert query.endpoint_scope == "source" and query.limit == 25
            assert query.standard_identifiers == (selector(edge.source_node_id),)
            assert query.cursor is None
        GetLearningProgressionRequest.model_validate(
            {**calls[3], "relationshipId": edge.relationship_id}
        )
        assert not any(p in result.message for p in FIXED_COUNT_PROMISES)
        for phrase in [
            "own budget of at most 3 pages",
            "limit 25 is the maximum requested",
            "never reuse a cursor from another scan",
            "never follow a fourth page of a scan",
            "that type's review is incomplete",
            "select up to 5 per type",
            "unused slots to the other type",
            "never sum",
            "at most 10 distinct full",
            "whole conjunction",
            "reviewed subset",
            "unknown denominators",
            "needs_review/no_relation",
            "curriculum omission",
            "producer/checker",
            "source/config/content hashes",
        ]:
            assert phrase.lower() in result.message.lower()


def test_shared_legacy_enrichment(accepted_state: AppState) -> None:
    """All four retained client workflows use the same finite optional LP step."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    common: dict[str, Any] = dict(
        focus_mode=PromptFocusMode.TOPIC,
        framework_id=runtime.catalog_package.package_identity.framework_id,
        local_context=None,
        output_language=None,
        snapshot_id=None,
        topic_or_standard="mathematics",
    )
    grade = runtime.loaded_package.profile.grade_mappings[0].local_label
    service = accepted_state.prompt_service
    results = [
        service.teacher_guide_draft(
            **common,
            available_materials=None,
            grade_or_stage=grade,
            learner_context=None,
            lesson_duration_minutes=45,
        ),
        service.student_study_support(
            **common,
            difficulty=StudyDifficulty.FOUNDATIONAL,
            grade_or_stage=grade,
            practice_count=3,
        ),
        service.student_handbook_section(
            **common, grade_or_stage=grade, target_word_count=500
        ),
        service.multigrade_lesson_plan(
            **common,
            grades_in_room=tuple(
                row.local_label
                for row in runtime.loaded_package.profile.grade_mappings[:2]
            ),
            learner_context=None,
            lesson_duration_minutes=45,
        ),
    ]
    for result in results:
        assert "at most 3 distinct already-resolved standards" in result.message
        assert_per_kind_direct_calls(result.message, "<selected-node-id>")
        assert "at most 10 distinct full edge-provenance" in result.message
        assert "get_learning_components_for_standard" in result.message
        assert (
            "collect_progression_evidence" not in result.message
            and "inferred_progression_hypothesis" not in result.message
        )
        assert "get_standard_context" in result.message
        assert "EVIDENCE ACCESS" in result.message
    assert len({result.prompt_name for result in results}) == 4


def test_prompt_rights_are_enforced(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Prohibited derivatives refuse the prompt before any generated composition."""
    original = CatalogService.get_graph_package

    def deny(self: CatalogService, **kwargs: Any) -> Any:
        """Supply isolated denied catalog rights while retaining the immutable package."""
        package = original(self, **kwargs)
        return package.model_copy(
            update={
                "rights": package.rights.model_copy(
                    update={
                        "allow_generated_derivatives": DerivativeGenerationPolicy.PROHIBITED
                    }
                )
            }
        )

    monkeypatch.setattr(CatalogService, "get_graph_package", deny)
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    with pytest.raises(PromptAccessDeniedError):
        accepted_state.prompt_service.learning_progression_teaching_sequence(
            focus_mode=PromptFocusMode.TOPIC,
            framework_id=runtime.catalog_package.package_identity.framework_id,
            local_context=None,
            local_grade_labels=(),
            normalized_grades=(),
            output_language=None,
            snapshot_id=None,
            topic_or_standard="mathematics",
        )


def test_new_prompt_inputs_are_finite() -> None:
    """Bounded invalid mutations exercise the new prompt's finite input property."""
    base = dict(framework_id="synthetic", topic_or_standard="mathematics")
    updates: list[dict[str, Any]] = [
        {"topic_or_standard": "x" * 513},
        {"local_context": "x" * 4001},
        {"local_grade_labels": tuple(str(i) for i in range(33))},
    ]
    for update in updates:
        with pytest.raises(ValidationError):
            LearningProgressionTeachingSequenceRequest.model_validate(
                {**base, **update}
            )
    LearningProgressionTeachingSequenceRequest.model_validate(base)


def test_unavailable_optional_evidence_has_no_fallback(
    accepted_state: AppState,
) -> None:
    """Unavailable stored LP evidence skips those queries and retains AS/LC work."""
    runtime = accepted_state.catalog_load_result.package_runtimes[0]
    capabilities = runtime.catalog_package.capabilities.model_copy(
        update={
            "has_learning_progressions": False,
            "has_learning_progression_provenance": False,
        }
    )
    # A real runtime rejects capabilities that differ from its manifest, so a
    # namespace double supplies the two attributes the renderer reads.
    projected = SimpleNamespace(
        catalog_package=runtime.catalog_package.model_copy(
            update={"capabilities": capabilities}
        ),
        loaded_package=runtime.loaded_package,
    )
    message = render_optional_progression_workflow(
        runtime=cast(CatalogPackageRuntime, projected)
    )
    assert "unavailable" in message.lower()
    assert "get_standard_progressions" not in message
    assert (
        "continue the existing standards/component workflow and useful output"
        in message
    )
    assert "infer" in message.lower()


@pytest.mark.parametrize(
    "relationship_types",
    [("relatesTo", "relatesTo"), ("hasChild",)],
    ids=["duplicate", "unknown"],
)
def test_review_relationship_types_are_validated(
    relationship_types: tuple[str, ...],
) -> None:
    """Repeated or non-LP relationship types fail before any rendering."""
    base = {"framework_id": "synthetic", "relationship_types": ("relatesTo",)}
    LearningProgressionCurriculumReviewRequest.model_validate(base)
    with pytest.raises(ValidationError):
        LearningProgressionCurriculumReviewRequest.model_validate(
            {**base, "relationship_types": relationship_types}
        )


async def test_rendered_relates_scan_reaches_stored_relates_edges(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """F3: Ghana Mathematics BASIC 5's rendered relatesTo scan returns relatesTo."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    runtime = next(
        item
        for item in accepted_state.catalog_load_result.package_runtimes
        if item.catalog_package.package_identity.framework_id
        == "ghana-nacca-primary-mathematics-basic-4-6"
    )
    stored = {
        edge.relationship_id: edge.label
        for edge in runtime.loaded_package.relationships
        if edge.label in {"buildsTowards", "relatesTo"}
    }
    identity = runtime.catalog_package.package_identity
    message = accepted_state.prompt_service.learning_progression_curriculum_review(
        framework_id=identity.framework_id,
        local_grade_labels=("BASIC 5",),
        snapshot_id=identity.snapshot_id,
    ).message
    scans = [call for call in templates(message) if "relationshipTypes" in call]
    returned: dict[str, list[str]] = {}
    async with Client(create_mcp()) as client:
        # Execute each rendered scan as written: its own cursor, at most 3 pages.
        for scan in scans:
            request, labels = dict(scan), list[str]()
            for _ in range(3):
                result = await client.call_tool(
                    "search_learning_progressions", {"request": request}
                )
                page = ProgressionCollectionResult.model_validate(
                    result.structured_content
                )
                labels.extend(
                    stored[item.relationship.relationship_id]
                    for item in page.relationships
                )
                if page.page.next_cursor is None:
                    break
                request = {**scan, "cursor": page.page.next_cursor}
            returned[scan["relationshipTypes"][0]] = labels
    assert returned["relatesTo"] and set(returned["relatesTo"]) == {"relatesTo"}
    assert returned["buildsTowards"] and set(returned["buildsTowards"]) == {
        "buildsTowards"
    }
