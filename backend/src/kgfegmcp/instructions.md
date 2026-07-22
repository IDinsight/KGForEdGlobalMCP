# Curriculum Knowledge Graph MCP Server

## Comprehensive implementation plan

**Status:** Phase 0 foundational contracts and PR 2 JSONL boundary implemented; PR 3 deterministic manifest construction is next  
**Primary runtime:** Python 3.13 with standalone `fastmcp==3.4.4`  
**Initial client:** Claude Desktop over local STDIO  
**Initial graph type:** Academic Standards  
**Future graph types:** Learning Components, Learning Progressions, curriculum resources, assessments, and reviewed alignments

---

## 1. Purpose of this document

This `instructions.md` file is the definitive starting point for implementing a general, multi-framework Model Context Protocol server over curriculum knowledge graphs.

It is intended to provide enough context for a coding assistant to work productively without requiring the complete upstream extraction pipeline, every runtime configuration, and every graph artifact to be pasted into each new conversation.

The implementation must remain general. Country-, curriculum-, organization-, language-, grade-, subject-, code-, and hierarchy-specific behavior must be supplied through versioned data and configuration rather than embedded in generic Python code.

### How a coding assistant should use this file

Before making changes, the coding assistant should:

1. Read `instructions.md` completely.
2. Identify the current implementation phase and its acceptance criteria.
3. Inspect the existing repository before proposing structural changes.
4. Keep MCP transport code thin and put graph logic in ordinary domain services.
5. Add or update tests with every behavioral change unless the operator explicitly
   defers tests for the current unit; any deferral must remain visible and does not
   waive the production definition of done.
6. Avoid hardcoding facts from the six current curriculum packages.
7. Preserve source graph topology, including valid multi-parent DAGs and explicit unresolved-edge statuses.
8. Distinguish source facts, deterministic derivations, retrieval candidates, LLM inferences, and reviewed mappings.
9. Avoid introducing a server-side LLM. Claude Desktop is the reasoning and generation layer for the initial implementation.
10. Update `instructions.md` or an ADR when a foundational decision changes.

### Implementation discipline

Work in small, reviewable phases. Do not simultaneously rewrite the loader, add a new search engine, add all educational prompts, and create an alignment system. Each phase below has a narrow goal, tests, and exit criteria.

---

## 2. Executive summary

The target system is one catalog-driven FastMCP server that can load, validate, index, and query many versioned curriculum graph packages from different countries, states, organizations, subjects, languages, grade bands, and authorities.

The source graphs remain isolated and immutable. The server federates them through a catalog and common query services rather than merging all source nodes into one undifferentiated graph.

```text
Claude Desktop
      |
      | MCP over local STDIO
      v
Standalone FastMCP server
      |
      +-- deterministic tools
      +-- read-only resources
      +-- reusable prompts
      |
      v
Catalog and domain services
      |
      +-- graph package registry
      +-- DAG-aware graph store
      +-- search indexes
      +-- resource repository
      +-- optional derived alignment repository
      |
      +-- Ghana English
      +-- Ghana Mathematics
      +-- Nigeria Mathematics
      +-- Tamil Nadu Mathematics
      +-- India Science
      +-- Rwanda Mathematics
      +-- future packages
```

The server will initially expose Academic Standards capabilities. It must be designed so Learning Components and Learning Progressions can be added without replacing the Academic Standards domain model or renaming public APIs unnecessarily.

The core architecture is:

1. **Immutable graph packages** for each framework snapshot.
2. **A framework catalog** for discovery, filtering, versioning, and capability reporting.
3. **A DAG-aware graph service** for deterministic navigation.
4. **A layered search service** for identifiers, codes, text, and later optional semantic retrieval.
5. **MCP tools** for deterministic retrieval and computation.
6. **MCP resources** for detailed pipeline artifacts, provenance, validation, and framework-specific interpretation profiles.
7. **MCP prompts** for student, teacher, administrator, comparison, and inferred-progression workflows.
8. **A separate derived overlay** for proposed, reviewed, and accepted cross-framework alignments or progressions.
9. **Claude Desktop as the LLM layer**, with no second model call inside the server.

---

## 3. Goals

### 3.1 Product goals

The server should help (including but not limited to):

- students find grade-relevant standards and receive grounded explanations and practice;
- teachers retrieve standards and draft teacher guides, lesson ideas, student handbooks, questions, and rubrics;
- administrators inspect official frameworks, compare local standards to source frameworks, review evidence-based alignment candidates, and evaluate how one curriculum changed across historical and current snapshots;
- curriculum specialists analyze terminology, hierarchy, granularity, coverage, and progression hypotheses across frameworks;
- developers consume structured, versioned standards data through a stable MCP interface.

### 3.2 Engineering goals

The implementation should:

- use the standalone `fastmcp` project;
- run locally through Claude Desktop using STDIO;
- support all current and future curriculum packages through configuration and manifests;
- preserve source graph semantics and topology exactly;
- support trees and valid multi-parent DAGs;
- support coded, partially coded, and entirely uncoded frameworks;
- preserve unresolved relationship statuses;
- return typed, structured outputs through Pydantic models;
- expose detailed artifacts as resources without forcing them into every tool result;
- make curriculum-specific interpretation available without hardcoding it;
- make provenance and epistemic status visible;
- provide deterministic tests that do not require an LLM;
- allow later migration to HTTP hosting without rewriting domain services.

---

## 4. Non-goals for the first production milestone

The first milestone will not:

- call a server-side LLM;
- use MCP sampling;
- write to or modify source graph packages;
- assert official cross-framework equivalence without an authoritative mapping;
- assert official student mastery from a standard alone;
- claim that normalized grade numbers prove international grade equivalence;
- infer source-authored instructional sequence from `hasChild` hierarchy;
- create Learning Components or Learning Progressions inside the MCP server;
- require Neo4j, an RDF store, a vector database, or a distributed service;
- expose arbitrary local file paths as MCP resources;
- store personally identifiable information;
- automatically persist Claude-generated comparisons as approved graph relationships.

These can be revisited after the deterministic multi-framework core is stable.

---

## 5. Current upstream pipeline context

The upstream Academic Standards extraction pipeline consumes a stitched `DocumentIR` and runs ten stages:

```text
1. Validate DocumentIR and runtime configuration
2. Persist the KG run manifest
3. Plan extraction windows
4. Build source-faithful extraction windows
5. Extract candidate StandardsFrameworkItems
6. Build the global candidate registry
7. Review and merge duplicate candidates
8. Mint deterministic final SFI identities
9. Resolve final hasChild edges
10. Compile, validate, and write final KG artifacts
```

The final export produces two artifact tiers.

### 5.1 Detailed source-faithful artifacts

```text
as_kg_bundle.json
as_standards_framework.json
as_standards_framework_items.jsonl
as_relationships_has_child.jsonl
as_entity_provenance.json
as_unresolved_items.json
as_validation_report.json
```

These artifacts preserve local terminology, local grades, source evidence, merge history, relationship evidence, audit flags, unresolved decisions, deterministic identities, and complete accepted topology.

### 5.2 Slim Learning Commons-shaped delivery artifacts

```text
as_nodes_XXX.jsonl
as_relationships_XXX.jsonl
```

These adapt the accepted graph to a compact delivery envelope. They preserve the nodes and relationships but intentionally omit much of the detailed metadata and provenance.

### 5.3 Governing upstream principle

The MCP implementation must retain the same separation:

```text
Upstream extraction decides curriculum meaning.
Detailed artifacts preserve meaning, evidence, and audit history.
Slim JSONL artifacts provide a portable delivery representation.
The MCP server retrieves and computes over accepted artifacts.
Claude interprets and generates user-facing material from retrieved evidence.
```

Generic MCP code must not repair, reinterpret, or normalize away source-specific decisions already accepted by the upstream pipeline.

---

## 6. Greenfield implementation baseline

This project should be implemented as a fresh, catalog-driven FastMCP application inside
the existing `backend` Python package.

Useful behavior requirements learned from prior experimentation should still be carried
forward:

- operate locally over STDIO without writing logs to stdout;
- expose stable, actionable public errors for expected domain failures;
- support exact identifier lookup, exact and prefix code lookup, and lexical text search;
- support coded, partially coded, and entirely uncoded frameworks;
- never use jurisdiction as a unique framework key;
- preserve every valid parent edge and all root paths in a DAG;
- preserve unresolved relationship statuses;
- return deterministic, typed result shapes;
- load native `as_nodes_XXX.jsonl` and `as_relationships_XXX.jsonl` packages;
- make detailed artifacts available as resources when declared by the package manifest;
- keep subject, grade, language, hierarchy, code, and interpretation rules in validated
  profiles rather than generic Python.

The implementation should start from the contracts and phases in this file, then inspect
the small amount of code already present in `backend/src/kgfegmcp` before deciding what
can be reused.

### Current implementation state

Phase 0 and the PR 2 delivery-boundary unit have been implemented under
`backend/src/kgfegmcp`:

```text
config.py
regexes.py
schemas.py
errors.py
domain/
    __init__.py
    enums.py
    identifiers.py
    models.py
packages/
    __init__.py
    models.py
    wire.py
    decoder.py
profiles/
    __init__.py
    models.py
graph/
    __init__.py
    models.py
```

The implementation currently provides:

- immutable strict Pydantic base schemas;
- framework-independent enumerations and typed domain errors;
- distinct framework, snapshot, graph-package, profile, node, relationship, CASE,
  artifact, version, language, and checksum identifier types;
- deterministic snapshot and graph-package identifier builders;
- shared rights-policy and normalized-subject-vocabulary models;
- immutable graph-package manifest contracts;
- immutable curriculum interpretation profile contracts;
- environment-backed repository path resolution independent of the caller's working
  directory;
- six versioned interpretation profiles derived from the supplied upstream runtime
  configurations;
- strict Learning Commons-shaped node and relationship wire-envelope models;
- preservation of known and unknown raw delivery properties as source strings;
- lazy, one-physical-line-at-a-time JSONL parsing with line and source-order context;
- exact decoding of `isCurrent` from `"true"` and `"false"`;
- decoding of `gradeLevel` from a JSON array encoded inside a string;
- frozen semantic `FrameworkNode`, `StandardNode`, and `GraphRelationship` records;
- preservation of outer identifiers, property identifiers, CASE identifiers,
  relationship outer endpoints, property-declared endpoints, and `resolutionStatus`;
- typed `JSONLParsingError` and `DeliveryPropertyDecodingError` failures whose public
  messages expose the artifact file name and line number without exposing unnecessary
  raw local paths.

The current profiles are stored under:

```text
config/profiles/<profile-id>/<profile-version>/profile.json
```

The six current profile IDs are:

```text
ghana-nacca-primary-english-language-basic-1-3
ghana-nacca-primary-mathematics-basic-4-6
india-tamil-nadu-tnscert-mathematics-classes-1-5
india-cbse-science-learning-framework-classes-9-10
nigeria-nerdc-mathematics-primary-1-3
rwanda-reb-mathematics-lower-primary-1-3
```

PR 2 verification decoded all current delivery fixtures:

```text
2,735 node records
2,964 relationship records
15 unresolved fallback statuses
235 multi-parent India Science targets
```

The node count consists of 2,729 framework-item records plus one framework record for
each of the six packages. Representative negative smoke checks covered malformed JSON,
non-string and null property values, malformed string booleans, malformed embedded
arrays, unknown-property retention, and safe public path masking.

PR 2 also passed Black formatting, isort checking, Ruff, Pylint, full-package mypy,
100% Interrogate docstring coverage, and Python compilation.

No manifest builder, profile repository, checksum service, package aggregate loader,
package validator, graph store, traversal service, catalog, search service, FastMCP
application, resource layer, prompt layer, or CLI has been implemented yet.

Automated tests were intentionally deferred for Phase 0 and PR 2 at the operator's
request. They remain required before the affected behavior is production-ready. Until
the operator requests tests, each implementation unit must run deterministic formatting,
linting, type checking, compilation, and representative positive and negative smoke
checks.

Current top-level and boundary files should be treated as follows:

```text
config.py
    Contains environment-backed application settings and explicit repository path
    resolution. It supports `PATHS_PROJECT_DIR`. Split it only when the settings
    surface becomes too large.

regexes.py
    Contains only framework-independent validation patterns for identifiers, versions,
    checksums, language tags, artifact names, and unsafe control characters.
    Curriculum-specific patterns belong in versioned profiles or package data.

schemas.py
    Contains strict mutable and immutable Pydantic base schemas. Do not allow it to
    become a growing collection of domain models; new models belong in their owning
    subpackages.

errors.py
    Contains the typed domain-error hierarchy and stable error codes. FastMCP-specific
    `ToolError` translation will be implemented later at the MCP boundary.

packages/wire.py
    Defines the strict external delivery envelopes. It preserves source strings and
    unknown properties and must not perform semantic decoding or graph validation.

packages/decoder.py
    Owns JSONL line parsing and delivery-specific string decoding. It must not compare
    identifiers, resolve endpoints, repair records, or enforce graph-wide invariants.

graph/models.py
    Defines artifact-local semantic graph records produced by the decoder. These
    records intentionally do not carry `framework_id`, `snapshot_id`, or
    `graph_package_id`, because those values come from the package manifest rather than
    from each JSONL line.
```

The root `README.md` should remain a concise project overview and onboarding document.
`backend/README.md` should cover backend developer setup. This `instructions.md` file is
the architectural and implementation source of truth for coding-assistant sessions.

---

## 7. Current curriculum packages as validation fixtures

