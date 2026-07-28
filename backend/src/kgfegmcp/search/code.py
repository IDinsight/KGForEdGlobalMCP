"""This module builds and queries immutable profile-governed package-local code indexes.

This module creates one independent statement-code index for each accepted graph
package. Every indexed posting retains the exact source node, authored code, normalized
lookup value, configured code type, and package-local scope evidence.

Code normalization and prefix behavior come only from the exact curriculum profile
loaded with the package. Exact lookup may return multiple source records because a code
is not assumed to be a globally unique identifier. Prefix lookup is available only when
the profile explicitly enables it and matches only exact values or configured delimiter
boundaries.

Configured code-parent rules produce retrieval evidence only. They never create,
replace, or reinterpret graph relationships. The existing package
`~kgfegmcp.graph.store.GraphStore` remains authoritative for hierarchy, parentage,
identifiers, and traversal.

All indexing and lookup remain package-local. This module does not read package files,
load settings, validate packages, merge code namespaces, infer instructional sequence,
or add curriculum-specific behavior.
"""

# Future Library
from __future__ import annotations

# Standard Library
import re

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

# Package Library
from kgfegmcp.catalog.models import CatalogPackageRuntime
from kgfegmcp.domain.enums import CodeAvailability
from kgfegmcp.domain.identifiers import NodeId
from kgfegmcp.errors import CatalogError
from kgfegmcp.graph.models import (
    GraphPackageIdentity,
    StandardNode,
    graph_node_order_key,
)
from kgfegmcp.profiles.models import (
    CodeSearchPolicy,
    CurriculumProfile,
    StatementTypePolicy,
)
from kgfegmcp.search.models import CodeParentDerivationStatus
from kgfegmcp.search.normalizers import CodeNormalizer, normalize_facet_value

CodeTypeAndValueKey = tuple[str, str]
PostingIdentityKey = tuple[str, tuple[tuple[str, str], ...], str]


@dataclass(frozen=True, slots=True)
class CodePosting:
    """Retain one exact source code record and its package-local scope evidence."""

    authored_code: str
    code_type: str
    node: StandardNode
    normalized_code: str
    scope_key: tuple[tuple[str, str], ...]
    scopes: tuple[StandardNode, ...]


@dataclass(frozen=True, slots=True)
class CodeCandidate:
    """Return one package-local code match and its normalized query key."""

    is_exact_match: bool
    normalized_query: str
    posting: CodePosting


@dataclass(frozen=True, slots=True)
class ParentCodeDerivation:
    """Return internal deterministic evidence for one configured parent-code rule."""

    child_code_type: str
    derived_code: str
    matched_parent_nodes: tuple[StandardNode, ...]
    normalized_derived_code: str
    parent_code_type: str
    status: CodeParentDerivationStatus


