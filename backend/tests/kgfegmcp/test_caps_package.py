"""CAPS English Home Language Grades R-3 served through the generic MCP surface."""

# Standard Library
import json
import re

from collections import Counter
from typing import Any

# Third Party Library
import pytest

from fastmcp import Client

# Package Library
from kgfegmcp.app import create_mcp
from kgfegmcp.bootstrap import AppState
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.errors import CapabilityUnavailableError
from kgfegmcp.services.models import (
    ExactCodeStandardsSearchRequest,
    PrefixCodeStandardsSearchRequest,
    TextStandardsSearchRequest,
)

CAPS = "south-africa-dbe-caps-english-home-language-grades-r-3"
# Item grades as the source encodes them; "K" is CAPS Grade R.
GRADES = {"K": ("Grade R", 385), "1": ("Grade 1", 237), "2": ("Grade 2", 262)}
GRADES["3"] = ("Grade 3", 260)


def _caps(state: AppState) -> CatalogPackageRuntime:
    """Return the accepted CAPS package runtime.

    Parameters
    ----------
    state
        Application state bootstrapped from the accepted packages.

    Returns
    -------
    CatalogPackageRuntime
        The CAPS runtime.
    """

    return next(
        runtime
        for runtime in state.catalog_load_result.package_runtimes
        if runtime.catalog_package.package_identity.framework_id == CAPS
    )


def _hits(state: AppState, **filters: Any) -> set[str]:
    """Collect every CAPS text-search hit for a broad query under optional filters.

    Parameters
    ----------
    state
        Application state holding the standards search service.
    **filters
        Grade filter fields of the search request.

    Returns
    -------
    set[str]
        Node IDs of every hit across all pages.
    """

    service = state.comparison_service.standards_service
    request = TextStandardsSearchRequest(
        framework_ids=(CAPS,),
        limit=100,
        match={"matchMode": "tokens", "operator": "any"},
        mode="text",
        query="words sounds letters read write",
        **filters,
    )
    found: set[str] = set()

    for _ in range(50):
        page = service.search_standards(request).page
        found |= {hit.node.node_id for hit in page.hits}

        if page.next_cursor is None:
            return found

        request = request.model_copy(update={"cursor": page.next_cursor})

    raise AssertionError("CAPS search pagination did not finish.")


def _root(runtime: CatalogPackageRuntime) -> dict[str, Any]:
    """Read the source framework root's properties from the delivered nodes file.

    Parameters
    ----------
    runtime
        Accepted CAPS runtime.

    Returns
    -------
    dict[str, Any]
        Properties of the single ``StandardsFramework`` node.
    """

    nodes = runtime.loaded_package.artifact("nodes")
    assert nodes is not None
    rows = [json.loads(line) for line in nodes.resolved_path.read_text().splitlines()]
    (root,) = [row for row in rows if "StandardsFramework" in row["labels"]]
    return dict(root["properties"])