The current six accepted graph artifact sets are examples and regression fixtures, not the universe of supported curricula. PR 3 will package these artifacts and generate their manifests.

| Framework | Items | Relationships | Coded items | Notable topology or status |
|---|---:|---:|---:|---|
| Ghana English, Basic 1-3 | 430 | 430 | 319 | Tree; 2 unresolved-root fallback edges |
| Ghana Mathematics, Basic 4-6 | 302 | 302 | 254 | Tree; 13 unresolved-root fallback edges |
| Nigeria Mathematics, Primary 1-3 | 242 | 242 | 0 | Tree; entirely uncoded |
| Tamil Nadu Mathematics, Classes 1-5 | 255 | 255 | 35 | Tree; partially coded |
| India Science | 874 | 1,109 | 831 | Valid multi-parent DAG; 235 items have two parents |
| Rwanda Mathematics, Primary 1-3 | 626 | 626 | 0 | Tree; entirely uncoded |
| **Total** | **2,729** | **2,964** | **1,439** | Six complete graph packages |

The table counts framework items. The complete wire fixtures also contain one
`StandardsFramework` node per package, for a total of 2,735 node records.

These fixtures prove that the implementation must support:

- more than one subject in the same jurisdiction;
- local subject labels such as `English Language` and normalized search facets such as `English Language Arts`;
- coded, partially coded, and uncoded frameworks;
- source hierarchies with different statement-type vocabularies;
- multi-parent DAGs;
- explicit unresolved fallback relationships;
- local grade labels and explicit normalized-grade mappings;
- heterogeneous licensing and attribution metadata.

No production logic should contain conditionals for Ghana, Nigeria, India, Rwanda, or any current curriculum name.

The current operator-assigned stable framework IDs are:

```text
ghana-nacca-primary-english-language-basic-1-3
ghana-nacca-primary-mathematics-basic-4-6
india-tamil-nadu-tnscert-mathematics-classes-1-5
india-cbse-science-learning-framework-classes-9-10
nigeria-nerdc-mathematics-primary-1-3
rwanda-reb-mathematics-lower-primary-1-3
```

These IDs identify conceptual framework families. They do not include publication
dates, extraction dates, providers, or content hashes.

---

## 8. Core architectural decisions

### Decision 1: use standalone FastMCP

Use:

```python
from fastmcp import FastMCP
```

Do not use `mcp.server.fastmcp.FastMCP` from the official Python SDK in the new implementation.

Reasons:

- concise definitions for tools, resources, and prompts;
- typed input and output schema generation;
- structured tool output support;
- controlled public errors through `ToolError`;
- lifespan hooks for loading the catalog once;
- in-memory client testing;
- middleware and telemetry support;
- provider and mounting options for future composition;
- direct Claude Desktop installation support.

The MCP protocol remains the interoperability contract. Another implementation using `rmcp`, TypeScript, or a low-level SDK can still expose an equivalent MCP interface.

### Decision 2: one catalog-driven server

One server should access all available curriculum packages.

This means one MCP surface and one process, not one server per country or subject.

It does **not** mean flattening all source frameworks into one graph. Each package remains separate and versioned. The catalog determines which packages are available and routes queries to the correct graph or set of graphs.

Benefits:

- cross-framework search and comparison become straightforward;
- Claude Desktop requires one connection;
- tool names remain stable;
- indexes and configuration are centralized;
- new packages can be added without adding new MCP tools;
- framework identity is explicit rather than inferred from jurisdiction.

### Decision 3: immutable source graph packages

A graph package represents one validated snapshot of one framework.

Source packages must be treated as immutable. Reprocessing or correcting a curriculum creates a new snapshot rather than mutating a package silently.

### Decision 4: source graphs and derived overlays remain separate

Do not write LLM-generated cross-country relationships into source `as_nodes_XXX.jsonl` or `as_relationships_XXX.jsonl`.

Use separate derived stores for:

- proposed alignments;
- reviewed alignments;
- accepted alignments;
- inferred progressions;
- reviewed progressions;
- generated instructional artifacts, if persistence is added later.

This keeps source authority and derived interpretation distinguishable.

### Decision 5: the graph layer must be DAG-aware

The graph store must support:

```python
parents[node_id] -> list[Relationship]
children[node_id] -> list[Relationship]
```

It must not store a single `parent[node_id]` value.

Every context API must be capable of returning all direct parents and all bounded paths to the root.

### Decision 6: curriculum-specific interpretation is external configuration

Curriculum-specific facts and heuristics belong in versioned profiles, not generic Python.

Examples:

- subject aliases;
- local grade labels and mappings;
- statement-type semantics;
- expected hierarchy conventions;
- code policies;
- known anomalies;
- source roles that contain official activities or assessment guidance;
- progression heuristics;
- wording and disclosure rules;
- rights and attribution policy.

### Decision 7: the server remains deterministic in the initial design

The server performs:

- loading;
- validation;
- indexing;
- filtering;
- retrieval;
- graph traversal;
- statistics;
- evidence packaging.

Claude Desktop performs:

- explanation;
- comparison narrative;
- lesson and guide drafting;
- student-facing generation;
- inferred progression reasoning;
- draft alignment analysis.

### Decision 8: detailed artifacts are resources

Detailed pipeline artifacts are a strong fit for MCP resources because they are read-only contextual data.

However, a resource is not a substitute for a query tool. Raw artifacts are exposed as resources; selection, traversal, filtering, aggregation, and comparison remain tools.

### Decision 9: use structured output and explicit error types

All public tools should return Pydantic models or `ToolResult` objects with structured content.

Expected domain failures should raise controlled `ToolError` messages. Unexpected exceptions should be logged with details on the server and masked from the client.

### Decision 10: preserve local and normalized values separately

Do not overwrite source values with normalized values.

Examples:

```text
localSubject: English Language
normalizedSubject: English Language Arts

localGrade: PRIMARY THREE
normalizedGrades: ["3"]
```

Normalization supports discovery and comparison. It does not assert exact semantic equivalence.

---

## 9. Epistemic status model

Every important result should identify what kind of claim it contains.

Recommended statuses:

| Status | Meaning |
|---|---|
| `source_asserted` | Directly represented in the accepted source graph or source artifact |
| `source_extracted` | Extracted from an authoritative source document with preserved provenance |
| `deterministic_derived` | Computed mechanically from accepted nodes, relationships, or configuration |
| `retrieval_candidate` | Selected by lexical, code, or semantic retrieval but not asserted as equivalent |
| `llm_inferred` | Generated by Claude from supplied evidence |
| `human_reviewed` | Reviewed by a qualified person but not necessarily formally approved |
| `accepted_derived` | Approved through a documented governance process |
| `unresolved` | Evidence is incomplete or contradictory |

The MCP server should use the first four and `unresolved`. Claude-generated responses should explicitly identify `llm_inferred` claims. A future review system can use `human_reviewed` and `accepted_derived`.

---

## 10. Claims the Academic Standards graph can and cannot support

### 10.1 What it can support directly

A standalone Academic Standards graph can authoritatively retrieve:

- framework metadata;
- standard descriptions;
- source identifiers and codes;
- local and mapped grades;
- source hierarchy and membership;
- direct parents and children;
- bounded ancestors and descendants;
- all available root paths in a DAG;
- source statement types;
- source relationship status;
- source provenance and validation artifacts, when available.

### 10.2 Mastery

The graph defines a learning expectation. It does not contain a particular learner's evidence, rubric results, decision threshold, or mastery policy.

Therefore:

- the server may retrieve the standard against which evidence would be evaluated;
- Claude may draft questions or explain what evidence might be relevant;
- the system must not state that a learner has officially mastered the standard without an assessment and learner-evidence layer.

### 10.3 Official equivalence

Two standards can be retrieved as similar candidates, but official equivalence requires an authoritative crosswalk, association, or reviewed mapping.

A text or embedding match is not official equivalence.

### 10.4 International grade equivalence

A normalized grade is a retrieval and comparison facet. It does not prove that two countries' grades have the same entry age, duration, prior learning, instructional time, content, or performance expectations.

Use language such as `mapped to normalized grade 3 for retrieval` rather than `exactly equivalent to Grade 3 elsewhere`.

### 10.5 Official instructional activities and assessments

The current slim Academic Standards graphs generally model organizers and learning expectations, not complete pedagogy, activities, resources, assessments, or rubrics.

If the upstream detailed artifacts preserve official activity or evaluation material, that material can be exposed through resources with source provenance and rights controls. It should not be represented as an Academic Standard unless the upstream model explicitly accepted it as one.

A future Curriculum or Assessment graph can model these entities directly.

---

## 11. Target repository structure

The implementation should fit the repository's existing `backend` source layout. The
following is the target structure; files and directories can be introduced phase by
phase.

```text
.
├── instructions.md
├── README.md
├── Makefile
├── backend/
│   ├── README.md
│   ├── Makefile
│   ├── pyproject.toml
│   ├── uv.lock
│   ├── fastmcp.json
│   ├── src/
│   │   └── kgfegmcp/
│   │       ├── __init__.py
│   │       ├── app.py
│   │       ├── bootstrap.py
│   │       ├── config.py
│   │       ├── errors.py
│   │       ├── logging_.py
│   │       ├── regexes.py
│   │       ├── schemas.py
│   │       │
│   │       ├── domain/
│   │       │   ├── __init__.py
│   │       │   ├── models.py
│   │       │   ├── enums.py
│   │       │   ├── identifiers.py
│   │       │   ├── results.py
│   │       │   └── protocols.py
│   │       │
│   │       ├── packages/
│   │       │   ├── __init__.py
│   │       │   ├── models.py
│   │       │   ├── wire.py
│   │       │   ├── decoder.py
│   │       │   ├── builder.py
│   │       │   ├── checksums.py
│   │       │   ├── loader.py
│   │       │   └── validator.py
│   │       │
│   │       ├── profiles/
│   │       │   ├── __init__.py
│   │       │   ├── models.py
│   │       │   ├── loader.py
│   │       │   └── validator.py
│   │       │
│   │       ├── catalog/
│   │       │   ├── __init__.py
│   │       │   ├── models.py
│   │       │   ├── repository.py
│   │       │   ├── service.py
│   │       │   └── filters.py
│   │       │
│   │       ├── graph/
│   │       │   ├── __init__.py
│   │       │   ├── models.py
│   │       │   ├── loader.py
│   │       │   ├── store.py
│   │       │   ├── traversal.py
│   │       │   └── validation.py
│   │       │
│   │       ├── search/
│   │       │   ├── __init__.py
│   │       │   ├── models.py
│   │       │   ├── normalizers.py
│   │       │   ├── lexical.py
│   │       │   ├── code.py
│   │       │   ├── service.py
│   │       │   └── semantic.py       # optional, later
│   │       │
│   │       ├── resources/
│   │       │   ├── __init__.py
│   │       │   ├── repository.py
│   │       │   ├── uri.py
│   │       │   └── policy.py
│   │       │
│   │       ├── alignments/
│   │       │   ├── __init__.py
│   │       │   ├── models.py
│   │       │   ├── repository.py
│   │       │   └── service.py
│   │       │
│   │       ├── services/
│   │       │   ├── __init__.py
│   │       │   ├── frameworks.py
│   │       │   ├── standards.py
│   │       │   ├── statistics.py
│   │       │   ├── comparison.py
│   │       │   └── capabilities.py
│   │       │
│   │       ├── mcp/
│   │       │   ├── __init__.py
│   │       │   ├── register.py
│   │       │   ├── tools/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── frameworks.py
│   │       │   │   ├── standards.py
│   │       │   │   ├── context.py
│   │       │   │   ├── statistics.py
│   │       │   │   └── comparison.py
│   │       │   ├── resources/
│   │       │   │   ├── __init__.py
│   │       │   │   ├── catalog.py
│   │       │   │   ├── framework.py
│   │       │   │   ├── artifacts.py
│   │       │   │   └── provenance.py
│   │       │   └── prompts/
│   │       │       ├── __init__.py
│   │       │       ├── student.py
│   │       │       ├── teacher.py
│   │       │       ├── administrator.py
│   │       │       ├── comparison.py
│   │       │       └── progression.py
│   │       │
│   │       └── cli/
│   │           ├── __init__.py
│   │           ├── build_manifests.py
│   │           ├── validate_packages.py
│   │           ├── build_catalog.py
│   │           └── inspect_package.py
│   │
│   └── tests/
│       ├── __init__.py
│       ├── conftest.py
│       ├── constants.py
│       ├── types_.py
│       ├── test.env
│       ├── fixtures/
│       │   └── ...
│       └── kgfegmcp/
│           ├── unit/
│           ├── integration/
│           ├── contract/
│           └── smoke/
│
├── config/
│   ├── server.json
│   ├── catalog.json
│   └── profiles/
│       └── <profile-id>/
│           └── <profile-version>/
│               ├── profile.json
│               ├── interpretation.md
│               └── prompt_fragments/
│
├── data/
│   ├── graph_packages/
│   │   └── <framework-id>/
│   │       └── <snapshot-id>/
│   │           ├── package_manifest.json
│   │           ├── delivery/
│   │           │   ├── as_nodes_XXX.jsonl
│   │           │   └── as_relationships_XXX.jsonl
│   │           └── detailed/
│   │               ├── as_kg_bundle.json
│   │               ├── as_standards_framework.json
│   │               ├── as_standards_framework_items.jsonl
│   │               ├── as_relationships_has_child.jsonl
│   │               ├── as_entity_provenance.json
│   │               ├── as_unresolved_items.json
│   │               └── as_validation_report.json
│   └── derived/
│       ├── alignments/
│       └── progressions/
│
├── docs/
│   └── adr/
├── scripts/
│   └── tools/
├── caches/
├── logs/
├── results/
└── secrets/
```