@dataclass(frozen=True, slots=True)
class CodeIndex:
    """Own one immutable code index for exactly one accepted graph package."""

    normalizer: CodeNormalizer
    package_identity: GraphPackageIdentity
    policy: CodeSearchPolicy
    postings: tuple[CodePosting, ...]
    postings_by_code_type_and_value: Mapping[
        CodeTypeAndValueKey, tuple[CodePosting, ...]
    ]
    postings_by_normalized_code: Mapping[str, tuple[CodePosting, ...]]

    @classmethod
    def from_runtime(cls, runtime: CatalogPackageRuntime) -> CodeIndex:
        """Build one package-local code index from an accepted catalog runtime.

        Parameters
        ----------
        runtime
            Exact accepted runtime whose profile and graph store govern the index.

        Returns
        -------
        CodeIndex
            Immutable package-local exact and optional prefix code index.

        Raises
        ------
        CatalogError
            If accepted source records cannot satisfy the operational profile contract.
        """

        profile = runtime.loaded_package.profile
        policy = profile.code_search_policy
        normalizer = CodeNormalizer.from_policy(policy)
        _require_capability_consistency(runtime)
        _require_supported_parent_rules(policy)
        statement_policies = _build_statement_policy_index(profile)
        code_type_policies = {
            str(code_type.code_type): code_type for code_type in policy.code_types
        }
        scope_resolver = _CodeScopeResolver(
            runtime=runtime, statement_policies_by_key=statement_policies
        )
        postings: list[CodePosting] = []

        for node in runtime.loaded_package.item_nodes:
            if node.statement_code is None:
                continue

            statement_policy = _resolve_statement_policy(
                node=node, policies_by_key=statement_policies
            )
            code_type_name = statement_policy.code_type

            if code_type_name is None:
                raise CatalogError(
                    details={
                        "graph_package_id": str(
                            runtime.catalog_package.package_identity.graph_package_id
                        ),
                        "node_id": str(node.node_id),
                        "statement_type": node.statement_type,
                    },
                    message=(
                        "An accepted coded node has no profile-governed code type."
                    ),
                )

            code_type_policy = code_type_policies.get(str(code_type_name))

            if code_type_policy is None:
                raise CatalogError(
                    details={
                        "code_type": str(code_type_name),
                        "graph_package_id": str(
                            runtime.catalog_package.package_identity.graph_package_id
                        ),
                        "node_id": str(node.node_id),
                    },
                    message=(
                        "An accepted coded node references an unavailable code " "type."
                    ),
                )

            try:
                normalized_code = normalizer.normalize(node.statement_code)
            except ValueError as error:
                raise CatalogError(
                    details={
                        "graph_package_id": str(
                            runtime.catalog_package.package_identity.graph_package_id
                        ),
                        "node_id": str(node.node_id),
                    },
                    message="An accepted source statement code normalizes to no value.",
                ) from error

            if (
                statement_policy.source_statement_type
                not in code_type_policy.statement_types
            ):
                raise CatalogError(
                    details={
                        "code_type": str(code_type_name),
                        "graph_package_id": str(
                            runtime.catalog_package.package_identity.graph_package_id
                        ),
                        "node_id": str(node.node_id),
                        "statement_type": statement_policy.source_statement_type,
                    },
                    message=(
                        "An accepted coded node is not permitted by its resolved "
                        "code-type policy."
                    ),
                )

            scopes = scope_resolver.resolve(
                node=node, scope_statement_types=code_type_policy.scope_statement_types
            )
            scope_key = _build_scope_key(
                policies_by_key=statement_policies, scopes=scopes
            )
            postings.append(
                CodePosting(
                    authored_code=node.statement_code,
                    code_type=str(code_type_name),
                    node=node,
                    normalized_code=normalized_code,
                    scope_key=scope_key,
                    scopes=scopes,
                )
            )

        postings_by_normalized_code = _group_postings_by_normalized_code(
            tuple(postings)
        )
        postings_by_code_type_and_value = _group_postings_by_code_type_and_value(
            tuple(postings)
        )
        _require_configured_uniqueness(policy=policy, postings=tuple(postings))

        return cls(
            normalizer=normalizer,
            package_identity=runtime.catalog_package.package_identity,
            policy=policy,
            postings=tuple(postings),
            postings_by_code_type_and_value=MappingProxyType(
                postings_by_code_type_and_value
            ),
            postings_by_normalized_code=MappingProxyType(postings_by_normalized_code),
        )

    @property
    def allow_prefix_search(self) -> bool:
        """Return whether the exact profile enables delimiter-boundary prefix search.

        Returns
        -------
        bool
            Profile-governed prefix-search availability.
        """

        return self.policy.allow_prefix_search

    @property
    def availability(self) -> CodeAvailability:
        """Return exact profile code-coverage availability.

        Returns
        -------
        CodeAvailability
            Complete, partial, or no code coverage.
        """

        return self.policy.availability

    @property
    def coded_node_count(self) -> int:
        """Return the number of exact coded source nodes retained in the index.

        Returns
        -------
        int
            Number of package-local code postings.
        """

        return len(self.postings)

    @property
    def normalized_code_key_count(self) -> int:
        """Return the number of distinct normalized code surfaces.

        Returns
        -------
        int
            Number of package-local normalized code keys.
        """

        return len(self.postings_by_normalized_code)

    def exact_candidates(self, query: str) -> tuple[CodeCandidate, ...]:
        """Return every exact normalized-code source record for one package.

        Parameters
        ----------
        query
            Raw caller-supplied exact code query.

        Returns
        -------
        tuple[CodeCandidate, ...]
            All matching source records in deterministic source tuple order.
        """

        normalized_query = self.normalizer.normalize(query)
        postings = (
            self.postings_by_normalized_code[normalized_query]
            if normalized_query in self.postings_by_normalized_code
            else ()
        )
        return tuple(
            CodeCandidate(
                is_exact_match=True, normalized_query=normalized_query, posting=posting
            )
            for posting in postings
        )

    def parent_derivations(
        self, posting: CodePosting
    ) -> tuple[ParentCodeDerivation, ...]:
        """Return configured parent-code evidence without changing graph topology.

        Parameters
        ----------
        posting
            Exact matched child-code posting.

        Returns
        -------
        tuple[ParentCodeDerivation, ...]
            Deterministically ordered evidence for applicable configured rules.
        """

        derivations: list[ParentCodeDerivation] = []

        for rule in self.policy.code_parent_rules:
            if str(rule.child_code_type) != posting.code_type:
                continue

            match = re.fullmatch(pattern=rule.regex, string=posting.authored_code)

            if match is None:
                continue

            try:
                derived_code = re.sub(
                    count=1,
                    pattern=rule.regex,
                    repl=rule.replacement,
                    string=posting.authored_code,
                )
                normalized_derived_code = self.normalizer.normalize(derived_code)
            except (re.error, ValueError) as error:
                raise CatalogError(
                    details={
                        "child_code_type": str(rule.child_code_type),
                        "graph_package_id": str(self.package_identity.graph_package_id),
                        "node_id": str(posting.node.node_id),
                        "parent_code_type": str(rule.parent_code_type),
                    },
                    message=(
                        "A configured parent-code rule could not produce deterministic "
                        "non-empty evidence."
                    ),
                ) from error
            candidate_key = str(rule.parent_code_type), normalized_derived_code
            parent_postings = (
                self.postings_by_code_type_and_value[candidate_key]
                if candidate_key in self.postings_by_code_type_and_value
                else ()
            )
            compatible_postings = tuple(
                parent_posting
                for parent_posting in parent_postings
                if _scopes_are_compatible(
                    child_posting=posting, parent_posting=parent_posting
                )
            )
            matched_parent_nodes = tuple(
                parent_posting.node for parent_posting in compatible_postings
            )
            status = _parent_derivation_status(
                matched_parent_count=len(matched_parent_nodes)
            )
            derivations.append(
                ParentCodeDerivation(
                    child_code_type=str(rule.child_code_type),
                    derived_code=derived_code,
                    matched_parent_nodes=matched_parent_nodes,
                    normalized_derived_code=normalized_derived_code,
                    parent_code_type=str(rule.parent_code_type),
                    status=status,
                )
            )

        return tuple(derivations)

    def prefix_candidates(self, query: str) -> tuple[CodeCandidate, ...]:
        """Return exact and delimiter-descendant code-prefix candidates.

        Parameters
        ----------
        query
            Raw caller-supplied code-prefix query.

        Returns
        -------
        tuple[CodeCandidate, ...]
            Matching source records in source tuple order before global code ordering.
        """

        normalized_query = self.normalizer.normalize_prefix(query)
        return tuple(
            CodeCandidate(
                is_exact_match=(posting.normalized_code == normalized_query),
                normalized_query=normalized_query,
                posting=posting,
            )
            for posting in self.postings
            if self.normalizer.is_prefix_match(
                candidate=posting.normalized_code, prefix=normalized_query
            )
        )


