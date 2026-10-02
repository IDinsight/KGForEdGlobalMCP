"""Check representative stored progression contracts through any connected transport."""

# Future Library
from __future__ import annotations

# Standard Library
import hashlib
import json

from collections.abc import Mapping

# Third Party Library
from fastmcp import Client
from fastmcp.utilities.json_schema import compress_schema

# Package Library
from kgfegmcp.domain.identifiers import FrameworkId, RelationshipId, SnapshotId
from kgfegmcp.services.lp_models import (
    GetLearningProgressionPathsRequest,
    GetLearningProgressionPathsResult,
    GetLearningProgressionRequest,
    GetLearningProgressionResult,
    GetStandardProgressionsRequest,
    ProgressionCollectionResult,
    ProgressionEvidenceResult,
    SearchLearningProgressionsRequest,
    TraverseLearningProgressionsRequest,
    TraverseLearningProgressionsResult,
)

_REQUEST_MODELS = {
    "get_learning_progression": GetLearningProgressionRequest,
    "get_learning_progression_paths": GetLearningProgressionPathsRequest,
    "get_standard_progressions": GetStandardProgressionsRequest,
    "search_learning_progressions": SearchLearningProgressionsRequest,
    "traverse_learning_progressions": TraverseLearningProgressionsRequest,
}
_RESULT_MODELS: Mapping[str, type[ProgressionEvidenceResult]] = {
    "get_learning_progression": GetLearningProgressionResult,
    "get_learning_progression_paths": GetLearningProgressionPathsResult,
    "get_standard_progressions": ProgressionCollectionResult,
    "search_learning_progressions": ProgressionCollectionResult,
    "traverse_learning_progressions": TraverseLearningProgressionsResult,
}


def _query_requests(
    *, exact: GetLearningProgressionResult, route: dict[str, object]
) -> tuple[tuple[str, dict[str, object]], ...]:
    """Build four bounded requests around the exact representative stored edge.

    Parameters
    ----------
    exact
        Exact lookup with one retained directional relationship.
    route
        Pinned framework and immutable snapshot.

    Returns
    -------
    tuple[tuple[str, dict[str, object]], ...]
        Tool names and nested request payloads for direct, discovery, walk and path.
    """

    edge = exact.relationships[0].relationship
    source = {"identifierType": "node_id", "nodeId": str(edge.source_node_id)}
    target = {"identifierType": "node_id", "nodeId": str(edge.target_node_id)}
    return (
        (
            "get_standard_progressions",
            {
                **route,
                "connectionKind": "outgoing_builds",
                "identifier": source,
                "limit": 25,
            },
        ),
        (
            "search_learning_progressions",
            {
                **route,
                "endpointScope": "source",
                "limit": 25,
                "relationshipTypes": ["buildsTowards"],
                "standardIdentifiers": [source],
            },
        ),
        (
            "traverse_learning_progressions",
            {
                **route,
                "direction": "downstream",
                "identifier": source,
                "maxDepth": 1,
                "maxEdges": 25,
                "maxNodes": 30,
            },
        ),
        (
            "get_learning_progression_paths",
            {
                **route,
                "maxDepth": 1,
                "maxPaths": 1,
                "sourceIdentifier": source,
                "targetIdentifier": target,
            },
        ),
    )


async def _read_query(
    *, client: Client, name: str, request: dict[str, object]
) -> ProgressionEvidenceResult:
    """Execute a real nested request and validate the full operation result.

    Parameters
    ----------
    client
        Connected transport client.
    name
        Approved progression tool name.
    request
        Exact bounded request body.

    Returns
    -------
    ProgressionEvidenceResult
        Validated operation-specific evidence and completeness model.

    Raises
    ------
    RuntimeError
        If a tool reports failure instead of structured evidence.
    """

    _REQUEST_MODELS[name].model_validate(request)
    result = await client.call_tool(name=name, arguments={"request": request})

    if result.is_error:
        raise RuntimeError(f"Progression smoke tool failed: {name}.")

    return _RESULT_MODELS[name].model_validate(result.structured_content)