### Repository path conventions

- Python source lives under `backend/src/kgfegmcp`.
- Test modules live under `backend/tests/kgfegmcp`.
- Shared test fixtures may remain under `backend/tests/fixtures`.
- Python, `uv`, pytest, and FastMCP commands should run from `backend`, unless a root
  Makefile target delegates there explicitly.
- Runtime configuration and graph-package data remain repository-level concerns under
  `config/` and `data/`.
- Application settings must resolve repository-level paths explicitly; they must not
  rely on the caller's current working directory.
- The root `instructions.md` is the implementation source of truth.
- The root `README.md` is for project-level onboarding; `backend/README.md` is for
  backend setup and developer commands.
- Generated `__pycache__` directories and `.pyc` files are not part of the intended
  structure and should remain ignored by version control.
- `caches/`, `logs/`, and `results/` are runtime output locations, not importable source
  packages.
- `secrets/` must never be exposed through an MCP resource, included in package
  manifests, or committed.

### Existing-file transition

Do not rename or split `config.py`, `regexes.py`, or `schemas.py` merely to match the
target tree. Introduce domain subpackages when their responsibilities are implemented,
then move or re-export definitions in small tested steps.

### Explicit registration versus FileSystemProvider

Start with explicit registration in `mcp/register.py` so the public MCP surface is
obvious and startup failures are strict.

FastMCP's provider and filesystem discovery features can be introduced later if the
component count becomes difficult to manage. Automatic discovery is convenient, but
explicit assembly is easier to audit during the first implementation.

---

## 12. Identity and versioning model

The implementation must distinguish several identifiers.

### `framework_id`

Stable operator-assigned identity for the conceptual framework across snapshots.

Use lowercase kebab case with enough authority, family, subject, and document-scope
information to avoid collisions:

```text
<jurisdiction>-<issuing-authority>-<framework-family>-<subject>-<document-scope>
```

Do not include publication year, extraction date, provider, adoption status, or content
hash. Do not derive the final identifier automatically from a filename or display title.

Example:

```text
ghana-nacca-primary-english-language-basic-1-3
```

### `snapshot_id`

Immutable identity for one accepted exported version of a framework.

Use:

```text
<framework-id>@<version-token>+<12-character-snapshot-hash>
```

The version token should use the first authoritative value available:

1. official release or edition;
2. official publication date;
3. official publication year;
4. descriptive release label such as `2025-proposed-draft`;
5. `undated` when no authoritative version is available.

Do not automatically treat the extraction runtime year as the official source version.

The snapshot hash is the first 12 lowercase hexadecimal characters of a SHA-256 digest
computed from a canonical ordered list of the checksums of all declared immutable source
snapshot artifacts. Do not include the manifest itself, profile files, caches, search
indexes, logs, or generated results in this digest.

Example:

```text
ghana-nacca-primary-english-language-basic-1-3@2019+4f82a91d3c7e
```

A semantic correction to accepted nodes, relationships, provenance, unresolved
decisions, or validation artifacts creates a new `snapshot_id`.

A profile-only change does not change `snapshot_id`; it creates a new profile version.

### `graph_package_id`

Globally unique identity for one packaged graph representation.

During the initial single-graph implementation:

```text
graph_package_id == snapshot_id
```

When several graph types or package revisions can belong to one snapshot, use:

```text
<snapshot-id>--<graph-type>--p<package-revision>
```

Examples:

```text
<snapshot-id>--academic-standards--p1
<snapshot-id>--learning-components--p1
<snapshot-id>--learning-progressions--p1
```

A packaging-only change, such as a delivery schema or artifact-layout revision, may
increment the package revision without changing the source snapshot. A semantic graph
change must create a new snapshot instead.

### Multiple snapshots for one framework family

One `framework_id` may have several immutable snapshots in the catalog at the same
time.

Example:

```text
framework_id:
    ghana-nacca-primary-mathematics

snapshot_id:
    ghana-nacca-primary-mathematics@2019+abc123

snapshot_id:
    ghana-nacca-primary-mathematics@2026+def456
```

This supports historical retrieval and reproducible curriculum-revision analysis. Adding
the 2026 snapshot must not overwrite or mutate the 2019 snapshot.

Recommended catalog behavior:

- list every available snapshot for the framework;
- expose source version, publication date, adoption status, and `is_current`;
- permit at most one default current snapshot unless ambiguity is reported explicitly;
- allow users and tools to select any snapshot by exact `snapshot_id`;
- record optional snapshot-family relations such as `revises`, `supersedes`,
  `replaces`, or `derived_from` when supplied by an operator or authoritative source;
- never infer a revision-family relationship solely from matching jurisdiction and
  subject.

A comparison between snapshots must identify both exact snapshot IDs. This keeps the
result reproducible even if a later re-extraction or correction creates another snapshot.

### `node_id`

The outer graph node `identifier`.

### `case_identifier_uuid` and `case_identifier_uri`

Source or CASE-style identifiers carried by the node. The server must not assume these equal `node_id`.

### `relationship_id`

The outer relationship `identifier`.

### `profile_id` and `profile_version`

Identity for the curriculum interpretation profile used by tools and prompts.

All tool responses should include `framework_id`, `snapshot_id`, and `node_id` so results remain reproducible.

---

## 13. Graph package manifest

Every package must have a manifest validated by Pydantic. For the current six artifact
sets, `package_manifest.json` is generated inside the KGForEdGlobalMCP repository rather than
being expected as an upstream extraction output.

The manifest generator uses the selected versioned profile and the accepted graph
artifacts as its primary inputs.

### Manifest-generation authority

Manifest fields come from four explicit sources:

```text
selected config/profiles profile
    stable framework identity, normalized subjects and grades, hierarchy and code
    policy, language policy, source-role capabilities, and operator rights policy

decoded StandardsFramework root node
    source-facing name, jurisdiction, authority/author, provider, local subject,
    adoption status, current status, source license, and attribution

accepted as_* graph artifacts
    artifact names, checksums, counts, code coverage, unresolved-status evidence,
    multi-parent evidence, and optional detailed-artifact availability

explicit package-build inputs
    authoritative version token, jurisdiction type when not already modeled, optional
    source publication date, package revision, and approved snapshot-family relations
```

The generator must compare overlapping profile and framework-node values and fail on a
material deterministic mismatch. It must not silently select whichever source is more
convenient.

The generator must not guess an official version from a filename, local filesystem path,
or extraction runtime year. The operator supplies the accepted version token explicitly.

### Required manifest responsibilities

The manifest should describe:

- package and framework identity;
- graph type and included graph types;
- source and delivery schema versions;
- framework metadata and normalized facets;
- artifact paths;
- checksums;
- counts;
- validation status;
- topology capabilities;
- statement-code availability;
- detailed-artifact availability;
- rights and exposure policy;
- associated curriculum profile.

### Illustrative manifest

```json
{
  "manifestVersion": "1.0",
  "graphPackageId": "ghana-nacca-primary-english-language-basic-1-3@2019+4f82a91d3c7e",
  "frameworkId": "ghana-nacca-primary-english-language-basic-1-3",
  "snapshotId": "ghana-nacca-primary-english-language-basic-1-3@2019+4f82a91d3c7e",
  "graphType": "academic_standards",
  "includedGraphTypes": ["academic_standards"],
  "sourceSchemaVersion": "1.0",
  "deliverySchemaVersion": "1.0",
  "framework": {
    "name": "English Language Curriculum for Primary Schools (Basic 1 - 3)",
    "jurisdiction": "Ghana",
    "jurisdictionType": "country",
    "issuingAuthority": "National Council for Curriculum and Assessment",
    "provider": "IDinsight",
    "localSubject": "English Language",
    "normalizedSubjects": ["English Language Arts"],
    "subjectMappingStatus": "mapped",
    "languages": ["en"],
    "localGradesOrStages": ["BASIC 1", "BASIC 2", "BASIC 3"],
    "normalizedGrades": ["1", "2", "3"],
    "adoptionStatus": "Adopted",
    "isCurrent": true,
    "sourceVersion": "2019"
  },
  "artifacts": {
    "nodes": "delivery/as_nodes_ghana_english.jsonl",
    "relationships": "delivery/as_relationships_ghana_english.jsonl",
    "validationReport": "detailed/as_validation_report.json",
    "entityProvenance": "detailed/as_entity_provenance.json",
    "unresolvedItems": "detailed/as_unresolved_items.json"
  },
  "checksums": {
    "delivery/as_nodes_ghana_english.jsonl": "sha256:<64-lowercase-hex-characters>",
    "delivery/as_relationships_ghana_english.jsonl": "sha256:<64-lowercase-hex-characters>",
    "detailed/as_validation_report.json": "sha256:<64-lowercase-hex-characters>",
    "detailed/as_entity_provenance.json": "sha256:<64-lowercase-hex-characters>",
    "detailed/as_unresolved_items.json": "sha256:<64-lowercase-hex-characters>"
  },
  "counts": {
    "frameworkNodes": 1,
    "itemNodes": 430,
    "relationships": 430
  },
  "capabilities": {
    "codeSearch": "partial",
    "textSearch": true,
    "multiParent": false,
    "hasUnresolvedRelationships": true,
    "hasDetailedProvenance": true,
    "hasOfficialActivities": false,
    "hasOfficialAssessmentGuidance": false
  },
  "rights": {
    "sourceLicense": "Unknown",
    "attributionStatement": "...",
    "reviewStatus": "provisional_operator_approved",
    "allowFullText": true,
    "allowStandardResources": true,
    "allowBulkResource": false,
    "allowGeneratedDerivatives": "allowed"
  },
  "profile": {
    "profileId": "ghana-nacca-primary-english-language-basic-1-3",
    "profileVersion": "1.0",
    "sha256": "sha256:<64-lowercase-hex-characters>"
  },
  "validation": {
    "status": "pending",
    "validatedAt": null
  },
  "createdAt": "2026-07-20T00:00:00Z"
}
```

Profiles are resolved through the configured central profile root by profile ID and
version. Manifests must not contain arbitrary profile filesystem paths.

The exact schema can be simplified, but these concepts should not be collapsed.

---

## 14. Curriculum interpretation profiles

A profile is versioned configuration used by the MCP layer. It is distinct from the upstream extraction runtime config, though fields can be derived or copied from it.

### Why a separate profile exists

The upstream runtime config is optimized for extraction, deduplication, and relationship resolution. The MCP server needs a smaller, stable set of interpretation and presentation rules.

Do not make the MCP server import the entire extraction application just to interpret a package.

### Profile contents

Recommended machine-readable fields:

```text
profile_id
profile_version
framework_ids
local_subject
normalized_subjects
subject_aliases
local_grade_mappings
education_stage_mappings
statement_type_definitions
normalized_statement_type_mappings
hierarchy_expectations
code_policy
known_source_anomalies
comparison_dimensions
progression_heuristics
source_role_capabilities
rights_policy
required_disclosures
language_policy
```

Recommended human-readable companion:

```text
interpretation.md
```

Profiles are stored and resolved centrally:

```text
config/profiles/<profile-id>/<profile-version>/profile.json
```

The manifest stores only `profile_id`, `profile_version`, and the expected profile
checksum. The profile repository resolves the path beneath the configured profile root;
arbitrary manifest-provided paths are not allowed.

The initial normalized-subject vocabulary is versioned configuration with these values:

```text
English Language Arts
Mathematics
Science
Social Studies
Other
```

A subject mapping has one of three states:

```text
mapped
other
unreviewed
```

`Other` means the mapping was reviewed and no better vocabulary match exists.
`unreviewed` means no mapping decision has been made yet.

The current profile models include local grade mappings, education-stage mappings,
statement-type definitions, normalized statement-type mappings, identity scopes,
parent-cardinality rules, tree or DAG topology, code interpretation and search policy,
language policy, known source anomalies, source-role capabilities, rights policy, and
required disclosures.

This can explain:

- what local statement types mean;
- how grades are represented;
- what codes mean and do not mean;
- which source columns or sections contain standards, activities, or assessment guidance;
- known anomalies;
- curriculum-specific progression heuristics;
- warnings Claude should include.

### Critical distinction

Correctness-critical rules must be available to server logic or returned in tool evidence. They must not exist only in an MCP prompt, because prompts are user-controlled and may not be invoked.

### Profile versioning

Every result influenced by a profile should include its profile ID and version. Changing a profile should invalidate affected caches and comparison artifacts.

The exported `normalizedStatementType` is treated as an accepted deterministic upstream
derivation, not source-authored terminology. Manifest construction records the selected
profile and may perform deterministic compatibility checks needed to describe the package.
Full package validation in PR 4 must compare exported values with the selected profile's
expected mapping and preserve mismatches as failures rather than silently rewriting source
graph records.

Code policy means deterministic code interpretation and search behavior, including code
availability, normalization, case behavior, delimiter-aware prefix matching, scope,
code-parent derivation, and whether codes are reliable unique identifiers. It does not
assert educational equivalence.

---

## 15. Package ingestion and validation

### 15.1 Startup behavior

Use FastMCP lifespan setup to:

1. load server settings;
2. load and validate the catalog;
3. load package manifests;
4. validate checksums and artifact presence;
5. parse delivery JSONL;
6. build graph indexes;
7. build search indexes;
8. load curriculum profiles;
9. construct immutable application state;
10. expose the state through the FastMCP lifespan context.

### 15.2 Invalid-package policy

Support an explicit setting:

