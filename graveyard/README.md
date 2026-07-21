# Curriculum Knowledge Graph MCP Server

## Comprehensive implementation plan

**Status:** Approved starting architecture for implementation  
**Primary runtime:** Python with the standalone `fastmcp` package  
**Initial client:** Claude Desktop over local STDIO  
**Initial graph type:** Academic Standards  
**Future graph types:** Learning Components, Learning Progressions, curriculum resources, assessments, and reviewed alignments

---

## 1. Purpose of this document

This README is the definitive starting point for implementing a general, multi-framework Model Context Protocol server over curriculum knowledge graphs.

It is intended to provide enough context for a coding assistant to work productively without requiring the complete upstream extraction pipeline, every runtime configuration, and every graph artifact to be pasted into each new conversation.

The implementation must remain general. Country-, curriculum-, organization-, language-, grade-, subject-, code-, and hierarchy-specific behavior must be supplied through versioned data and configuration rather than embedded in generic Python code.

### How a coding assistant should use this file

Before making changes, the coding assistant should:

1. Read this README completely.
2. Identify the current implementation phase and its acceptance criteria.
3. Inspect the existing repository before proposing structural changes.
4. Keep MCP transport code thin and put graph logic in ordinary domain services.
5. Add or update tests with every behavioral change.
6. Avoid hardcoding facts from the six current curriculum packages.
7. Preserve source graph topology, including valid multi-parent DAGs and explicit unresolved-edge statuses.
8. Distinguish source facts, deterministic derivations, retrieval candidates, LLM inferences, and reviewed mappings.
9. Avoid introducing a server-side LLM. Claude Desktop is the reasoning and generation layer for the initial implementation.
10. Update this README or an ADR when a foundational decision changes.

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
- administrators inspect official frameworks, compare local standards to source frameworks, and review evidence-based alignment candidates;
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
academic_standards_kg_bundle.json
standards_framework.json
standards_framework_items.jsonl
relationships_has_child.jsonl
entity_provenance.json
unresolved_items.json
validation_report.json
```

These artifacts preserve local terminology, local grades, source evidence, merge history, relationship evidence, audit flags, unresolved decisions, deterministic identities, and complete accepted topology.

### 5.2 Slim Learning Commons-shaped delivery artifacts

```text
nodes.jsonl
relationships.jsonl
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

## 6. Current prototype and why it must change

The current prototype has one low-level MCP tool, `find_standard_statement`. It loads converted combined JSON files into memory and supports code-prefix or simple stemmed keyword search.

Important limitations include:

- it uses the low-level Python MCP server instead of standalone FastMCP;
- it expects a custom combined export rather than native `nodes.jsonl` and `relationships.jsonl` packages;
- its registry is keyed only by jurisdiction, so multiple frameworks in one jurisdiction overwrite each other;
- it assumes a single graph per jurisdiction and effectively a single subject;
- it keeps only child indexes and does not expose all parent paths;
- it is not safe for multi-parent DAGs;
- code and keyword modes are implicit and code silently wins when both are supplied;
- keyword matching is unranked OR matching;
- results are capped without pagination;
- subject values are hardcoded;
- grade normalization contains country-specific heuristics;
- resources and prompts are not exposed;
- rich detailed artifacts are unavailable;
- there is no framework snapshot identity, capability model, or alignment layer.

The new system should preserve the existing tool temporarily as a compatibility wrapper, but the canonical API should become framework-oriented and explicit.

### Existing implementation files to inspect during migration

The current implementation should be treated as migration input rather than discarded without review:

```text
server.py
    Low-level MCP STDIO adapter and current public compatibility contract.

kg.py
    Current in-memory graph registry, grade handling, code search, keyword search,
    result shaping, and several assumptions that must be removed.

convert_bundle.py
    Compatibility converter from the earlier report-shaped bundle to a combined
    graph export. It should become unnecessary for native JSONL packages, but may
    remain as a legacy import utility until all workflows are migrated.

create_kgs.py
    Upstream ten-stage pipeline entry point. The MCP server should consume its
    validated outputs and should not duplicate its semantic extraction logic.

sfi_export.py
    Authoritative final compiler and validator for detailed artifacts and the slim
    Learning Commons-shaped JSONL delivery files.

as_kg_instructions.md
    Architectural source of truth for upstream semantic ownership, topology
    preservation, validation, and artifact tiers.

run_config_schemas.py and curriculum runtime configs
    Source material for deriving smaller MCP curriculum interpretation profiles.
```