async def test_caps_identity_rights_and_counts(
    accepted_state: AppState, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CAPS is the seventh accepted framework with its source identity and rights."""
    monkeypatch.setattr("kgfegmcp.app.bootstrap_application", lambda: accepted_state)
    runtime = _caps(accepted_state)
    root = _root(runtime)
    async with Client(create_mcp()) as client:
        listed = await client.call_tool("list_frameworks", {"request": {}})
        framework = await client.call_tool(
            "get_framework", {"request": {"frameworkId": CAPS}}
        )
        statistics = await client.call_tool(
            "get_framework_statistics", {"request": {"frameworkId": CAPS}}
        )
    items = (listed.structured_content or {})["items"]
    assert len(items) == 7 and CAPS in {item["frameworkId"] for item in items}
    served = (framework.structured_content or {})["framework"]
    (package,) = served["graphPackages"]
    assert package["validationStatus"] == "passed"
    assert re.fullmatch(rf"{CAPS}@2011\+[0-9a-f]{{12}}", served["snapshotId"])
    identity = package["packageIdentity"]
    assert (identity["profileId"], identity["profileVersion"]) == (CAPS, "2.0")
    # Scope counts; the relationship total includes the 1,144 hasChild edges.
    assert package["counts"] == {
        "additionalCounts": {
            "codedItems": 0,
            "multiParentTargets": 0,
            "unresolvedRelationships": 0,
        },
        "buildsTowardsRelationships": 2879,
        "frameworkNodes": 1,
        "itemNodes": 1144,
        "learningComponentNodes": 912,
        "relatesToRelationships": 6708,
        "relationships": 11935,
        "supportsRelationships": 1204,
    }
    assert package["rights"] == {
        "allowBulkResource": False,
        "allowFullText": True,
        "allowGeneratedDerivatives": "allowed",
        "allowStandardResources": True,
        "attributionStatement": root["attributionStatement"],
        "licenseUri": None,
        "reviewStatus": "provisional_operator_approved",
        "sourceLicense": root["license"],
    }
    assert root["license"] == "Unknown" and "©" in root["attributionStatement"]
    metadata = (statistics.structured_content or {})["sourceMetadata"]
    assert {
        key: metadata[key]
        for key in (
            "issuingAuthority",
            "jurisdiction",
            "jurisdictionType",
            "localGradesOrStages",
            "localSubject",
            "name",
        )
    } == {
        "issuingAuthority": "Department of Basic Education",
        "jurisdiction": "South Africa",
        "jurisdictionType": "country",
        "localGradesOrStages": ["Grade R", "Grade 1", "Grade 2", "Grade 3"],
        "localSubject": root["academicSubject"],
        "name": root["name"],
    }
    assert root["academicSubject"] == "English Home Language"
    counted = (statistics.structured_content or {})["statistics"]
    assert counted["learningProgressions"]["buildsTowardsRelationships"] == 2879
    assert counted["learningProgressions"]["relatesToRelationships"] == 6708


def test_caps_grade_r_labels_and_filters(accepted_state: AppState) -> None:
    """Source grade K reads as Grade R, and every grade filter selects its items."""
    runtime = _caps(accepted_state)
    grades = Counter(
        grade
        for node in runtime.loaded_package.item_nodes
        for grade in node.grade_level or ()
    )
    assert dict(grades) == {grade: count for grade, (_, count) in GRADES.items()}
    by_node: dict[str, tuple[str, ...] | None] = {
        node.node_id: node.grade_level for node in runtime.loaded_package.item_nodes
    }
    everything = _hits(accepted_state)
    assert len(everything) > 100
    for grade, (label, _) in GRADES.items():
        expected = {node for node in everything if by_node[node] == (grade,)}
        assert expected
        assert _hits(accepted_state, local_grade_labels=(label,)) == expected
        assert _hits(accepted_state, normalized_grades=(grade,)) == expected
    page = (
        accepted_state.comparison_service.standards_service.search_standards(
            TextStandardsSearchRequest(
                framework_ids=(CAPS,),
                local_grade_labels=("Grade R",),
                match={"matchMode": "tokens", "operator": "any"},
                mode="text",
                query="sounds",
            )
        )
    ).page
    assert page.hits
    for hit in page.hits:
        assert hit.facets.normalized_grades == ("K",)
        assert hit.facets.resolved_local_grade_labels == ("Grade R",)


def test_caps_code_search_unavailable(accepted_state: AppState) -> None:
    """CAPS prints no statement codes, so code lookup is refused, never guessed."""
    runtime = _caps(accepted_state)
    assert runtime.catalog_package.capabilities.code_search.value == "none"
    assert all(
        node.statement_code is None for node in runtime.loaded_package.item_nodes
    )
    service = accepted_state.comparison_service.standards_service
    for request in (
        ExactCodeStandardsSearchRequest(
            framework_ids=(CAPS,), mode="code_exact", query="1.1"
        ),
        PrefixCodeStandardsSearchRequest(
            framework_ids=(CAPS,), mode="code_prefix", query="1"
        ),
    ):
        with pytest.raises(CapabilityUnavailableError) as failure:
            service.search_standards(request)
        assert "Available package search modes: text" in str(failure.value)