```text
invalid_package_policy = fail | quarantine
```

Recommended defaults:

- development and CI: `fail`;
- production: `fail` unless there is an operational reason to quarantine;
- `quarantine` must expose the package and validation error in catalog diagnostics but must not make its standards queryable.

Never silently skip a malformed package.

### 15.3 Required validation checks

At minimum:

- manifest schema is valid;
- all declared files exist;
- checksums match;
- JSONL lines parse;
- exactly one `StandardsFramework` node exists;
- item labels are supported;
- outer identifiers equal property identifiers when required by the delivery format;
- node identifiers are unique;
- relationship identifiers are unique;
- relationship endpoint pairs are unique unless explicitly allowed;
- every endpoint resolves;
- declared endpoint labels agree with resolved nodes;
- relationship property keys agree with outer endpoints;
- self-loops are rejected unless a future relation explicitly permits them;
- directed cycles in `hasChild` are rejected;
- every item is reachable from the framework root, except when a graph type explicitly permits detached components;
- multiple parents are preserved;
- `resolutionStatus` is parsed and preserved;
- string-encoded booleans and arrays are decoded through one boundary adapter;
- local and normalized facets in the manifest are consistent with package metadata;
- detailed validation report passed when one is declared;
- counts match manifest values;
- profile references and profile checksums are valid;
- rights policy is present.

### 15.4 Preserve raw values

The implemented delivery boundary maintains both:

```text
raw property dictionary
decoded typed view
```

Every wire property must be a string. Explicit JSON `null`, numeric, boolean, object,
and array property values are rejected rather than coerced. Optional properties are
represented by omission. Unknown source properties are accepted and retained in
`raw_properties`; they are not discarded or promoted into generic Python conditionals.

### 15.5 Implemented Learning Commons-shaped boundary adapter

The delivery JSONL wire conventions are implemented in:

```text
backend/src/kgfegmcp/packages/wire.py
backend/src/kgfegmcp/packages/decoder.py
backend/src/kgfegmcp/graph/models.py
```

Node records use an outer envelope similar to:

```json
{
  "type": "node",
  "identifier": "...",
  "labels": ["StandardsFrameworkItem"],
  "properties": {
    "identifier": "...",
    "caseIdentifierUUID": "...",
    "isCurrent": "true",
    "gradeLevel": "[\"2\"]"
  }
}
```

Relationship records use:

```json
{
  "type": "relationship",
  "identifier": "...",
  "label": "hasChild",
  "properties": {
    "identifier": "...",
    "relationshipType": "hasChild",
    "sourceEntityKey": "caseIdentifierUUID",
    "sourceEntityValue": "...",
    "targetEntityKey": "caseIdentifierUUID",
    "targetEntityValue": "...",
    "resolutionStatus": "unresolvedRootFallback"
  },
  "source_identifier": "...",
  "source_labels": ["StandardsFrameworkItem"],
  "target_identifier": "...",
  "target_labels": ["StandardsFrameworkItem"]
}
```

Implemented boundary behavior:

- `NodeWireEnvelope` and `RelationshipWireEnvelope` strictly validate the outer record
  type, identifiers, labels, endpoints, and property object;
- `NodeWireProperties` and `RelationshipWireProperties` expose known properties while
  accepting unknown property names;
- all property keys and values must remain strings;
- wire records are read lazily, one physical line at a time;
- blank lines are invalid JSONL records and are not silently skipped;
- each located record retains the one-based physical line number, internal source path,
  and `source_export_order`;
- `source_export_order` is the one-based physical JSONL line number and is not an
  instructional sequence;
- `isCurrent` decodes only from the exact strings `"true"` and `"false"`;
- `gradeLevel` decodes only from a valid JSON array string whose elements are all
  strings, and the typed value preserves source order as a tuple;
- omitted optional properties remain `None` without invented defaults;
- all known and unknown source strings are copied into `raw_properties` using their
  original wire names;
- outer `identifier`, property `identifier`, `caseIdentifierUUID`, and
  `caseIdentifierURI` remain separate;
- relationship outer source and target identifiers remain separate from
  `sourceEntity`, `sourceEntityKey`, `sourceEntityValue`, `targetEntity`,
  `targetEntityKey`, and `targetEntityValue`;
- `resolutionStatus`, including unresolved fallback values, survives decoding;
- node decoding distinguishes framework records from framework-item records through
  the delivery labels and requires exactly one supported node kind;
- relationship decoding does not resolve or compare endpoints;
- source records are not mutated, repaired, normalized, deduplicated, or reordered.

`JSONLParsingError` covers unreadable artifacts, invalid UTF-8, invalid JSON, and invalid
wire envelopes. `DeliveryPropertyDecodingError` covers malformed encoded properties and
typed semantic-record conversion failures. Public messages include the artifact file
name and line number when available; full paths and structured validation details remain
internal.

Only this boundary layer may know the slim wire-format encodings. Package validation,
graph-wide invariants, endpoint resolution, topology checks, indexing, traversal, and
search remain separate responsibilities.

---

## 16. Domain and semantic graph records

The domain and graph-record layers must not depend on FastMCP.

The foundational domain implementation contains:

```text
domain/enums.py
    Framework-independent fixed vocabularies.

domain/identifiers.py
    Validated operator-controlled and opaque source-controlled identifiers plus
    deterministic snapshot and graph-package ID builders.

domain/models.py
    Shared frozen `RightsPolicy` and `SubjectVocabulary` models.
```

`RightsPolicy` deliberately preserves source license and attribution metadata separately
from operator-controlled exposure decisions. `SubjectVocabulary` keeps normalized
subject values versioned and configurable rather than hardcoded into search logic.

The implemented semantic graph-record layer contains:

```text
graph/__init__.py
    Exposes the decoded semantic record types.

graph/models.py
    Defines `GraphNode`, `FrameworkNode`, `StandardNode`, and
    `GraphRelationship`.
```

The `graph` package is currently a semantic-record package, not a graph store. It is the
boundary between delivery-shaped records and future validation, storage, traversal, and
search services.

### Implemented node records

`GraphNode` contains the fields shared by decoded nodes:

```text
node_id
property_identifier
case_identifier_uuid
case_identifier_uri
labels
academic_subject
adoption_status
attribution_statement
author
in_language
is_current
jurisdiction
license
provider
raw_properties
source_export_order
```

`FrameworkNode` adds:

```text
name
```

`StandardNode` adds:

```text
description
grade_level
statement_code
statement_type
normalized_statement_type
```

The decoded `grade_level` is a tuple of source strings. It is not yet a profile-derived
normalized-grade view. The exported `normalized_statement_type` is preserved as the
accepted upstream deterministic value and uses the existing typed enum.

### Implemented relationship records

`GraphRelationship` contains:

```text
relationship_id
property_identifier
label
relationship_type
source_node_id
source_labels
source_entity
source_entity_key
source_entity_value
target_node_id
target_labels
target_entity
target_entity_key
target_entity_value
resolution_status
description
attribution_statement
author
license
provider
raw_properties
source_export_order
```

These fields deliberately preserve both outer endpoints and property-declared endpoint
information for later comparison and resolution.

### Package context boundary

The semantic graph records are artifact-local. They do not duplicate
`framework_id`, `snapshot_id`, or `graph_package_id`, because those values are package
context supplied by the manifest and package loader. PR 4 should associate decoded
records with an immutable loaded-package aggregate rather than mutating each source
record or inventing package identifiers from JSONL content.

### Current non-responsibilities

The graph-record models do not:

- compare outer and property identifiers;
- resolve relationship endpoints;
- enforce identifier uniqueness;
- detect duplicate endpoint pairs;
- detect self-loops or cycles;
- calculate reachability;
- choose a parent;
- assume a tree;
- validate profile semantics;
- perform traversal, indexing, or search;
- repair or rewrite source records.

Those responsibilities belong to the package validator and later DAG-aware graph
services.

### Service protocols

Define interfaces before concrete implementations:

```python
class CatalogRepository(Protocol):
    def list_frameworks(self, filters: FrameworkFilters) -> Page[FrameworkSnapshot]: ...
    def get_framework(self, framework_id: str, snapshot_id: str | None = None) -> FrameworkSnapshot: ...


class GraphRepository(Protocol):
    def get_node(self, snapshot_id: str, node_id: str) -> StandardNode: ...
    def parents(self, snapshot_id: str, node_id: str, relation_type: str = "hasChild") -> list[GraphRelationship]: ...
    def children(self, snapshot_id: str, node_id: str, relation_type: str = "hasChild") -> list[GraphRelationship]: ...


class SearchBackend(Protocol):
    def search(self, query: SearchQuery) -> Page[SearchHit]: ...


class ResourceRepository(Protocol):
    def read(self, resource_uri: str) -> ResourcePayload: ...
```

This enables future replacement of the in-memory implementation without changing tools.

---

## 17. Graph store and traversal

### 17.1 Required indexes

For each snapshot:

```text
nodes_by_id
nodes_by_case_identifier_uuid
nodes_by_case_identifier_uri
relationships_by_id
outgoing_by_type_and_node
incoming_by_type_and_node
framework_root_id
items_in_deterministic_source_order
```

### 17.2 Traversal rules

Traversal must:

- accept a maximum depth;
- enforce a maximum returned-node count;
- use cycle guards even though startup validation checks cycles;
- return all direct parents;
- optionally return all root paths;
- mark unresolved fallback edges;
- distinguish relationship type;
- never treat sibling file order as instructional order;
- preserve deterministic output ordering.

### 17.3 Ordering

If JSONL order is retained for stable display, label it as:

```text
source_export_order
```

Do not call it sequence, progression, or instructional order unless an explicit sequence property exists.

### 17.4 Multi-parent paths

For a DAG node, `get_standard_context` should return:

```json
{
  "directParents": [...],
  "rootPaths": [
    ["framework", "parent-a", "node"],
    ["framework", "parent-b", "node"]
  ]
}
```

The service must not select one preferred path unless a source-authored preference exists.

---

## 18. Search design

### 18.1 Explicit search modes

Use an explicit mode enum. Do not use implicit precedence.

```text
identifier
case_identifier_uuid
code_exact
code_prefix
text
semantic        # optional later
```

### 18.2 Text search

The first implementation can use a deterministic lexical index. Recommended progression:

1. normalized token index for a minimal implementation;
2. SQLite FTS5/BM25 for ranking and phrase support;
3. optional pluggable semantic retrieval later.

The service should expose:

```text
query
operator = any | all
phrase matching option
framework filters
grade filters
subject filters
statement type filters
include groupings
pagination cursor
limit
```

### 18.3 Code search

Code search must support:

- exact code;
- prefix code with delimiter-aware matching;
- case normalization where profile policy allows it;
- frameworks with no codes;
- frameworks with partial code coverage.

Do not fail an entire multi-framework query because one selected framework is uncoded. Return per-framework capability warnings.

### 18.4 Subject normalization

The source `academicSubject` remains unchanged. Cross-framework search uses profile-supplied normalized subjects and aliases.

No global hardcoded tuple of allowed subjects should exist in generic code.

### 18.5 Grade filtering

Support both:

```text
local_grade_labels
normalized_grades
```

A normalized-grade filter is a retrieval filter, not a claim of international equivalence.

### 18.6 Search result evidence

Each hit should include:

```text
retrieval_method
score
matched_terms
matched_fields
framework_id
snapshot_id
profile_version
warnings
```

### 18.7 Pagination

All list and search tools should use cursor-based pagination from the beginning.

The cursor should encode stable ordering state and be validated. It must not expose arbitrary filesystem or SQL information.

---

## 19. MCP server construction

### 19.1 Application state

Use a single immutable application state built in a lifespan:

```python
class AppState(BaseModel):
    catalog_service: Any
    standards_service: Any
    statistics_service: Any
    comparison_service: Any
    resource_repository: Any
    alignment_repository: Any | None
```

The exact typing can use dataclasses or protocols rather than `Any` in production.

### 19.2 Illustrative FastMCP bootstrap

We are using FastMCP version 3.4.4.

```python
from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

from kgfegmcp.bootstrap import build_app_state


@lifespan
async def app_lifespan(server):
    state = build_app_state()
    
    try:
        yield {"state": state}
    finally:
        state.close()


mcp = FastMCP(
    name="Knowledge Graph for All",
    lifespan=app_lifespan,
    mask_error_details=True,
    on_duplicate_tools="error",
    on_duplicate_resources="error",
    on_duplicate_prompts="error",
)
```

### 19.3 Logging and STDIO

When using STDIO:

- stdout is reserved for MCP protocol messages;
- application logs must go to stderr or a file;
- never use uncontrolled `print()` calls in package loaders or tools;
- startup errors should be logged clearly and cause a nonzero exit.

### 19.4 MCP annotations

All initial tools are read-only and should declare appropriate annotations, such as:

```text
readOnlyHint = true
destructiveHint = false
openWorldHint = false
idempotentHint = true
```

Treat annotations as descriptive hints, not security controls.

---

## 20. Error handling

### 20.1 Domain error taxonomy

The typed exception hierarchy currently includes:

```text
KGFEGMCPError
JSONLParsingError
DeliveryPropertyDecodingError
ManifestBuildError
PackageValidationError
ProfileValidationError
CatalogError
ConfigurationError
FrameworkNotFoundError
AmbiguousFrameworkError
StandardNotFoundError
UnsupportedSearchModeError
CapabilityUnavailableError
InvalidCursorError
ResourceNotFoundError
ResourceAccessDeniedError
AlignmentNotFoundError
```