Recommended migration treatment:

- analyze the provided input files to understand the current state of the mcp server and its behavior;
- move reusable search and graph logic out of `kg.py` into domain services;
- replace the combined-export loader with the native package loader;
- remove `convert_bundle.py` since it is a legacy adapter;
- do not import upstream extraction modules into the runtime MCP process unless a
  narrowly defined shared schema package is intentionally created.

---

## 7. Current curriculum packages as validation fixtures

The current six complete packages are examples and regression fixtures, not the universe of supported curricula.

| Framework | Items | Relationships | Coded items | Notable topology or status |
|---|---:|---:|---:|---|
| Ghana English, Basic 1-3 | 430 | 430 | 319 | Tree; 2 unresolved-root fallback edges |
| Ghana Mathematics, Basic 4-6 | 302 | 302 | 254 | Tree; 13 unresolved-root fallback edges |
| Nigeria Mathematics, Primary 1-3 | 242 | 242 | 0 | Tree; entirely uncoded |
| Tamil Nadu Mathematics, Classes 1-5 | 255 | 255 | 35 | Tree; partially coded |
| India Science | 874 | 1,109 | 831 | Valid multi-parent DAG; 235 items have two parents |
| Rwanda Mathematics, Primary 1-3 | 626 | 626 | 0 | Tree; entirely uncoded |
| **Total** | **2,729** | **2,964** | **1,439** | Six complete graph packages |

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

The MCP protocol remains the compatibility contract. Another implementation using `rmcp`, TypeScript, or a low-level SDK can still expose an equivalent MCP interface.

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

Do not write LLM-generated cross-country relationships into source `nodes.jsonl` or `relationships.jsonl`.

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

The following structure is recommended. Exact names can adapt to the existing repository, but separation of responsibilities should remain.

```text
KGForAllMCP/
├── README.md
├── pyproject.toml
├── fastmcp.json
├── src/
│   └── kgfamcp/
│       ├── __init__.py
│       ├── app.py
│       ├── bootstrap.py
│       ├── settings.py
│       ├── errors.py
│       ├── logging_.py
│       │
│       ├── domain/
│       │   ├── models.py
│       │   ├── enums.py
│       │   ├── identifiers.py
│       │   ├── results.py
│       │   └── protocols.py
│       │
│       ├── packages/
│       │   ├── models.py
│       │   ├── loader.py
│       │   ├── validator.py
│       │   ├── checksums.py
│       │   └── import_legacy.py
│       │
│       ├── profiles/
│       │   ├── models.py
│       │   ├── loader.py
│       │   └── validator.py
│       │
│       ├── catalog/
│       │   ├── models.py
│       │   ├── repository.py
│       │   ├── service.py
│       │   └── filters.py
│       │
│       ├── graph/
│       │   ├── models.py
│       │   ├── loader.py
│       │   ├── store.py
│       │   ├── traversal.py
│       │   └── validation.py
│       │
│       ├── search/
│       │   ├── models.py
│       │   ├── normalizers.py
│       │   ├── lexical.py
│       │   ├── code.py
│       │   ├── service.py
│       │   └── semantic.py       # optional, later
│       │
│       ├── resources/
│       │   ├── repository.py
│       │   ├── uri.py
│       │   └── policy.py
│       │
│       ├── alignments/
│       │   ├── models.py
│       │   ├── repository.py
│       │   └── service.py
│       │
│       ├── services/
│       │   ├── frameworks.py
│       │   ├── standards.py
│       │   ├── statistics.py
│       │   ├── comparison.py
│       │   └── capabilities.py
│       │
│       ├── mcp/
│       │   ├── register.py
│       │   ├── tools/
│       │   │   ├── frameworks.py
│       │   │   ├── standards.py
│       │   │   ├── context.py
│       │   │   ├── statistics.py
│       │   │   ├── comparison.py
│       │   │   └── compatibility.py
│       │   ├── resources/
│       │   │   ├── catalog.py
│       │   │   ├── framework.py
│       │   │   ├── artifacts.py
│       │   │   └── provenance.py
│       │   └── prompts/
│       │       ├── student.py
│       │       ├── teacher.py
│       │       ├── administrator.py
│       │       ├── comparison.py
│       │       └── progression.py
│       │
│       └── cli/
│           ├── validate_packages.py
│           ├── build_catalog.py
│           └── inspect_package.py
│
├── config/
│   ├── server.json
│   ├── catalog.json
│   └── profiles/
│       └── <profile-id>/
│           ├── profile.json
│           ├── interpretation.md
│           └── prompt_fragments/
│
├── data/
│   ├── graph_packages/
│   │   └── <framework-id>/
│   │       └── <snapshot-id>/
│   │           ├── manifest.json
│   │           ├── delivery/
│   │           │   ├── nodes.jsonl
│   │           │   └── relationships.jsonl
│   │           └── detailed/
│   │               ├── academic_standards_kg_bundle.json
│   │               ├── standards_framework.json
│   │               ├── standards_framework_items.jsonl
│   │               ├── relationships_has_child.jsonl
│   │               ├── entity_provenance.json
│   │               ├── unresolved_items.json
│   │               └── validation_report.json
│   └── derived/
│       ├── alignments/
│       └── progressions/
│
└── tests/
    ├── unit/
    ├── integration/
    ├── contract/
    ├── fixtures/
    └── smoke/
```