def _require_edge(
    *, expected: GetLearningProgressionResult, result: ProgressionEvidenceResult
) -> None:
    """Require each query to preserve the exact generated edge and package identity.

    Parameters
    ----------
    expected
        Exact original relationship returned by lookup.
    result
        One bounded query's typed result.

    Raises
    ------
    RuntimeError
        If the edge is missing, changed or routed into a different package.
    """

    if (
        expected.relationships[0] not in result.relationships
        or result.metadata != expected.metadata
    ):
        raise RuntimeError(
            "Progression query lost the exact edge or evidence identity."
        )

    if isinstance(result, GetLearningProgressionPathsResult):
        edge = expected.relationships[0].relationship

        if not any(
            path.relationship_ids == (edge.relationship_id,)
            and path.node_ids == (edge.source_node_id, edge.target_node_id)
            for path in result.paths
        ):
            raise RuntimeError("Progression path lost the stored directed hop.")


async def progression_schema_identities(client: Client) -> dict[str, str]:
    """Validate nested request schemas and fingerprint all tool contracts.

    Parameters
    ----------
    client
        Connected client used by either transport smoke command.

    Returns
    -------
    dict[str, str]
        Sorted tool names and exact input/output schema SHA-256 identities.

    Raises
    ------
    RuntimeError
        If a progression tool's nested request schema differs from its service model.
    """

    identities: dict[str, str] = {}

    for tool in sorted(await client.list_tools(), key=lambda item: item.name):
        schema = tool.inputSchema

        if tool.name in _REQUEST_MODELS:
            model = _REQUEST_MODELS[tool.name]
            expected = compress_schema(
                dereference=True,
                prune_titles=True,
                schema=model.model_json_schema(by_alias=True),
            )
            actual = dict(schema.get("properties", {}).get("request", {}))

            # FastMCP uses the adapter parameter description at the request root.
            expected.pop("description", None)
            actual.pop("description", None)

            if (
                schema.get("required") != ["request"]
                or set(schema.get("properties", {})) != {"request"}
                or actual != expected
            ):
                raise RuntimeError(f"Unexpected nested request schema: {tool.name}.")

        payload = json.dumps(
            obj={"input": schema, "output": tool.outputSchema}, sort_keys=True
        ).encode("utf-8")
        identities[tool.name] = "sha256:" + hashlib.sha256(payload).hexdigest()

    return identities


async def verify_progression_queries(
    *,
    client: Client,
    framework_id: FrameworkId,
    relationship_id: RelationshipId,
    snapshot_id: SnapshotId,
) -> dict[str, object]:
    """Exercise all five stored-edge tools and one exact missing-edge error.

    Parameters
    ----------
    client
        Connected MCP client.
    framework_id
        Known representative framework.
    relationship_id
        Known stored buildsTowards relationship.
    snapshot_id
        Accepted replacement snapshot shared by all requests.

    Returns
    -------
    dict[str, object]
        Deterministic requests, result identities and typed error evidence.

    Raises
    ------
    RuntimeError
        If any operation loses stored evidence or fails the expected error contract.
    """

    route: dict[str, object] = {
        "frameworkId": str(framework_id),
        "snapshotId": str(snapshot_id),
    }
    request = {**route, "relationshipId": str(relationship_id)}
    exact = GetLearningProgressionResult.model_validate(
        await _read_query(
            client=client, name="get_learning_progression", request=request
        )
    )

    if (
        len(exact.relationships) != 1
        or exact.relationships[0].relationship.label != "buildsTowards"
    ):
        raise RuntimeError("Exact smoke lookup did not return one directional edge.")

    reads: list[dict[str, object]] = []

    for name, payload in (
        ("get_learning_progression", request),
        *_query_requests(exact=exact, route=route),
    ):
        result = (
            exact
            if name == "get_learning_progression"
            else await _read_query(client=client, name=name, request=payload)
        )
        _require_edge(expected=exact, result=result)
        reads.append(
            {
                "name": name,
                "request": payload,
                "resultSha256": "sha256:"
                + hashlib.sha256(
                    result.model_dump_json(by_alias=True).encode("utf-8")
                ).hexdigest(),
            }
        )

    missing = await client.call_tool(
        name="get_learning_progression",
        arguments={"request": {**route, "relationshipId": "smoke-missing-edge"}},
        raise_on_error=False,
    )

    if not missing.is_error or "learning_progression_not_found" not in str(
        missing.content
    ):
        raise RuntimeError("Missing progression did not return its typed error.")

    return {
        "queries": reads,
        "queryCount": 6,
        "missingEdgeError": "learning_progression_not_found",
    }