`JSONLParsingError` and `DeliveryPropertyDecodingError` are implemented and used by the
PR 2 boundary. PR 4 should use `PackageValidationError` and `ProfileValidationError` for
package- and profile-level failures rather than translating every validation problem
into a wire parsing error.

### 20.2 Public versus internal errors

Expected user-correctable errors should become `ToolError` with stable, actionable text.

Unexpected errors should:

- be logged with request ID and stack trace;
- return a generic masked message;
- never expose local paths, raw tracebacks, environment variables, or secrets.

### 20.3 Protocol versus tool errors

- unknown tool names and malformed MCP requests are protocol errors;
- invalid domain values, missing framework selection, unsupported code search, and ambiguous matches are tool execution errors.

---

## 21. Initial MCP tools

The initial public surface should remain compact and composable.

### 21.1 `list_frameworks`

Purpose: discover available framework snapshots and capabilities.

Inputs:

```text
query
jurisdictions
jurisdiction_types
issuing_authorities
subjects
languages
local_grades
normalized_grades
graph_types
is_current
validation_status
cursor
limit
```

Output:

```text
framework summaries
capabilities
rights status
profile version
next cursor
```

### 21.2 `get_framework`

Purpose: retrieve complete metadata and capabilities for one framework snapshot.

Inputs:

```text
framework_id
snapshot_id optional; default to the unique current snapshot
```

If several current snapshots exist, return an ambiguity error rather than choosing silently.

### 21.3 `search_standards`

Purpose: canonical standards search across one or more frameworks.

Inputs:

```text
mode
query
framework_ids
snapshot_ids
jurisdictions
subjects
languages
local_grade_labels
normalized_grades
statement_types
normalized_statement_types
operator
include_groupings
cursor
limit
```

Output:

```text
search hits
match evidence
framework-specific warnings
pagination
```

### 21.4 `get_standard`

Purpose: retrieve exactly one standard or grouping by stable identity.

Inputs:

```text
framework_id or snapshot_id
node_id, case_identifier_uuid, or case_identifier_uri
```

Output includes resource links for provenance and source evidence when available.

### 21.5 `get_standard_context`

Purpose: deterministic graph navigation.

Inputs:

```text
snapshot_id
node_id
ancestor_depth
child_depth
include_all_root_paths
include_direct_children
include_descendants
relationship_types
include_unresolved
max_nodes
```

Output:

```text
node
direct parents
direct children
bounded ancestors
bounded descendants
all requested root paths
relationship status warnings
```

### 21.6 `get_framework_statistics`

Purpose: summarize framework contents.

Return counts by:

```text
statement type
normalized statement type
local grade
normalized grade
code presence
relationship type
hierarchy depth
multi-parent count
unresolved relationship count
```

### 21.7 `get_capabilities`

Purpose: report server-level and framework-level available graph types and features.

This helps Claude avoid calling progression or component tools before those graph types exist.

### 21.8 `compare_framework_evidence` - later deterministic phase

Purpose: retrieve evidence for a cross-framework comparison without generating the prose comparison.

Inputs:

```text
topic or query
framework_ids
local or normalized grade filters
search mode
maximum matches per framework
include context paths
```

Output:

```text
selected source standards per framework
retrieval evidence
hierarchy context
local and normalized grade metadata
warnings against unsupported equivalence claims
```

Claude then generates the comparison.

### 21.9 `diff_framework_snapshots`

Purpose: compute deterministic differences between two immutable snapshots, normally
belonging to the same `framework_id`.

Inputs:

```text
source_snapshot_id
target_snapshot_id
grade filters optional
statement type filters optional
include_metadata_changes
include_topology_changes
cursor
limit
```

Output categories should include:

```text
unchanged exact records
added records
removed records
changed fields
statement-code changes
grade-placement changes
parent or hierarchy changes
framework-metadata changes
unmatched records
```

This tool must report only mechanically established differences. It must not claim that
two differently identified records are semantically equivalent unless an authoritative
mapping already exists.

### 21.10 `find_snapshot_alignment_candidates`

Purpose: suggest likely correspondences between records in two snapshots when stable
identifiers or codes do not provide an exact match.

Candidate evidence may include:

```text
shared statement code
normalized text similarity
same local or normalized grade
same statement type
similar ancestor path
shared topic terms
optional semantic retrieval score
```

Every result must be labeled `retrieval_candidate`. The tool should support one-to-one,
one-to-many, and many-to-one candidates and should return unmatched records rather than
forcing a correspondence.

Claude can use these candidates, together with deterministic diff results, to explain
how a curriculum revision changed. Candidate results are not persisted as accepted
alignments automatically.

---

## 22. Tool result contract

Use structured Pydantic outputs.

A standard result should include, where available:

```text
node_id
case_identifier_uuid
case_identifier_uri
framework_id
snapshot_id
graph_package_id
framework_name
jurisdiction
jurisdiction_type
issuing_authority
local_subject
normalized_subjects
language
local_grade_labels
normalized_grades
statement_code
alternate_statement_code
description
statement_type
normalized_statement_type
source_status
relationship_warnings
rights
attribution
profile_id
profile_version
resource_links
```

A search hit additionally includes:

```text
retrieval_method
score
matched_terms
matched_fields
```

A tool should return both:

- structured content for clients;
- concise serialized or human-readable text for display and broad client support.

---

## 23. MCP resources

Resources expose read-only authoritative or inspectable context.

### 23.1 URI scheme

Use a custom RFC 3986-compatible scheme:

```text
kgfegmcp://
```

### 23.2 Recommended resources

```text
kgfegmcp://catalog
kgfegmcp://framework/{framework_id}
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/manifest
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/validation
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/unresolved
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/interpretation-profile
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/pipeline-instructions
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/artifact/{artifact_name}
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}/provenance
kgfegmcp://framework/{framework_id}/snapshot/{snapshot_id}/relationship/{relationship_id}
kgfegmcp://alignment/{alignment_id}
```

### 23.3 Artifact allowlist

`artifact_name` must resolve through a strict allowlist from the package manifest. Never concatenate user input into a filesystem path.

### 23.4 Large resources

Raw `as_nodes_XXX.jsonl`, `as_relationships_XXX.jsonl`, and bundles may be large.

Provide:

- full raw resources when rights and client limits permit;
- granular standard and provenance resources;
- metadata indicating size and MIME type;
- optional chunked or paged resources if needed.

### 23.5 Resources are not automatically injected

MCP clients decide how resources are selected and incorporated. Therefore, correctness-critical tool results must contain essential warnings and facts directly, plus resource links for deeper inspection.

### 23.6 Public and audit profiles

Expose two levels where useful:

```text
interpretation-profile
    concise, user-appropriate semantic guidance

pipeline-instructions
    complete extraction, deduplication, and relationship instructions for audit use
```

The audit resource can be hidden or access-controlled in a later remote deployment.

---

## 24. MCP prompts

Prompts are reusable, user-invoked workflows. They should guide Claude to retrieve evidence and clearly label generated content.

Prompts must be versioned and tested as text artifacts.

### 24.1 `student_study_support`

Parameters:

```text
framework_id
grade or stage
topic or standard identifier
language
difficulty
practice_count
```

Workflow:

1. retrieve the source standard;
2. retrieve relevant context;
3. explain in age-appropriate language;
4. provide examples and self-check questions;
5. cite standard identifiers;
6. label explanation and questions as generated;
7. avoid claiming mastery.

### 24.2 `teacher_guide_draft`

Parameters:

```text
framework_id
standard identifiers or topic
grade or stage
lesson duration
learner context
available materials
language
```

Workflow:

1. retrieve standards and hierarchy;
2. separate source-backed expectations from generated pedagogy;
3. draft objectives, activities, questions, differentiation, and checks;
4. include attribution and rights notices;
5. avoid presenting generated activities as officially prescribed.

### 24.3 `student_handbook_section`

Create a student-facing overview grounded in selected standards, with generated examples and practice clearly labeled.

### 24.4 `administrator_alignment_review`

Parameters:

```text
authoritative framework
candidate or local framework
subject
grade or stage scope
comparison dimensions
```

Workflow:

1. retrieve candidate standards;
2. display source text side by side;
3. identify likely matches, broader/narrower cases, gaps, and ambiguity;
4. show retrieval method and evidence;
5. avoid reducing the result to an opaque percentage;
6. require human review before acceptance.

### 24.5 `cross_framework_comparison`

Use `compare_framework_evidence`, then compare wording, scope, cognitive demand, granularity, hierarchy placement, and grade context.

### 24.6 `framework_revision_review`

Parameters:

```text
framework_id
source_snapshot_id
target_snapshot_id
subject or topic scope optional
grade or stage scope optional
comparison dimensions
```

Workflow:

1. call `diff_framework_snapshots` for deterministic changes;
2. call `find_snapshot_alignment_candidates` only for unresolved correspondences;
3. retrieve hierarchy context for important changed records;
4. distinguish exact changes from candidate semantic matches;
5. identify additions, removals, rewrites, grade moves, hierarchy changes, and
   granularity changes;
6. discuss likely educational implications as generated interpretation;
7. cite both exact snapshot IDs and the relevant standard identifiers;
8. avoid treating candidate matches as official equivalence.

### 24.7 `inferred_progression_hypothesis`

Use when no Learning Progressions KG exists.

Required disclosure:

```text
This is an LLM-inferred likely progression based on standards text, grade context,
and curriculum-specific guidance. It is not a source-authored progression edge.
```

The prompt should ask Claude to provide evidence and counter-considerations rather than only a confidence score.

### 24.8 Curriculum profile use in prompts

A prompt should include the selected profile ID/version and the relevant interpretation excerpt.

Do not embed all profiles statically into every prompt. Retrieve the selected profile dynamically.

---

## 25. LLM-inferred progression before a Progressions KG

Reasonable progression hypotheses are useful, but must be typed correctly.

Recommended relationship statuses:

```text
source_asserted_progression
deterministic_grade_order
llm_inferred_progression
human_reviewed_progression
accepted_progression
```

A Grade 2 fraction standard appearing before a Grade 3 fraction standard is deterministic grade order. A claim that the first directly prepares the learner for the second is an inference unless an authoritative progression source states it.

Curriculum-specific profile rules can improve the inference by explaining:

- whether grades are cumulative;
- how recurring practices are expressed;
- what performance verbs imply locally;
- known grade-band conventions;
- when topics recur for fluency rather than progression;
- negative rules that should block a direct progression claim.

The server supplies the evidence and profile. Claude makes the labeled inference.

---

## 26. Cross-framework federation and alignment

Use three complementary layers.

### Layer 1: catalog federation

The catalog knows which frameworks exist and routes searches. It makes no semantic mapping claim.

### Layer 2: runtime evidence comparison

The server retrieves standards from selected frameworks. Claude compares them in the current conversation.

This is exploratory and not persisted as an official crosswalk.

### Layer 3: reviewed derived overlay

Persistent mappings live in a separate overlay with provenance and review status.

### Same-framework snapshot comparison and curriculum revision analysis

The catalog must support several historical and current snapshots of one conceptual
framework at the same time.

Example:

```text
framework_id:
    ghana-nacca-primary-mathematics

source_snapshot_id:
    ghana-nacca-primary-mathematics@2019+abc123

target_snapshot_id:
    ghana-nacca-primary-mathematics@2026+def456
```

This is a first-class use case, not a special case of file replacement. The 2019
snapshot remains queryable after the 2026 snapshot is added.

The comparison has three layers.

#### 1. Deterministic snapshot diff

The server can establish facts without an LLM:

- records present in both snapshots under the same stable identity;
- additions and removals;
- exact description or code changes;
- local or normalized grade changes;
- statement-type changes;
- parent and hierarchy changes;
- relationship additions and removals;
- framework metadata changes;
- changes in unresolved-edge status;
- changes in graph statistics and granularity.

These results should come from `diff_framework_snapshots`.

#### 2. Candidate correspondence

A revised curriculum may mint new identifiers, rename codes, split one standard into
several standards, or merge several standards into one. In those cases, the server can
retrieve likely correspondences using `find_snapshot_alignment_candidates`.

Candidate mappings must:

- retain source and target snapshot IDs;
- expose retrieval evidence and scores;
- support one-to-one, one-to-many, and many-to-one possibilities;
- leave uncertain items unmatched;
- use `retrieval_candidate` status;
- remain separate from accepted alignments.

#### 3. Claude-generated revision evaluation

Claude can combine the deterministic diff and candidate evidence to discuss questions
such as:

- What content was added or removed?
- Which expectations moved to earlier or later grades?
- Did the curriculum become more detailed or more consolidated?
- Which domains received greater or reduced emphasis?
- Were performance verbs or expected cognitive demand changed?
- Which old standards have no clear counterpart?
- What changes may matter for teachers, materials, assessment, or transition planning?

These conclusions are `llm_inferred` interpretations. The evidence package, exact
snapshot IDs, and relevant standards must remain visible.

A result may be persisted later as a reviewed revision crosswalk, but ordinary runtime
comparison must not modify either source package.

#### Snapshot-family metadata

When known, the catalog may record:

```text
revises
supersedes
replaces
derived_from
```

These relations describe framework history. They are distinct from standard-to-standard
semantic alignments.

Do not infer that two snapshots belong to one framework family solely because their
jurisdiction and subject match. Framework-family assignment is an operator-controlled
or authoritative metadata decision.

#### Future Learning Components advantage

Once Learning Components exist, revision comparison can identify retained, added, and
removed teachable skills even when standards are reorganized or rewritten. Until then,
snapshot comparison relies on identifiers, codes, text, grade context, hierarchy, and
clearly labeled candidate retrieval.

