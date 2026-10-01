"""Independent LP endpoint, pair and directed-cycle acceptance checks."""

# Standard Library
from collections import Counter, defaultdict
from collections.abc import Iterator
from typing import Final

# Package Library
from kgfegmcp.domain.enums import GraphType
from kgfegmcp.graph.models import GraphRelationship
from kgfegmcp.packages.models import LoadedGraphPackage, PackageValidationFinding

LP_TYPES: Final[frozenset[str]] = frozenset({"buildsTowards", "relatesTo"})


def _cycle_witness(edges: tuple[GraphRelationship, ...]) -> tuple[str, ...]:
    """Find one exact directed cycle without recursive depth limits.

    Parameters
    ----------
    edges
        Builds-only directed edges.

    Returns
    -------
    tuple[str, ...]
        Relationship IDs around a cycle, or empty when acyclic.

    Examples
    --------
    >>> _cycle_witness(())
    ()
    """

    adjacency: dict[str, list[tuple[str, str]]] = defaultdict(list)

    for edge in edges:
        adjacency[str(edge.source_node_id)].append(
            (str(edge.target_node_id), str(edge.relationship_id))
        )

    visited: set[str] = set()

    for start in sorted(adjacency):
        if start in visited:
            continue

        active = {start: 0}
        path: list[str] = []
        stack: list[tuple[str, Iterator[tuple[str, str]]]] = [
            (start, iter(adjacency[start]))
        ]
        visited.add(start)

        while stack:
            node, children = stack[-1]
            child = next(children, None)

            if child is None:
                del active[node]
                stack.pop()

                if path:
                    path.pop()

                continue

            target, identifier = child

            if target in active:
                return (*path[active[target] :], identifier)

            if target not in visited:
                visited.add(target)
                active[target] = len(path) + 1
                path.append(identifier)
                stack.append((target, iter(adjacency[target])))

    return ()


def _edge_findings(
    *, edge: GraphRelationship, standards: dict[str, str | None]
) -> tuple[PackageValidationFinding, ...]:
    """Require standard-only exact CASE endpoints and clean LP identity fields.

    Parameters
    ----------
    edge
        One stored LP edge.
    standards
        Original standards outer IDs mapped to CASE selectors.

    Returns
    -------
    tuple[PackageValidationFinding, ...]
        Endpoint and representation errors.

    Examples
    --------
    >>> bool(_edge_findings(edge=lp_edge, standards={}))
    True
    """

    checks = {
        "lp_endpoint_mismatch": (
            str(edge.source_node_id) in standards
            and str(edge.target_node_id) in standards
            and standards.get(str(edge.source_node_id)) == edge.source_entity_value
            and standards.get(str(edge.target_node_id)) == edge.target_entity_value
            and edge.source_entity_value is not None
            and edge.target_entity_value is not None
        ),
        "lp_identity_mismatch": (
            edge.property_identifier == edge.relationship_id
            and edge.relationship_type == edge.label
            and edge.source_labels == edge.target_labels == ("StandardsFrameworkItem",)
            and edge.source_entity == edge.target_entity == "StandardsFrameworkItem"
            and edge.source_entity_key == edge.target_entity_key == "caseIdentifierUUID"
        ),
        "lp_self_edge": edge.source_node_id != edge.target_node_id,
        "lp_foreign_resolution_metadata": (
            edge.resolution_status is None and edge.support_confidence is None
        ),
        "lp_relates_to_order": (
            edge.label != "relatesTo"
            or (edge.source_entity_value or "") < (edge.target_entity_value or "")
        ),
    }
    return tuple(
        PackageValidationFinding(
            code=code,
            message="An LP relationship violates its stored graph contract.",
            record_id=str(edge.relationship_id),
        )
        for code, passed in checks.items()
        if not passed
    )


def validate_learning_progression_graph(
    package: LoadedGraphPackage,
) -> tuple[PackageValidationFinding, ...]:
    """Check LP declarations, counts, pair exclusivity and builds-only cycles.

    Parameters
    ----------
    package
        Decoded immutable graph package.

    Returns
    -------
    tuple[PackageValidationFinding, ...]
        Independent LP graph findings, separate from hasChild validation.

    Examples
    --------
    >>> validate_learning_progression_graph(valid_package)
    ()
    """

    edges = tuple(edge for edge in package.relationships if edge.label in LP_TYPES)
    findings: list[PackageValidationFinding] = []
    declared = GraphType.LEARNING_PROGRESSIONS in package.manifest.included_graph_types

    lp_artifacts = any(
        str(reference.logical_name).startswith("learningProgression")
        for reference in package.artifacts
    )

    if (edges or lp_artifacts) and not declared:
        findings.append(
            PackageValidationFinding(
                code="lp_undeclared", message="LP edges require declared LP evidence."
            )
        )

    if declared and package.learning_progression_evidence is None:
        findings.append(
            PackageValidationFinding(
                code="lp_evidence_not_validated",
                message="Declared LP evidence has not passed independent validation.",
            )
        )

    counts = Counter(edge.label for edge in edges)
    expected = {
        "buildsTowards": package.manifest.counts.builds_towards_relationships,
        "relatesTo": package.manifest.counts.relates_to_relationships,
    }

    if any(counts[label] != value for label, value in expected.items()):
        findings.append(
            PackageValidationFinding(
                code="lp_manifest_count_mismatch",
                message="Manifest LP counts disagree with decoded LP edges.",
            )
        )

    standards = {
        str(node.node_id): node.case_identifier_uuid for node in package.item_nodes
    }
    pairs: dict[tuple[str, ...], str] = {}
    identifiers: set[str] = set()

    for edge in edges:
        findings.extend(_edge_findings(edge=edge, standards=standards))
        identifier = str(edge.relationship_id)
        pair = tuple(
            sorted((edge.source_entity_value or "", edge.target_entity_value or ""))
        )

        if pair in pairs or identifier in identifiers:
            findings.append(
                PackageValidationFinding(
                    code="lp_pair_conflict",
                    details={"other_relationship_id": pairs.get(pair)},
                    message="An LP pair or relationship ID is published more than once.",
                    record_id=identifier,
                )
            )

        pairs[pair] = identifier
        identifiers.add(identifier)

    cycle = _cycle_witness(
        tuple(edge for edge in edges if edge.label == "buildsTowards")
    )

    if cycle:
        findings.append(
            PackageValidationFinding(
                code="lp_builds_towards_cycle",
                details={"relationship_ids": cycle},
                message="Stored buildsTowards relationships contain a directed cycle.",
            )
        )

    return tuple(findings)