### Explicit registration versus FileSystemProvider

Start with explicit registration in `mcp/register.py` so the public MCP surface is obvious and startup failures are strict.

FastMCP's provider and filesystem discovery features can be introduced later if the component count becomes difficult to manage. Automatic discovery is convenient, but explicit assembly is easier to audit during the first implementation.

---

## 12. Identity and versioning model

The implementation must distinguish several identifiers.

### `framework_id`

Stable identity for the conceptual framework across snapshots.

Example:

```text
ghana-nacca-primary-english-basic-1-3
```

This value should be explicit in a manifest rather than derived at runtime from display text.

### `snapshot_id`

Immutable identity for one exported version of the framework.

Recommended structure:

```text
<framework-id>@<declared-version-or-date>+<short-content-hash>
```

When an official version is unavailable, use a stable extraction date or source fingerprint plus the package hash.

### `graph_package_id`

A globally unique identifier for a package. It can equal `snapshot_id` initially, but the schema should keep the concept explicit in case one snapshot later contains several graph types.

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

Every package must have a manifest validated by Pydantic.

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
  "graphPackageId": "ghana-nacca-primary-english-basic-1-3@2019+abc123",
  "frameworkId": "ghana-nacca-primary-english-basic-1-3",
  "snapshotId": "ghana-nacca-primary-english-basic-1-3@2019+abc123",
  "graphType": "academic_standards",
  "includedGraphTypes": ["academic_standards"],
  "framework": {
    "name": "English Language Curriculum for Primary Schools (Basic 1 - 3)",
    "jurisdiction": "Ghana",
    "jurisdictionType": "country",
    "issuingAuthority": "National Council for Curriculum and Assessment",
    "provider": "IDinsight",
    "localSubject": "English Language",
    "normalizedSubjects": ["English Language Arts"],
    "languages": ["en"],
    "localGradesOrStages": ["Basic 1", "Basic 2", "Basic 3"],
    "normalizedGrades": ["1", "2", "3"],
    "adoptionStatus": "Adopted",
    "isCurrent": true,
    "sourceVersion": "2019"
  },
  "artifacts": {
    "nodes": "delivery/nodes.jsonl",
    "relationships": "delivery/relationships.jsonl",
    "bundle": "detailed/academic_standards_kg_bundle.json",
    "validationReport": "detailed/validation_report.json",
    "entityProvenance": "detailed/entity_provenance.json",
    "unresolvedItems": "detailed/unresolved_items.json"
  },
  "checksums": {
    "delivery/nodes.jsonl": "sha256:...",
    "delivery/relationships.jsonl": "sha256:..."
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
    "license": "Unknown",
    "attributionStatement": "...",
    "reviewStatus": "review_required",
    "allowFullText": true,
    "allowBulkResource": false,
    "allowGeneratedDerivatives": "review_required"
  },
  "profile": {
    "profileId": "ghana-primary-english",
    "profileVersion": "1.0",
    "path": "../../../../config/profiles/ghana-primary-english/profile.json",
    "sha256": "..."
  },
  "validation": {
    "status": "passed",
    "validatedAt": "2026-07-20T00:00:00Z"
  }
}
```

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

The loader should maintain both:

```text
raw property dictionary
normalized typed view
```

Unknown source properties should be preserved in an `extensions` or `raw_properties` field rather than discarded.

### 15.5 Learning Commons-shaped boundary adapter

The delivery JSONL format has wire conventions that should be decoded in one adapter
layer rather than throughout the services.

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

Boundary rules:

- values inside `properties` are string-encoded in the slim wire format;
- `isCurrent` must be decoded from `"true"` or `"false"`;
- `gradeLevel` must be decoded from a JSON array encoded inside a string;
- optional null properties may be omitted;
- outer endpoint fields remain snake_case;
- property names are camelCase;
- `identifier` and `caseIdentifierUUID` must remain distinct concepts;
- relationship endpoints should be validated through both the outer identifiers and
  the declared property key/value fields;
- `resolutionStatus` must survive domain conversion;
- the domain layer should use semantic Python values while retaining the raw strings.

Only this adapter should know the wire-format encoding details.

---

## 16. Domain model

The domain layer must not depend on FastMCP.

Illustrative models:

```python
class FrameworkSnapshot(BaseModel):
    framework_id: str
    snapshot_id: str
    graph_package_id: str
    name: str
    jurisdiction: str
    jurisdiction_type: str | None
    issuing_authority: str | None
    local_subject: str | None
    normalized_subjects: list[str]
    languages: list[str]
    local_grades_or_stages: list[str]
    normalized_grades: list[str]
    capabilities: FrameworkCapabilities
    rights: RightsPolicy
    profile_ref: ProfileRef