### Alignment model

```json
{
  "alignmentId": "...",
  "sourceFrameworkId": "...",
  "sourceSnapshotId": "...",
  "sourceNodeId": "...",
  "targetFrameworkId": "...",
  "targetSnapshotId": "...",
  "targetNodeId": "...",
  "alignmentType": "close_match",
  "direction": "bidirectional",
  "method": "llm_assisted_review",
  "evidence": [],
  "rationale": "...",
  "score": 0.82,
  "status": "proposed",
  "createdBy": "...",
  "reviewedBy": null,
  "model": "...",
  "promptVersion": "...",
  "profileVersions": {},
  "createdAt": "...",
  "reviewedAt": null
}
```

### Relation vocabulary

Use a conservative internal vocabulary influenced by CASE and SKOS:

```text
exact_match
close_match
broader_than
narrower_than
related_to
translation_of
likely_builds_towards
```

Do not claim formal CASE or SKOS conformance unless the complete required model and semantics are implemented.

`exact_match` should require a high evidentiary and governance threshold. It must not be created from lexical similarity alone.

### Version invalidation

An alignment references exact source and target snapshot IDs. When either framework changes, mark the alignment as requiring review rather than silently applying it to the new snapshot.

### Provenance

Record:

- source snapshots;
- retrieval evidence;
- algorithm or model;
- prompt and profile versions;
- human reviewer;
- review decision;
- timestamps;
- supersession history.

W3C PROV concepts such as Entity, Activity, and Agent are useful as a conceptual guide even if the storage format remains Pydantic JSON.

---

## 27. Future Learning Components

Learning Components should become a separate graph type, not extra properties added ad hoc to Academic Standards items.

Expected concepts:

```text
LearningComponent node
supports relationship from component to standard, or the chosen canonical direction
component provenance
component type
language
subject
review status
```

Future capabilities:

- decompose a broad standard into granular teachable skills;
- retrieve components for a standard;
- compare standards through shared components;
- calculate interpretable overlap metrics;
- identify broader and narrower standards;
- generate targeted practice tied to components;
- support component-level gap analysis.

The server catalog should already report graph-type availability so future tools can be added without changing how frameworks are discovered.

---

## 28. Future Learning Progressions

Learning Progressions must remain semantically distinct from hierarchy.

Expected relationship types may include:

```text
buildsTowards
relatesTo
recurringPractice
```

Future capabilities:

- retrieve backward and forward progression evidence;
- distinguish developmental prerequisites from recurring practice;
- construct review pathways;
- generate prior-knowledge practice;
- identify follow-on expectations.

Even with a Learning Progressions KG, avoid universal claims unless the source itself asserts a universal prerequisite.

---

## 29. General graph-type extensibility

Create a registry of graph-type adapters:

```python
class GraphTypeAdapter(Protocol):
    graph_type: str

    def validate_node(self, node: RawNode) -> None: ...
    def validate_relationship(self, relationship: RawRelationship) -> None: ...
    def capabilities(self) -> dict[str, bool]: ...
```

Initial adapter:

```text
academic_standards
```

Future adapters:

```text
learning_components
learning_progressions
curriculum
assessment
reviewed_alignment
```

The common catalog and package layers remain graph-type agnostic. Graph-type services own domain-specific behavior.

---

## 30. Local Claude Desktop deployment

### 30.1 Development transport

Use STDIO first.

```text
Claude Desktop launches the FastMCP process.
The server reads MCP messages from stdin.
The server writes MCP messages to stdout.
Logs go to stderr.
The graph packages remain local.
```

### 30.2 FastMCP commands

Exact commands depend on the FastMCP version (we are using version 3.4.4), but the expected workflow is:

From the repository root:

```bash
cd backend
uv run fastmcp inspect src/kgfegmcp/app.py:mcp
uv run fastmcp run src/kgfegmcp/app.py:mcp --transport stdio
uv run fastmcp install claude-desktop src/kgfegmcp/app.py:mcp --with-editable .
```

Equivalent root Makefile targets may wrap these commands, but backend commands and
dependency resolution should remain owned by `backend/pyproject.toml`.

`backend/fastmcp.json` can centralize the entrypoint, dependency, and environment configuration.

### 30.3 Environment configuration

Use absolute paths or a project-root environment variable because Claude Desktop launches the process from its own environment.

Supported application-owned variables:

```text
KGFEGMCP_CONFIG
KGFEGMCP_CONFIG_ROOT
KGFEGMCP_SERVER_CONFIG
KGFEGMCP_CATALOG
KGFEGMCP_PROFILE_ROOT
KGFEGMCP_DATA_ROOT
KGFEGMCP_GRAPH_PACKAGES_ROOT
KGFEGMCP_DERIVED_ROOT
KGFEGMCP_CACHE_ROOT
KGFEGMCP_LOG_ROOT
KGFEGMCP_RESULTS_ROOT
KGFEGMCP_INVALID_PACKAGE_POLICY
KGFEGMCP_LOG_LEVEL
KGFEGMCP_ENV
```

`PATHS_PROJECT_DIR` remains a supported fallback for the repository root because it is
already provided by the root environment and `direnv`. Application-owned
`KGFEGMCP_*` values take precedence. Relative overrides are resolved from the configured
project root, never from the caller's current working directory.

### 30.4 Manual smoke test

After installation:

1. restart Claude Desktop;
2. verify the server appears in connectors/developer settings;
3. list tools, resources, and prompts;
4. call `list_frameworks`;
5. search a coded framework;
6. search an uncoded framework;
7. retrieve a multi-parent India Science node context;
8. retrieve a Ghana unresolved relationship warning;
9. read a validation resource;
10. verify no protocol-corrupting stdout logs appear.

### 30.5 Later packaging

After local development stabilizes, consider MCPB for one-click local installation and dependency bundling.

Remote Streamable HTTP hosting is a later deployment phase and will require authentication, authorization, rate limiting, and centralized package update policy.

---

## 31. Security, privacy, and safety

### 31.1 Read-only first

All initial tools are read-only. No tool should modify packages, write alignments, or persist student data.

### 31.2 Resource path safety

- validate custom URIs;
- resolve only manifest-declared artifacts;
- reject `..`, absolute paths, symlinks escaping the data root, and unknown artifact names;
- enforce size limits;
- set correct MIME types.

### 31.3 Input limits

Enforce:

```text
maximum query length
maximum framework count per request
maximum page size
maximum traversal depth
maximum returned nodes
maximum comparison matches per framework
maximum resource size
```

### 31.4 Treat source text as untrusted data

Standards descriptions, notes, and source artifacts can contain text that resembles instructions. They must be treated as quoted data, not system instructions.

Curriculum profiles are trusted operator configuration and must be separately validated and versioned.

### 31.5 Student privacy

Do not request or persist:

- student names;
- IDs;
- disability information;
- assessment histories;
- grades or disciplinary data;
- other sensitive learner records.

Student prompts should work with anonymous grade, topic, and learning-context inputs.

### 31.6 Administrative claims

Alignment evidence must remain reviewable and decomposable. Avoid an opaque single-number judgment as the primary output.

### 31.7 Licensing and attribution

Every package needs a rights policy.

At minimum track:

```text
license text or URI
attribution statement
rights review status
full-text display permission
bulk-export permission
derivative-generation policy
```

Unknown or unspecified rights must be visible. Rights policy can gate raw resources or generated-derivative prompts.

---

## 32. Observability

### 32.1 Logging

Use structured logging to stderr.

Include:

```text
timestamp
level
request_id
operation
framework_id
snapshot_id
result_count
duration_ms
error_type
```

Do not log full user prompts, student information, or entire standards payloads by default.

### 32.2 Metrics

Useful metrics:

```text
startup duration
loaded package count
quarantined package count
node and relationship counts
search latency
traversal latency
resource reads
tool error counts
cache hit rates
```

---

## 33. Performance and scaling

The current corpus is small enough for an in-memory graph representation.

Recommended initial choices:

- load immutable package state once at startup;
- use dictionaries and adjacency lists for graph access;
- use a simple lexical index or SQLite FTS5;
- use deterministic cursor pagination;
- avoid a network database in Phase 1;
- keep repository interfaces storage-agnostic.

Reconsider storage when one or more of the following become material:

```text
hundreds of thousands or millions of nodes
frequent package updates without restart
many concurrent remote users
complex graph analytics
large alignment overlays
semantic vector retrieval at scale
multi-tenant access control
```

Possible later backends include SQLite, PostgreSQL, a graph database, a search service, or a vector database. The MCP surface should not depend on the choice.

---

## 34. Testing strategy

### 34.1 Test location and execution conventions

- Put test modules under `backend/tests/kgfegmcp`.
- Keep shared files and minimized graph packages under `backend/tests/fixtures`.
- Reuse `backend/tests/conftest.py`, `constants.py`, and `types_.py` when their existing
  responsibilities fit.
- Run the deterministic suite from `backend`, for example:

```bash
cd backend
uv run pytest
```

- Tests must use temporary directories for generated catalogs, indexes, caches, and
  package manifests.
- Manifest-builder tests must use temporary output roots and must not overwrite immutable
  package fixtures.
- Tests must not mutate repository-level `data/`, `results/`, or source graph packages.
- Full curriculum packages may be used in explicit integration tests, while most unit
  tests should use minimized fixtures preserving the relevant topology or edge case.

### 34.2 Unit tests (using pytest ecosystem)

Test:

- manifest validation;
- profile validation;
- string-encoded property decoding;
- identifier alias resolution;
- code matching;
- lexical normalization;
- cursor encoding and decoding;
- resource URI validation;
- rights policy;
- graph traversal;
- cycle detection;
- all-root-path traversal;
- error translation.

### 34.3 Package fixture tests

Use the six current packages as integration fixtures or create minimized fixtures preserving their important properties.

Required assertions:

| Fixture | Required assertion |
|---|---|
| Ghana English | 430 items; 430 edges; 2 unresolved fallbacks; English subject alias mapping |
| Ghana Mathematics | 302 items; 302 edges; 13 unresolved fallbacks |
| Nigeria Mathematics | 242 items; no statement codes; text search works |
| Tamil Nadu Mathematics | 255 items; partial code coverage |
| India Science | 874 items; 1,109 edges; 235 multi-parent items; all paths preserved |
| Rwanda Mathematics | 626 items; no statement codes; source hierarchy preserved |

### 34.4 Graph invariant tests

For every valid package:

- all endpoints exist;
- root exists;
- no `hasChild` cycles;
- expected reachability holds;
- multiple parents are not collapsed;
- unresolved statuses survive loading and output;
- node and relationship counts remain stable.

### 34.5 Snapshot comparison tests

Create minimized fixture pairs representing:

- unchanged records;
- additions and removals;
- description and statement-code changes;
- grade moves;
- hierarchy moves;
- one standard split into several;
- several standards merged into one;
- framework metadata changes;
- a corrected extraction that creates a new snapshot;
- ambiguous records that should remain unmatched.

Required assertions:

- historical snapshots remain independently queryable;
- the diff result references both exact snapshot IDs;
- deterministic changes do not depend on an LLM;
- candidate correspondence never becomes `source_asserted`;
- one-to-many and many-to-one candidates are preserved;
- a new snapshot invalidates or flags prior snapshot-specific derived mappings.

### 34.6 MCP contract tests

Use FastMCP's in-memory client to test the real protocol layer without subprocesses.

Test:

- tool listing;
- resource listing and reading;
- prompt listing and retrieval;
- structured output schemas;
- controlled errors;
- pagination;
- annotations;
- resource links.

### 34.7 STDIO tests

Add a smaller set of subprocess tests to ensure:

- startup works;
- no stdout log corruption occurs;
- environment variables are passed correctly;
- process exits cleanly.

### 34.8 Prompt snapshot tests

Prompts do not need an LLM test in the core suite. Snapshot their generated messages and assert required disclosures, resource references, and profile versions.

### 34.9 No-LLM deterministic CI

The complete core test suite must run without network access or an LLM API key.

---

## 35. Implementation phases

## Phase 0: freeze contracts and fixtures

**Status:** Substantially implemented. Remaining work is limited to formal ADR files,
tool input/output model drafts, and automated tests.

### Implemented deliverables

- package manifest Pydantic models;
- curriculum profile Pydantic models;
- framework-independent enums and epistemic-status vocabulary;
- typed identifier contracts and deterministic ID builders;
- typed domain-error hierarchy;
- shared rights and normalized-subject models;
- operator-assigned framework IDs for all six current frameworks;
- versioned profile IDs and central profile-root layout;
- six initial profile JSON files derived from the upstream runtime configurations;
- repository path settings and environment template;
- fixture inventory and expected counts;
- public naming conventions.

### Deferred deliverables

- initial ADR files capturing the accepted decisions;
- tool input/output model drafts;
- automated unit tests for the foundational contracts.

### Exit criteria status

- all six package identities can be represented: satisfied;
- multiple Ghana frameworks coexist: satisfied;
- India Science multi-parent topology is explicitly represented in profile policy:
  satisfied;
- unresolved fallbacks are represented: satisfied;
- no current country name appears in generic model validators: satisfied;
- source paths are rooted under `backend/src/kgfegmcp`: satisfied;
- automated tests: deferred by operator and still required before production readiness.

---

## Phase 1: package construction, loading, validation, catalog, and graph domain

**Status:** In progress. PR 2 completed the JSONL wire boundary and semantic graph-record
conversion. PR 3 deterministic manifest construction is the next unit.

### Implemented deliverables