@dataclass(slots=True)
class _CodeScopeResolver:
    """Resolve and memoize nearest scope nodes during package-index construction."""

    runtime: CatalogPackageRuntime
    statement_policies_by_key: Mapping[str, StatementTypePolicy]
    _cache: dict[tuple[NodeId, str], tuple[StandardNode, ...]] = field(
        default_factory=dict, init=False, repr=False
    )

    def resolve(
        self, *, node: StandardNode, scope_statement_types: tuple[str, ...]
    ) -> tuple[StandardNode, ...]:
        """Resolve every nearest scope statement type across all authored parent paths.

        Parameters
        ----------
        node
            Exact coded source node whose configured scope is required.
        scope_statement_types
            Ordered source statement types that define code scope.

        Returns
        -------
        tuple[StandardNode, ...]
            Deterministically ordered exact scope node instances.

        Raises
        ------
        CatalogError
            If any configured scope type cannot be resolved for the coded node.
        """

        if not scope_statement_types:
            return ()

        graph_package_id = (
            self.runtime.catalog_package.package_identity.graph_package_id
        )
        resolved_scopes: list[StandardNode] = []

        for scope_statement_type in scope_statement_types:
            target_policy = self.statement_policies_by_key.get(
                normalize_facet_value(scope_statement_type)
            )

            if target_policy is None:
                raise CatalogError(
                    details={
                        "graph_package_id": str(graph_package_id),
                        "node_id": str(node.node_id),
                        "scope_statement_type": scope_statement_type,
                    },
                    message=(
                        "A configured code scope has no resolvable statement-type policy."
                    ),
                )

            scopes = self._resolve_one_type(
                node_id=node.node_id,
                scope_statement_type=target_policy.source_statement_type,
                visited=frozenset(),
            )

            if not scopes:
                raise CatalogError(
                    details={
                        "graph_package_id": str(graph_package_id),
                        "node_id": str(node.node_id),
                        "scope_statement_type": scope_statement_type,
                    },
                    message=(
                        "An accepted coded node has no resolvable configured "
                        "code scope."
                    ),
                )

            resolved_scopes.extend(scopes)

        unique_scopes = {scope.node_id: scope for scope in resolved_scopes}
        ordered_scopes = list(unique_scopes.values())
        ordered_scopes.sort(key=graph_node_order_key)
        return tuple(ordered_scopes)

    def _resolve_one_type(
        self, *, node_id: NodeId, scope_statement_type: str, visited: frozenset[NodeId]
    ) -> tuple[StandardNode, ...]:
        """Resolve nearest matching ancestors independently across every parent branch.

        Parameters
        ----------
        node_id
            Current package-local graph node identifier.
        scope_statement_type
            Exact configured source statement type sought on each parent branch.
        visited
            Branch-local node identifiers used as a defensive cycle guard.

        Returns
        -------
        tuple[StandardNode, ...]
            Exact nearest matching scope nodes in deterministic graph order.

        Raises
        ------
        CatalogError
            If a cycle is observed despite the accepted DAG precondition.
        """

        cache_key = node_id, scope_statement_type

        if cache_key in self._cache:
            return self._cache[cache_key]

        if node_id in visited:
            raise CatalogError(
                details={
                    "graph_package_id": str(
                        self.runtime.catalog_package.package_identity.graph_package_id
                    ),
                    "node_id": str(node_id),
                },
                message="Code-scope resolution encountered a graph cycle.",
            )

        next_visited = visited.union({node_id})
        parent_result = self.runtime.graph_store.direct_parents(node_id=node_id)
        matches: list[StandardNode] = []

        for neighbor in parent_result.neighbors:
            parent = neighbor.node

            if not isinstance(parent, StandardNode):
                continue

            parent_policy = _resolve_optional_statement_policy(
                node=parent, policies_by_key=self.statement_policies_by_key
            )

            if (
                parent_policy is not None
                and parent_policy.source_statement_type == scope_statement_type
            ):
                matches.append(parent)
                continue

            matches.extend(
                self._resolve_one_type(
                    node_id=parent.node_id,
                    scope_statement_type=scope_statement_type,
                    visited=next_visited,
                )
            )

        unique_matches = {match.node_id: match for match in matches}
        ordered_matches = list(unique_matches.values())
        ordered_matches.sort(key=graph_node_order_key)
        result = tuple(ordered_matches)
        self._cache[cache_key] = result
        return result