class StandardNode(BaseModel):
    node_id: str
    framework_id: str
    snapshot_id: str
    case_identifier_uuid: str | None
    case_identifier_uri: str | None
    description: str
    statement_code: str | None
    alternate_statement_code: str | None
    statement_type: str | None
    normalized_statement_type: str | None
    local_subject: str | None
    normalized_subjects: list[str]
    local_grade_labels: list[str]
    normalized_grades: list[str]
    language: str | None
    raw_properties: dict[str, str]


class GraphRelationship(BaseModel):
    relationship_id: str
    framework_id: str
    snapshot_id: str
    relationship_type: str
    source_node_id: str
    target_node_id: str
    resolution_status: str | None
    raw_properties: dict[str, str]
```

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

The exact API must be verified against the pinned FastMCP version (version 3.4.4).

```python
from fastmcp import FastMCP
from fastmcp.server.lifespan import lifespan

from kgfamcp.bootstrap import build_app_state


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

Create typed exceptions:

```text
KGForAllMCPError
PackageValidationError
CatalogError
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

### 20.2 Public versus internal errors

Expected user-correctable errors should become `ToolError` with stable, actionable text.

Unexpected errors should:

- be logged with request ID and stack trace;
- return a generic masked message;
- never expose local paths, raw tracebacks, environment variables, or secrets.

### 20.3 Compatibility error wording

If exact compatibility with the existing Learning Commons-style tool is required, catch the domain error inside the FastMCP tool and raise `ToolError` with the exact public sentence.

Do not choose a low-level MCP server solely for error wording.

### 20.4 Protocol versus tool errors

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

### 21.9 Compatibility tool

Retain `find_standard_statement` behind a feature flag during migration.

It should delegate to the new services. It must not keep its own graph-loading or search implementation.

Deprecation policy:

1. preserve existing fixture behavior in Phase 2;
2. document the canonical replacement;
3. remove only after clients and tests no longer depend on it.

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
- concise serialized or human-readable text for compatibility and display.

---

## 23. MCP resources

Resources expose read-only authoritative or inspectable context.

### 23.1 URI scheme

Use a custom RFC 3986-compatible scheme:

```text
kgfamcp://
```

### 23.2 Recommended resources

```text
kgfamcp://catalog
kgfamcp://framework/{framework_id}
kgfamcp://framework/{framework_id}/snapshot/{snapshot_id}/manifest
kgfamcp://framework/{framework_id}/snapshot/{snapshot_id}/validation
kgfamcp://framework/{framework_id}/snapshot/{snapshot_id}/unresolved
kgfamcp://framework/{framework_id}/snapshot/{snapshot_id}/interpretation-profile
kgfamcp://framework/{framework_id}/snapshot/{snapshot_id}/pipeline-instructions
kgfamcp://framework/{framework_id}/snapshot/{snapshot_id}/artifact/{artifact_name}
kgfamcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}
kgfamcp://framework/{framework_id}/snapshot/{snapshot_id}/standard/{node_id}/provenance
kgfamcp://framework/{framework_id}/snapshot/{snapshot_id}/relationship/{relationship_id}
kgfamcp://alignment/{alignment_id}
```

### 23.3 Artifact allowlist

`artifact_name` must resolve through a strict allowlist from the package manifest. Never concatenate user input into a filesystem path.

### 23.4 Large resources

Raw `nodes.jsonl`, `relationships.jsonl`, and bundles may be large.

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

### 24.6 `inferred_progression_hypothesis`

Use when no Learning Progressions KG exists.

Required disclosure:

```text
This is an LLM-inferred likely progression based on standards text, grade context,
and curriculum-specific guidance. It is not a source-authored progression edge.
```

The prompt should ask Claude to provide evidence and counter-considerations rather than only a confidence score.

### 24.7 Curriculum profile use in prompts

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

Exact commands depend on the pinned FastMCP version (version 3.4.4), but the expected workflow is:

```bash
fastmcp inspect src/kgfamcp/app.py:mcp
fastmcp run src/kgfamcp/app.py:mcp --transport stdio
fastmcp install claude-desktop src/kgfamcp/app.py:mcp --with-editable .
```

A `fastmcp.json` file can centralize the entrypoint, dependency, and environment configuration.

### 30.3 Environment configuration

Use absolute paths or a project-root environment variable because Claude Desktop launches the process from its own environment.

Recommended variables:

```text
KG_FOR_ALL_MCP_CATALOG
KG_FOR_ALL_MCP_CONFIG
KG_FOR_ALL_MCP_DATA_ROOT
KG_FOR_ALL_MCP_ENABLE_COMPATIBILITY_TOOL
KG_FOR_ALL_MCP_INVALID_PACKAGE_POLICY
KG_FOR_ALL_MCP_LOG_LEVEL
```

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

### 32.3 OpenTelemetry

FastMCP has OpenTelemetry support. Keep it optional for local development and configure an exporter only in environments that require it.

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

### 34.1 Unit tests

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

### 34.2 Package fixture tests

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

### 34.3 Graph invariant tests

For every valid package:

- all endpoints exist;
- root exists;
- no `hasChild` cycles;
- expected reachability holds;
- multiple parents are not collapsed;
- unresolved statuses survive loading and output;
- node and relationship counts remain stable.

### 34.4 MCP contract tests

Use FastMCP's in-memory client to test the real protocol layer without subprocesses.

Test:

- tool listing;
- resource listing and reading;
- prompt listing and retrieval;
- structured output schemas;
- controlled errors;
- exact compatibility-tool errors where required;
- pagination;
- annotations;
- resource links.

### 34.5 STDIO tests

Add a smaller set of subprocess tests to ensure:

- startup works;
- no stdout log corruption occurs;
- environment variables are passed correctly;
- process exits cleanly.

### 34.6 Prompt snapshot tests

Prompts do not need an LLM test in the core suite. Snapshot their generated messages and assert required disclosures, resource references, and profile versions.

### 34.7 No-LLM deterministic CI

The complete core test suite must run without network access or an LLM API key.

---

## 35. Implementation phases

## Phase 0: freeze contracts and fixtures

### Deliverables

- this README committed;
- initial ADR files;
- package manifest Pydantic model;
- curriculum profile Pydantic model;
- result status vocabulary;
- fixture inventory and expected counts;
- tool input/output model drafts;
- public naming conventions.

### Exit criteria

- all six package identities can be represented;
- multiple Ghana frameworks coexist;
- India Science multi-parent topology is explicitly covered;
- unresolved fallbacks are represented;
- no current country name appears in generic model validators.

---

## Phase 1: package loader, validator, catalog, and graph domain

### Deliverables

- native Learning Commons-shaped JSONL loader;
- detailed-artifact path support;
- manifest loader;
- profile loader;
- package validator;
- DAG-aware graph store;
- catalog repository;
- CLI commands to validate and inspect packages;
- legacy-file packaging helper.

### Exit criteria

- all six complete packages load simultaneously;
- an incomplete package fails or quarantines according to policy;
- node and edge counts match fixtures;
- India Science returns all parents;
- Ghana fallback statuses remain visible;
- identifiers do not assume `identifier == caseIdentifierUUID`;
- codeless packages load without warnings that imply invalidity.

---

## Phase 2: FastMCP migration with behavior parity

### Deliverables

- standalone FastMCP app;
- lifespan-loaded application state;
- compatibility `find_standard_statement` tool;
- controlled `ToolError` behavior;
- structured outputs;
- in-memory MCP tests;
- STDIO smoke test;
- Claude Desktop development installation instructions.

### Exit criteria

- current compatibility fixtures pass;
- expected public errors are stable;
- unexpected errors are masked;
- no protocol output is polluted by logs;
- Claude Desktop can connect locally.

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

## Phase 6: deterministic cross-framework comparison evidence

### Deliverables

- `compare_framework_evidence`;
- comparison result schema;
- per-framework retrieval and context;
- comparison warnings;
- optional pluggable semantic retrieval interface;
- evaluation dataset of known comparison queries.

### Exit criteria

- a topic such as fractions can be retrieved across selected frameworks;
- all source statements and paths are visible;
- results are labeled retrieval candidates;
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

1. **PR 1:** domain identifiers, enums, errors, manifest model, profile model.
2. **PR 2:** JSONL parser and delivery-property boundary decoder.
3. **PR 3:** package validator and CLI.
4. **PR 4:** DAG-aware graph store and traversal tests.
5. **PR 5:** catalog repository and six-package fixture integration.
6. **PR 6:** lexical and code search service.
7. **PR 7:** FastMCP bootstrap, lifespan, error translation, compatibility tool.
8. **PR 8:** canonical framework and standards tools.
9. **PR 9:** resources and strict URI resolver.
10. **PR 10:** role-oriented prompts and snapshot tests.
11. **PR 11:** comparison evidence service.
12. **PR 12:** Claude Desktop packaging and smoke tests.
13. **Later PRs:** alignment overlay, Learning Components, Learning Progressions, remote hosting.

Each PR should leave the repository runnable and tested.

---

## 37. Migration of current files into packages

Create a one-time or reusable packaging CLI:

```bash
curriculum-mcp package create \
  --nodes nodes_ghana_english.jsonl \
  --relationships relationships_ghana_english.jsonl \
  --profile config/profiles/ghana-primary-english/profile.json \
  --output data/graph_packages/...