- strict Learning Commons-shaped node and relationship wire models;
- line-by-line JSONL parsing with safe file and line context;
- strict delivery-property decoding;
- raw and unknown property preservation;
- semantic framework, standard, and relationship records;
- preservation of unresolved statuses and all endpoint representations.

### Remaining deliverables

- deterministic manifest builder driven by versioned profiles and accepted `as_*`
  artifacts;
- reusable manifest-build CLI and six generated package fixtures;
- manifest loader and repository;
- profile loader and repository;
- checksum verification during package loading;
- immutable loaded-package aggregate;
- package validator and validation CLI;
- detailed-artifact path support;
- DAG-aware graph store;
- catalog repository.

### Exit criteria

- all six complete packages load simultaneously by the end of Phase 1;
- an incomplete package fails or quarantines according to policy;
- node and edge counts match fixtures;
- India Science returns all parents after the graph-store unit;
- Ghana fallback statuses remain visible;
- identifiers do not assume `identifier == caseIdentifierUUID`;
- codeless packages load without warnings that imply invalidity.

---

## Phase 2: FastMCP server foundation

### Deliverables

- standalone FastMCP application under `backend/src/kgfegmcp`;
- lifespan-loaded immutable application state;
- explicit tool, resource, and prompt registration in `mcp/register.py`;
- base structured result and error-translation contracts;
- controlled `ToolError` behavior for expected domain failures;
- in-memory MCP tests;
- STDIO smoke test;
- Claude Desktop development installation instructions.

### Exit criteria

- the FastMCP application starts and stops cleanly;
- duplicate tools, resources, and prompts fail startup;
- expected domain errors are translated into stable public errors;
- unexpected errors are masked and logged;
- no protocol output is polluted by logs;
- Claude Desktop can connect locally and enumerate the components registered at that
  implementation phase.

---

## Phase 3: canonical multi-framework tools

### Deliverables

- `list_frameworks`;
- `get_framework`;
- `search_standards`;
- `get_standard`;
- `get_standard_context`;
- `get_framework_statistics`;
- `get_capabilities`;
- cursor pagination;
- subject and grade normalization through profiles;
- lexical ranking;
- code exact and prefix search.

### Exit criteria

- queries can target one or several frameworks;
- jurisdiction is never used as a unique key;
- codeless and partially coded frameworks behave correctly;
- all root paths can be returned for DAG nodes;
- source and normalized values are both returned;
- every result includes snapshot identity and profile version.

---

## Phase 4: resources and audit context

### Deliverables

- catalog resource;
- framework and manifest resources;
- validation and unresolved resources;
- profile resources;
- standard provenance resources;
- strict artifact allowlist;
- rights-aware resource policy;
- resource links in tool results.

### Exit criteria

- users can inspect detailed artifacts without exposing arbitrary files;
- large resources are size-limited or clearly annotated;
- essential correctness warnings remain in tools even when resources are not read;
- invalid resource URIs are rejected safely.

---

## Phase 5: role-oriented prompts

### Deliverables

- student study support prompt;
- teacher guide prompt;
- student handbook prompt;
- administrator alignment review prompt;
- cross-framework comparison prompt;
- inferred progression prompt;
- prompt versioning and snapshot tests.

### Exit criteria

- prompts instruct Claude to retrieve source evidence;
- generated content is labeled;
- no prompt claims official mastery, equivalence, progression, activity, or grade equivalence without evidence;
- curriculum profile context is included dynamically.

---

## Phase 6: deterministic cross-framework and snapshot comparison evidence

### Deliverables

- `compare_framework_evidence`;
- `diff_framework_snapshots`;
- `find_snapshot_alignment_candidates`;
- cross-framework and same-framework comparison result schemas;
- per-framework retrieval and context;
- comparison warnings;
- optional pluggable semantic retrieval interface;
- evaluation dataset of known comparison queries.

### Exit criteria

- a topic such as fractions can be retrieved across selected frameworks;
- two historical/current snapshots of one framework can be diffed without overwriting
  either snapshot;
- additions, removals, exact field changes, and topology changes are deterministic;
- semantic correspondences without stable identity are labeled retrieval candidates;
- one-to-many and many-to-one revision candidates are supported;
- all source statements and paths are visible;
- no persistent equivalence edge is created.

---

## Phase 7: reviewed alignment overlay

### Deliverables

- alignment schema;
- read-only alignment repository;
- proposed/reviewed/accepted statuses;
- snapshot invalidation rules;
- alignment resource and retrieval tools;
- separate administrative workflow for creating or reviewing alignments.

### Exit criteria

- source packages remain unchanged;
- every alignment references exact snapshots and evidence;
- broader, narrower, related, close, and exact relationships are distinguished;
- exact mappings require explicit review policy;
- updates flag stale mappings.

---

## Phase 8: Learning Components

### Deliverables

- graph-type adapter;
- component nodes and `supports` relationships;
- component search and retrieval;
- standard-to-component tools;
- component-overlap comparison;
- updated capabilities.

### Exit criteria

- component results retain provenance and review status;
- Academic Standards tools remain backward compatible;
- crosswalk evidence can use shared components.

---

## Phase 9: Learning Progressions

### Deliverables

- progression graph adapter;
- backward and forward traversal;
- relation subtype support;
- source-authored versus inferred distinction;
- progression prompts and tools.

### Exit criteria

- hierarchy and progression remain distinct;
- source progressions and LLM hypotheses are not conflated;
- progressions are versioned and evidence-bearing.

---

## Phase 10: packaging and remote hosting

### Deliverables

- MCPB packaging for local distribution;
- remote Streamable HTTP deployment option;
- authentication and authorization;
- rate limiting;
- centralized package update mechanism;
- tenant and framework visibility policy;
- production telemetry.

### Exit criteria

- local and remote transports share the same domain services and public schemas;
- remote access is authenticated;
- rights and audit policy are enforced;
- package updates are versioned and rollbackable.

---

## 36. Suggested implementation sequence by pull request

1. **PR 1 — implemented:** domain identifiers, enums, shared domain models, errors,
   manifest models, profile models, repository path settings, environment template, and
   six initial versioned profiles.
2. **PR 2 — implemented:** strict Learning Commons-shaped JSONL wire models,
   one-line-at-a-time parsing, delivery-property decoding, typed parsing and decoding
   errors, and semantic graph-record models.
3. **PR 3 — next:** deterministic manifest construction from versioned profiles and
   accepted `as_*` delivery and detailed artifacts, plus a reusable manifest-build CLI
   and six generated package fixtures.
4. **PR 4:** manifest and profile repositories, package checksum verification, immutable
   loaded-package assembly, package-wide validation, and a validation CLI.
5. **PR 5:** DAG-aware graph store and deterministic traversal.
6. **PR 6:** catalog repository and six-package integration.
7. **PR 7:** lexical and profile-controlled code search.
8. **PR 8:** FastMCP bootstrap, lifespan, explicit registration, logging, and error
   translation.
9. **PR 9:** canonical framework and standards tools.
10. **PR 10:** resources and strict URI resolver.
11. **PR 11:** role-oriented prompts and prompt snapshots.
12. **PR 12:** comparison evidence services.
13. **PR 13:** Claude Desktop packaging and STDIO smoke coverage.
14. **Later PRs:** alignment overlay, Learning Components, Learning Progressions, and
    remote hosting.

Each PR should leave the repository importable and reviewable. Deterministic tests remain
part of the production acceptance criteria even while temporarily deferred by operator
instruction.

### PR 2 implementation record

PR 2 added or updated:

```text
backend/src/kgfegmcp/packages/wire.py
backend/src/kgfegmcp/packages/decoder.py
backend/src/kgfegmcp/graph/__init__.py
backend/src/kgfegmcp/graph/models.py
backend/src/kgfegmcp/errors.py
backend/src/kgfegmcp/packages/models.py
backend/src/kgfegmcp/profiles/models.py
```

The changes to `packages/models.py` and `profiles/models.py` were limited to explicit
typing of existing version defaults so full-project static type checking succeeds. They
did not change the established manifest or profile contracts.

PR 2 intentionally did not add package validation, graph storage, traversal, catalog,
search, FastMCP behavior, resources, prompts, or tests.

### Next implementation unit: PR 3 deterministic manifest construction

PR 3 must remain limited to constructing reproducible `package_manifest.json` files and package
fixture directories from the already implemented profile and decoder contracts. Do not
add the full package loader, package-wide validator, DAG graph store, catalog, search
service, FastMCP application, tools, resources, or prompts in this unit.

Expected files to add or update:

```text
backend/src/kgfegmcp/packages/checksums.py
backend/src/kgfegmcp/packages/builder.py
backend/src/kgfegmcp/profiles/loader.py
backend/src/kgfegmcp/cli/__init__.py
backend/src/kgfegmcp/cli/build_manifests.py
backend/src/kgfegmcp/errors.py                    # only if a concrete typed gap exists
backend/src/kgfegmcp/packages/models.py           # only for build request/result models
backend/pyproject.toml                            # only if adding a stable CLI entry point
```

Do not split the builder into additional modules unless inspection shows a clear
responsibility that cannot remain cohesive in the files above.

#### PR 3 manifest inputs

The builder must accept:

```text
profile_id
profile_version
authoritative version_token
jurisdiction_type when not already represented by the established contract
as_nodes_XXX.jsonl
as_relationships_XXX.jsonl
optional directory or explicit list of detailed as_* artifacts
output graph-packages root
optional source_publication_date
optional package_revision, defaulting to 1
optional operator-approved snapshot relations
```

The builder must resolve profiles beneath the configured central profile root. It must
not accept an arbitrary profile filesystem path as the package's permanent profile
reference.

The upstream extraction runtime configuration and `kgs.as` are not required inputs.
They may be preserved separately as audit provenance or used by an operator to review
profile drift, but manifest construction must be reproducible from the selected profile,
accepted `as_*` artifacts, and explicit package-build identity values.

#### PR 3 responsibilities

1. Resolve and validate the selected profile by `profile_id` and `profile_version`
   beneath the configured profile root.
2. Calculate the exact SHA-256 checksum of the selected `profile.json` bytes.
3. Use the existing decoder to stream and decode `as_nodes_XXX.jsonl` and
   `as_relationships_XXX.jsonl`; do not duplicate wire parsing or property decoding.
4. Require exactly one decoded `StandardsFramework` root before constructing a manifest.
5. Read source-facing framework metadata from the decoded framework root and obtain
   normalized subjects, grade mappings, language policy, code policy, hierarchy policy,
   source-role capabilities, and operator rights policy from the selected profile.
6. Compare overlapping deterministic values from the profile and framework root. Fail
   with a typed, actionable error on a material mismatch; do not silently repair either
   source.
7. Calculate manifest counts from decoded records, including framework nodes, item
   nodes, relationships, coded items, unresolved statuses, and multi-parent targets as
   applicable to the established manifest model.
8. Derive evidence-backed capabilities from the profile and actual graph, including
   code-search availability, text search, multi-parent topology,
   `hasUnresolvedRelationships`, detailed provenance availability, and declared official
   source-role capabilities.
9. Preserve the accepted upstream artifact filenames. Delivery files use the canonical
   `as_nodes_XXX.jsonl` and `as_relationships_XXX.jsonl` names. Detailed files use the
   canonical names:

   ```text
   as_kg_bundle.json
   as_standards_framework.json
   as_standards_framework_items.jsonl
   as_relationships_has_child.jsonl
   as_entity_provenance.json
   as_unresolved_items.json
   as_validation_report.json
   ```

   Do not add fallback support for the former unprefixed filenames.
10. Copy or hard-link accepted artifacts into a staging package directory without
    changing their bytes. The implementation must be explicit and deterministic about
    which strategy it uses.
11. Calculate SHA-256 checksums for every declared package artifact and include exactly
    one checksum entry per declared artifact path.
12. Calculate the snapshot content hash from the canonical ordered list of checksums for
    all declared immutable source snapshot artifacts. Exclude the manifest itself,
    profile files, caches, indexes, logs, and generated results.
13. Build `snapshot_id` from the profile's operator-assigned `framework_id`, the explicit
    authoritative `version_token`, and the 12-character snapshot hash. Build the initial
    `graph_package_id` according to the established package-revision contract.
14. Construct the existing `GraphPackageManifest` model in memory with
    `validation.status="pending"` and `validatedAt=null`, then serialize it as
    deterministic UTF-8 JSON with stable field aliases and formatting.
15. Write `package_manifest.json` only after all build-time checks succeed. Materialize the
    staged candidate package atomically in the configured build output when the
    filesystem supports it. A pending package is not queryable or production-ready until
    PR 4 validation succeeds.
16. Refuse to overwrite an existing terminal immutable package. If an exact pending
    candidate already exists, report it idempotently without changing source artifacts.
17. Return or print a concise build summary containing the exact framework, snapshot,
    graph-package, and profile identities; artifact paths and checksums; counts;
    capabilities; pending validation status; and warnings.
18. Never edit, normalize, repair, reorder, or rewrite the source JSONL or detailed
    artifacts.

#### PR 3 boundaries

- PR 3 constructs and Pydantic-validates pending manifests; PR 4 performs full package
  loading and graph-wide acceptance validation. PR 4 may make the controlled one-way
  manifest transition from `pending` to a terminal validation status before publication;
  it must not change package identity, artifact paths, checksums, counts, profile
  reference, or source metadata during that transition.
- PR 3 may calculate topology facts needed for manifest capabilities, such as whether a
  target has multiple parents. It must not expose adjacency indexes or traversal APIs.