def _build_scope_key(
    *,
    policies_by_key: Mapping[str, StatementTypePolicy],
    scopes: tuple[StandardNode, ...],
) -> tuple[tuple[str, str], ...]:
    """Build one canonical configured scope key from exact scope nodes.

    Parameters
    ----------
    policies_by_key
        Package-local normalized statement-type policy lookup.
    scopes
        Exact configured scope nodes in deterministic graph order.

    Returns
    -------
    tuple[tuple[str, str], ...]
        Canonical source statement type and exact package-local node ID pairs.

    Raises
    ------
    CatalogError
        If a resolved scope node no longer maps to an exact profile policy.
    """

    scope_key: list[tuple[str, str]] = []

    for scope in scopes:
        policy = _resolve_optional_statement_policy(
            node=scope, policies_by_key=policies_by_key
        )

        if policy is None:
            raise CatalogError(
                details={
                    "node_id": str(scope.node_id),
                    "statement_type": scope.statement_type,
                },
                message=(
                    "A resolved code-scope node has no canonical statement-type policy."
                ),
            )

        scope_key.append((policy.source_statement_type, str(scope.node_id)))

    return tuple(scope_key)


def _build_statement_policy_index(
    profile: CurriculumProfile,
) -> Mapping[str, StatementTypePolicy]:
    """Build a collision-checked normalized statement-type policy index.

    Parameters
    ----------
    profile
        Exact loaded curriculum profile.

    Returns
    -------
    Mapping[str, StatementTypePolicy]
        Canonical and alias keys mapped to exact profile policy objects.

    Raises
    ------
    CatalogError
        If normalized canonical values or aliases collide.
    """

    policies_by_key: dict[str, StatementTypePolicy] = {}

    for policy in profile.statement_types:
        values = (policy.source_statement_type, *policy.aliases)

        for value in values:
            key = normalize_facet_value(value)
            existing = policies_by_key.get(key)

            if existing is not None and existing is not policy:
                raise CatalogError(
                    details={
                        "facet_key": key,
                        "profile_id": str(profile.profile_id),
                        "profile_version": str(profile.profile_version),
                    },
                    message=(
                        "Statement-type profile values collide after deterministic "
                        "normalization."
                    ),
                )

            policies_by_key[key] = policy

    return MappingProxyType(policies_by_key)