```

The CLI should:

1. parse the framework node;
2. request or derive a proposed framework ID;
3. require operator confirmation of identity and version fields;
4. copy or link delivery artifacts;
5. discover optional detailed artifacts;
6. compute checksums;
7. run validation;
8. write the manifest;
9. print counts and warnings;
10. never edit source JSONL content.

Do not derive final package identity solely from a filename.

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

---

## 39. Defaults for currently open implementation choices

These are defaults, not permanent constraints.

| Question | Default |
|---|---|
| Search backend | In-memory indexes plus SQLite FTS5 if available |
| Package invalidity | Fail startup in development and CI |
| Package reload | Restart server; no hot reload in production |
| Public API casing | Pythonic internal models; stable documented MCP field aliases |
| Compatibility tool | Enabled during migration, then feature-flagged |
| Semantic search | Interface only until lexical search is evaluated |
| Alignment persistence | Read-only and absent in initial milestone |
| Raw large resources | Disabled unless rights and size policy allow |
| Profile format | JSON for machine policy plus Markdown for interpretation |
| Logging | Structured stderr, no full prompt logging |
| Client generation | Claude Desktop only |

---

## 40. Definition of done for the first production milestone

The first production milestone is complete when:

1. standalone FastMCP runs through Claude Desktop over STDIO;
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
18. the compatibility tool is either passing its fixtures or intentionally disabled with migration documentation.

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

1. ask the user for clarification rather than guessing;
2. preserves source meaning and topology;
3. makes provenance and uncertainty visible;
4. keeps generic code curriculum-agnostic;
5. uses deterministic services before LLM inference;
6. leaves future graph types and storage backends open;
7. can be tested without Claude;
8. does not overstate educational authority.