- PR 3 must not implement endpoint-resolution acceptance, duplicate-identifier
  acceptance, cycle detection, reachability acceptance, or detailed validation-report
  acceptance as substitutes for the PR 4 validator. It may fail only when a condition
  prevents an internally coherent manifest from being constructed.
- The selected profile is the stable MCP policy contract. Do not make the upstream
  extraction runtime config a required dependency.
- Do not infer an authoritative version token from filenames, local paths, extraction
  timestamps, or runtime years.
- No country, curriculum, organization, subject, grade, statement-type, or code-specific
  conditional may appear in generic Python.
- Do not introduce backward-compatibility shims for former artifact names without the
  `as_` prefix.
- New modules, classes, methods, and functions require complete docstrings and precise
  type hints.
- Calls to functions with more than one argument must use alphabetically ordered named
  arguments. One-argument calls do not require a named argument.
- Automated tests remain deferred until explicitly requested. Run formatting, linting,
  full type checking, compilation, six-fixture positive smoke builds, and representative
  negative build checks before returning files.

#### PR 3 acceptance checks

- six deterministic `package_manifest.json` files are generated from the six versioned profiles
  and their accepted `as_*` artifacts;
- each generated package uses the canonical
  `data/graph_packages/<framework-id>/<snapshot-id>/` layout;
- delivery and detailed artifact filenames retain their upstream `as_` prefixes;
- artifact and profile checksums match the exact source bytes;
- repeated builds from identical inputs produce the same snapshot and graph-package
  identities and byte-equivalent manifests apart from an explicitly documented
  timestamp policy;
- framework and item node counts, relationship counts, code coverage, unresolved-status
  evidence, and multi-parent evidence match the decoded artifacts;
- India Science is described as multi-parent without collapsing its 235 multi-parent
  targets;
- all 15 unresolved fallback relationships remain represented in package evidence;
- codeless and partially coded frameworks receive correct code-search capabilities from
  profile policy and actual graph evidence;
- missing profiles, profile mismatches, malformed graph files, missing explicit version
  tokens, unsupported artifact names, duplicate declared paths, checksum failures,
  unsafe output paths, and attempts to overwrite an immutable package produce typed
  failures;
- no source artifact is changed;
- the repository remains importable and passes the required static and smoke checks.

## 37. Packaging current curriculum artifacts

PR 3 provides a reusable manifest-build CLI owned by KGForEdGlobalMCP.

Illustrative command from the repository root:

```bash
uv --directory backend run python -m kgfegmcp.cli.build_manifests \
  --profile-id ghana-nacca-primary-english-language-basic-1-3 \
  --profile-version 1.0 \
  --version-token 2019 \
  --jurisdiction-type country \
  --nodes /absolute/path/to/as_nodes_ghana_english.jsonl \
  --relationships /absolute/path/to/as_relationships_ghana_english.jsonl \
  --detailed-root /absolute/path/to/detailed_artifacts \
  --output-root ../data/graph_packages
```

The CLI must resolve the selected profile beneath the configured central profile root.
It must not require an arbitrary `--profile` path and must not require an upstream
runtime configuration.

The CLI should:

1. load the selected profile;
2. decode the `as_nodes_XXX.jsonl` and `as_relationships_XXX.jsonl` inputs through the
   existing decoder;
3. locate exactly one framework root;
4. compare deterministic framework-root metadata with the selected profile;
5. require explicit operator-approved identity values that are not derivable safely,
   especially the authoritative version token;
6. preserve the original `as_*` artifact filenames;
7. discover only the recognized optional detailed `as_*` artifacts, or accept them
   through explicit named arguments;
8. copy or hard-link artifacts into a staging package directory without changing bytes;
9. compute artifact and profile checksums;
10. derive counts and manifest capabilities;
11. calculate the snapshot hash and immutable package identities;
12. build and Pydantic-validate the manifest;
13. atomically materialize the pending candidate package directory;
14. print identities, counts, checksums, capabilities, warnings, pending validation
    status, and the final manifest location;
15. never overwrite an existing terminal immutable package or edit source artifacts.

Full graph-wide package acceptance remains the responsibility of the PR 4 validation
CLI. Manifest construction success means that the pending package description is
internally well-formed and reproducible; it does not replace full endpoint, uniqueness,
topology, reachability, profile-semantic, and detailed-report validation. PR 4 owns the
controlled transition to a terminal validation status.

Do not derive final package identity solely from a filename, extraction runtime year, or
local path.

---

## 38. Decision log

### ADR-001: standalone FastMCP

Accepted. It provides the desired high-level MCP features while allowing exact public errors through `ToolError`.

### ADR-002: one catalog-driven server

Accepted. Frameworks are selected by stable identity and facets, not by separate server instances.

### ADR-003: immutable versioned graph packages

Accepted. Corrections create new snapshots.

### ADR-004: source graphs remain separate

Accepted. Federation occurs through the catalog and services.

### ADR-005: DAG-aware graph model

Accepted. Multi-parent relationships are first-class.

### ADR-006: external curriculum profiles

Accepted. Generic code does not contain curriculum-specific semantics.

### ADR-007: detailed artifacts as MCP resources

Accepted. Tools still return essential facts and warnings.

### ADR-008: no server-side LLM in the initial design

Accepted. Claude Desktop performs reasoning and generation.

### ADR-009: derived alignments live in overlays

Accepted. Source package relationships are not mutated.

### ADR-010: local and normalized values coexist

Accepted. Normalization is for discovery and comparison, not replacement of source wording.

### ADR-011: historical and current snapshots coexist

Accepted. A new curriculum version does not overwrite an earlier snapshot. Deterministic
snapshot diffs and candidate correspondence are separate operations, and every comparison
references exact snapshot IDs.

### ADR-012: operator-assigned framework identity

Accepted. `framework_id` uses a stable authority/family/subject/scope identity and omits
year, provider, and content hash.

### ADR-013: deterministic snapshot and package identity

Accepted. `snapshot_id` uses `<framework-id>@<version-token>+<12-character-hash>`.
`graph_package_id` initially equals `snapshot_id` and later supports graph-type-specific
package revisions.

### ADR-014: central profile root

Accepted. Manifests store profile ID, version, and checksum only. Profile files resolve
beneath a configured central profile root.

### ADR-015: versioned normalized-subject vocabulary

Accepted. The initial vocabulary is Learning Commons-shaped configuration with an
explicit `Other` value and separate `mapped`, `other`, and `unreviewed` mapping states.

### ADR-016: rights facts and exposure policy remain separate

Accepted. Source license and attribution are preserved exactly. Operator exposure
decisions are modeled separately and do not rewrite source rights.

### ADR-017: normalized statement types are deterministic upstream derivations

Accepted. Exported normalized statement types are preserved and validated against the
selected profile. Generic loaders do not silently recalculate or repair them.

### ADR-018: current repository root compatibility

Accepted. Application-owned `KGFEGMCP_*` path settings take precedence.
`PATHS_PROJECT_DIR` remains a supported repository-root fallback for the existing root
environment and `direnv`. Relative overrides resolve from the configured project root,
never from the caller's current working directory.

### ADR-019: one strict delivery boundary

Accepted. `packages/wire.py` preserves the source-shaped Learning Commons delivery
envelopes, and `packages/decoder.py` is the only layer that decodes string booleans and
embedded JSON arrays. Unknown string properties are retained, explicit non-string
property values are rejected, and parsing remains separate from package validation.

### ADR-020: artifact-local semantic graph records

Accepted. `graph/models.py` contains frozen semantic records for decoded nodes and
relationships. Outer and property identifiers, CASE identifiers, outer and
property-declared endpoints, resolution status, raw properties, and source export order
remain distinct. Package identity is attached by the package loader rather than copied
or inferred inside every record.

### ADR-021: physical line order is source export order

Accepted. `source_export_order` is the one-based physical JSONL line number. It provides
deterministic display and diagnostics but does not assert instructional sequence or
progression.

### ADR-022: manifests are generated inside KGForEdGlobalMCP

Accepted. Versioned profiles, decoded accepted graph artifacts, and explicit
operator-approved package identity values are sufficient to generate package manifests.
The upstream extraction runtime configuration is optional provenance and profile-review
evidence, not a required package-build dependency.

### ADR-023: `as_` artifact names are canonical

Accepted. The package builder preserves the current upstream `as_` prefixes for delivery
and detailed Academic Standards artifacts. Generic code does not add compatibility
fallbacks for former unprefixed artifact names.

---

## 39. Defaults for currently open implementation choices

These are defaults, not permanent constraints.

| Question | Default |
|---|---|
| Search backend | In-memory indexes plus SQLite FTS5 if available |
| Package invalidity | Fail startup in development and CI |
| Package reload | Restart server; no hot reload in production |
| Public API casing | Pythonic internal models; stable documented MCP field aliases |
| Framework identity | Operator-assigned authority/family/subject/scope kebab-case ID |
| Snapshot identity | Version token plus canonical 12-character artifact-set hash |
| Graph package identity | Equal to snapshot initially; graph-type package revisions later |
| Subject vocabulary | Versioned Learning Commons-shaped vocabulary with `Other` |
| Profile resolution | Central configured root by profile ID and version |
| Manifest construction | Versioned profile + accepted `as_*` artifacts + explicit version token |
| Artifact naming | Preserve canonical upstream `as_` prefixes |
| Rights | Preserve source facts; apply separate operator exposure policy |
| Semantic search | Interface only until lexical search is evaluated |
| Alignment persistence | Read-only and absent in initial milestone |
| Raw large resources | Disabled unless rights and size policy allow |
| Profile format | JSON for machine policy plus Markdown for interpretation |
| Logging | Structured stderr, no full prompt logging |
| Client generation | Claude Desktop only |

---

## 40. Definition of done for the first production milestone

The first production milestone is complete when:

1. standalone FastMCP under `backend/src/kgfegmcp` runs through Claude Desktop over STDIO;
2. all six current graph packages load at once;
3. adding a seventh package requires no generic-code changes;
4. framework identity is not jurisdiction-based;
5. coded, partially coded, and uncoded frameworks all search correctly;
6. India Science multi-parent paths are preserved;
7. Ghana unresolved fallbacks are visible in context results;
8. source and normalized subject and grade values are both available;
9. tools return structured Pydantic outputs and stable public errors;
10. detailed validation, unresolved, profile, and provenance artifacts are available through safe resources;
11. student, teacher, administrator, comparison, and inferred-progression prompts are available;
12. prompts clearly label generated and inferred content;
13. no server-side LLM or sampling is required;
14. source packages remain immutable;
15. deterministic tests pass without network access;
16. no country- or curriculum-specific semantic rule exists in generic Python;
17. rights and attribution metadata appear in results and resource policy;
18. multiple historical/current snapshots of one framework can coexist and be compared
    reproducibly by exact snapshot ID;
19. the FastMCP application and canonical tools satisfy their contract and STDIO smoke tests.

---

## 41. Official references

The following references informed this architecture. Pin implementation behavior to the versions selected by the project and re-check documentation when upgrading dependencies.

### FastMCP

- [FastMCP server](https://gofastmcp.com/servers/server)
- [FastMCP tools and structured output](https://gofastmcp.com/servers/tools)
- [FastMCP resources and templates](https://gofastmcp.com/servers/resources)
- [FastMCP prompts](https://gofastmcp.com/servers/prompts)
- [FastMCP lifespans](https://gofastmcp.com/servers/lifespan)
- [FastMCP providers](https://gofastmcp.com/servers/providers/overview)
- [FastMCP middleware](https://gofastmcp.com/servers/middleware)
- [FastMCP Claude Desktop integration](https://gofastmcp.com/integrations/claude-desktop)
- [FastMCP tests](https://gofastmcp.com/v2/development/tests)

### Model Context Protocol

- [MCP specification](https://modelcontextprotocol.io/specification/2025-11-25)
- [MCP tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [MCP resources](https://modelcontextprotocol.io/specification/2025-11-25/server/resources)
- [MCP prompts](https://modelcontextprotocol.io/specification/2025-06-18/server/prompts)

### Learning Commons

- [Knowledge Graph quickstart](https://docs.learningcommons.org/knowledge-graph/getting-started/quickstart)
- [Knowledge Graph MCP server](https://docs.learningcommons.org/knowledge-graph/using-knowledge-graph/mcp-server)
- [Standards crosswalks through shared Learning Components](https://docs.learningcommons.org/api-reference/standards-crosswalks/crosswalks-for-a-standard)
- [Claude connector examples](https://docs.learningcommons.org/knowledge-graph/using-knowledge-graph/claude-connector)

### Education data and mapping standards

- [1EdTech CASE 1.1 specification](https://www.imsglobal.org/spec/case/v1p1/)
- [1EdTech CASE 1.1 implementation guide](https://www.imsglobal.org/spec/CASE/v1p1/impl)
- [W3C SKOS reference](https://www.w3.org/TR/skos-reference/)
- [W3C PROV-O](https://www.w3.org/TR/prov-o/)
- [UNESCO ISCED](https://www.uis.unesco.org/en/methods-and-tools/isced)

---

## 42. Final implementation rule

When a design choice is unclear, prefer the option that:

1. does not silently guess when a material requirement is ambiguous;
2. records a visible assumption or asks for clarification when necessary;
3. preserves source meaning and topology;
4. makes provenance and uncertainty visible;
5. keeps generic code curriculum-agnostic;
6. uses deterministic services before LLM inference;
7. leaves future graph types and storage backends open;
8. can be tested without Claude;
9. does not overstate educational authority.

IF UNCERTAIN, ASK THE USER FOR CLARIFICATION. DO NOT GUESS. DO NOT MAKE UNVERIFIABLE CLAIMS.