def _group_postings_by_code_type_and_value(
    postings: tuple[CodePosting, ...],
) -> dict[CodeTypeAndValueKey, tuple[CodePosting, ...]]:
    """Group source-order postings by code type and normalized code.

    Parameters
    ----------
    postings
        Complete package-local code postings in source tuple order.

    Returns
    -------
    dict[CodeTypeAndValueKey, tuple[CodePosting, ...]]
        Immutable-ready exact lookup groups.
    """

    mutable_groups: dict[CodeTypeAndValueKey, list[CodePosting]] = {}

    for posting in postings:
        key = posting.code_type, posting.normalized_code
        if key not in mutable_groups:
            mutable_groups[key] = []

        mutable_groups[key].append(posting)

    return {key: tuple(group) for key, group in sorted(mutable_groups.items())}


def _group_postings_by_normalized_code(
    postings: tuple[CodePosting, ...],
) -> dict[str, tuple[CodePosting, ...]]:
    """Group source-order postings by normalized code regardless of code type.

    Parameters
    ----------
    postings
        Complete package-local code postings in source tuple order.

    Returns
    -------
    dict[str, tuple[CodePosting, ...]]
        Immutable-ready exact lookup groups.
    """

    mutable_groups: dict[str, list[CodePosting]] = {}

    for posting in postings:
        if posting.normalized_code not in mutable_groups:
            mutable_groups[posting.normalized_code] = []

        mutable_groups[posting.normalized_code].append(posting)

    return {key: tuple(group) for key, group in sorted(mutable_groups.items())}


def _parent_derivation_status(
    *, matched_parent_count: int
) -> CodeParentDerivationStatus:
    """Map one deterministic parent-candidate count to public evidence status.

    Parameters
    ----------
    matched_parent_count
        Number of compatible exact parent-code postings.

    Returns
    -------
    CodeParentDerivationStatus
        Not found, uniquely matched, or multiply matched.
    """

    if matched_parent_count == 0:
        return CodeParentDerivationStatus.NOT_FOUND

    if matched_parent_count == 1:
        return CodeParentDerivationStatus.MATCHED_UNIQUE

    return CodeParentDerivationStatus.MATCHED_MULTIPLE


def _require_capability_consistency(runtime: CatalogPackageRuntime) -> None:
    """Require accepted manifest and profile code capabilities to remain identical.

    Parameters
    ----------
    runtime
        Exact accepted catalog package runtime.

    Raises
    ------
    CatalogError
        If immutable accepted inputs disagree about code-search availability.
    """

    manifest_availability = runtime.loaded_package.manifest.capabilities.code_search
    profile_availability = (
        runtime.loaded_package.profile.code_search_policy.availability
    )

    if manifest_availability is profile_availability:
        return

    raise CatalogError(
        details={
            "graph_package_id": str(
                runtime.catalog_package.package_identity.graph_package_id
            ),
            "manifest_availability": manifest_availability.value,
            "profile_availability": profile_availability.value,
        },
        message=(
            "Accepted package manifest and profile code-search capabilities disagree."
        ),
    )


def _require_configured_uniqueness(
    *, policy: CodeSearchPolicy, postings: tuple[CodePosting, ...]
) -> None:
    """Enforce only profile-declared code uniqueness within exact scope.

    Parameters
    ----------
    policy
        Exact profile code-search policy.
    postings
        Complete package-local code postings.

    Raises
    ------
    CatalogError
        If a profile declaring unique codes contains a same-type, same-scope collision.
    """

    if not policy.codes_are_unique_identifiers:
        return

    postings_by_identity: dict[PostingIdentityKey, CodePosting] = {}

    for posting in postings:
        identity_key = (posting.code_type, posting.scope_key, posting.normalized_code)
        existing = postings_by_identity.get(identity_key)

        if existing is not None:
            raise CatalogError(
                details={
                    "first_node_id": str(existing.node.node_id),
                    "normalized_code": posting.normalized_code,
                    "second_node_id": str(posting.node.node_id),
                },
                message=(
                    "A profile declaring unique code identifiers contains a scoped "
                    "normalized-code collision."
                ),
            )

        postings_by_identity[identity_key] = posting


def _require_supported_parent_rules(policy: CodeSearchPolicy) -> None:
    """Require every configured parent-code rule to use the supported method.

    Parameters
    ----------
    policy
        Exact profile code-search policy.

    Raises
    ------
    CatalogError
        If a configured rule method has no deterministic PR 7 implementation.
    """

    unsupported_methods = tuple(
        sorted(
            {
                str(rule.method)
                for rule in policy.code_parent_rules
                if str(rule.method) != "regex_substitution"
            }
        )
    )

    if unsupported_methods:
        raise CatalogError(
            details={"unsupported_methods": unsupported_methods},
            message="A profile declares an unsupported code-parent rule method.",
        )


def _resolve_optional_statement_policy(
    *, node: StandardNode, policies_by_key: Mapping[str, StatementTypePolicy]
) -> StatementTypePolicy | None:
    """Resolve one source statement type through profile aliases when available.

    Parameters
    ----------
    node
        Exact source node whose source statement type may identify a policy.
    policies_by_key
        Package-local normalized statement-type policy lookup.

    Returns
    -------
    StatementTypePolicy | None
        Exact profile policy or ``None`` when the node has no resolvable value.
    """

    if node.statement_type is None:
        return None

    return policies_by_key.get(normalize_facet_value(node.statement_type))


def _resolve_statement_policy(
    *, node: StandardNode, policies_by_key: Mapping[str, StatementTypePolicy]
) -> StatementTypePolicy:
    """Resolve one coded node's source statement type through exact profile data.

    Parameters
    ----------
    node
        Exact source node carrying a statement code.
    policies_by_key
        Package-local normalized policy lookup.

    Returns
    -------
    StatementTypePolicy
        Exact configured statement-type policy.

    Raises
    ------
    CatalogError
        If the coded node has no resolvable source statement type.
    """

    if node.statement_type is None:
        raise CatalogError(
            details={"node_id": str(node.node_id)},
            message="An accepted coded node has no source statement type.",
        )

    policy = policies_by_key.get(normalize_facet_value(node.statement_type))

    if policy is None:
        raise CatalogError(
            details={
                "node_id": str(node.node_id),
                "statement_type": node.statement_type,
            },
            message=("An accepted coded node has no resolvable statement-type policy."),
        )

    return policy


def _scopes_are_compatible(
    *, child_posting: CodePosting, parent_posting: CodePosting
) -> bool:
    """Return whether child and derived-parent postings share compatible scope.

    Parameters
    ----------
    child_posting
        Exact child-code posting.
    parent_posting
        Candidate derived-parent code posting.

    Returns
    -------
    bool
        ``True`` when either posting is globally scoped, or both scoped postings share
        at least one exact node for every common scope type and have at least one
        common scope type.
    """

    child_scopes_by_type = _scope_ids_by_statement_type(child_posting.scope_key)
    parent_scopes_by_type = _scope_ids_by_statement_type(parent_posting.scope_key)

    if not child_scopes_by_type or not parent_scopes_by_type:
        return True

    shared_types = set(child_scopes_by_type).intersection(parent_scopes_by_type)

    if not shared_types:
        return False

    for scope_statement_type in shared_types:
        child_scope_ids = child_scopes_by_type[scope_statement_type]
        parent_scope_ids = parent_scopes_by_type[scope_statement_type]

        if child_scope_ids.isdisjoint(parent_scope_ids):
            return False

    return True


def _scope_ids_by_statement_type(
    scope_key: tuple[tuple[str, str], ...],
) -> dict[str, frozenset[str]]:
    """Group exact scope node identifiers by canonical configured statement type.

    Parameters
    ----------
    scope_key
        Canonical statement-type and exact package-local node-ID pairs.

    Returns
    -------
    dict[str, frozenset[str]]
        Scope node identifiers grouped without crossing package boundaries.
    """

    mutable_groups: dict[str, set[str]] = {}

    for statement_type, node_id in scope_key:
        if statement_type not in mutable_groups:
            mutable_groups[statement_type] = set()

        mutable_groups[statement_type].add(node_id)

    return {
        statement_type: frozenset(node_ids)
        for statement_type, node_ids in mutable_groups.items()
    }
