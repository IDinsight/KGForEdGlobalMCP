# Prompts

The server registers nine deterministic prompt workflows. A prompt resolves accepted
package/profile context, applies rights and attribution rules, merges optional
framework-local guidance, and returns instructions for the connected MCP host model.

The server does not execute the generated educational or comparative content itself.

For workflow guidance, see [Use prompt workflows](../guides/prompts.md).

## Common prompt behavior

All prompts are registered at prompt version `1.4.0`.

Version 1.4.0 adds an **EVIDENCE ACCESS** section to the seven single-framework
teaching, study and progression workflows. It tells the client
to read each relied-on resource natively when it can, or otherwise with
[`read_evidence`](access-tools.md#read_evidence), replaying `page.nextRequest` until the
record is complete; to use at most 32 evidence windows per workflow (several windows of
one record count as one record toward every record cap); and to disclose and defer a
claim whose original provenance stays incomplete, denied or oversized. The same seven
workflows also render an **EVIDENCE LINKS** block: exact manifest, interpretation-profile, validation, unresolved and LP
summary URIs for the pinned snapshot, plus per-record patterns with a `{nodeId}`
placeholder for standards, standard provenance, a standard's learning components,
learning components and their provenance. Progression links are taken from tool results.
`administrator_alignment_review` and `cross_framework_comparison` do not include these
two sections.

The same seven workflows can be rendered through the
[`get_workflow_instructions`](access-tools.md#get_workflow_instructions) tool for clients
that do not offer native prompts; for identical arguments the message is identical.

Version 1.4.0 keeps the lean form introduced in 1.3.0:

- the embedded `ACCEPTED PACKAGE CONTEXT` is compact JSON holding only the profile
  facts a workflow reads: code-search policy, grade and stage mappings, hierarchy,
  known anomalies, language policy, subjects, source metadata, source-role
  capabilities, and statement types. Package identity, rights, required disclosures,
  and prompt-configuration identity appear once in their own sections, resource URIs
  arrive as links on the mandated tool results, and the interpretation-profile resource
  holds the complete profile; empty values are omitted;
- every tool request template is one compact line in the exact shape the tool schema
  accepts (`{"request": {...}}` for the request-wrapped tools; flat fields for
  `compare_framework_evidence`);
- multi-framework prompts render the generic soft guidance once, in a `SHARED
  GUIDANCE` section, and each framework section carries only what its configuration
  adds to or replaces in a named block; and
- guidance slots that share a label are merged under one heading.


A successful prompt returns one user-role prompt message plus metadata. Single-framework
metadata includes:

- `framework_id`;
- `snapshot_id`;
- `graphPackageId`;
- `profileId` and `profileVersion`;
- prompt configuration identity when configured;
- `promptVersion`;
- `generatedContent: true`; and
- `epistemicStatus: llm_inferred`.

Multi-framework prompts return a `contexts` array with package-local source metadata,
rights, attribution, profile identity, and prompt-configuration evidence for every
selected package.

Optional blank prompt arguments are normalized to their endpoint defaults at the MCP
adapter boundary.

## Shared argument types

### Focus mode

```text
topic
statement_code
node_id
case_identifier_uuid
case_identifier_uri
```

`topic_or_standard` is limited to 512 characters and must contain non-whitespace text.

### Common optional text limits

| Argument              | Maximum length  |
|-----------------------|-----------------|
| `local_context`       | 4000 characters |
| `available_materials` | 2000 characters |
| `learner_context`     | 2000 characters |
| `grade_or_stage`      | 128 characters  |

`output_language`, when supplied, uses the server's validated language-tag type.

### Learning components in the single-framework prompts

`student_study_support`, `teacher_guide_draft`, and `student_handbook_section` end their
evidence workflow with a step that calls `get_learning_components_for_standard` for the
resolved standard. The host uses the returned components as the package's generated
decomposition of the standard instead of inferring sub-skills of its own, labels each
`[GENERATED-EVIDENCE / llm_inferred]` with its support confidence, and reports where a
component also supports a standard in another grade. A package with no learning
components gets a stop line instead of the call, and the prompt still renders.

`multigrade_lesson_plan` requires components and is described below.

## `student_study_support`

Required:

- `framework_id`
- `grade_or_stage`
- `topic_or_standard`

Optional:

| Argument          | Default / values                             |
|-------------------|----------------------------------------------|
| `difficulty`      | `on_level`; also `foundational`, `extension` |
| `focus_mode`      | `topic`                                      |
| `local_context`   | null                                         |
| `output_language` | null                                         |
| `practice_count`  | 5; range 1-10                                |
| `snapshot_id`     | null; unique-current routing                 |

Example prompt arguments:

```json
{
  "framework_id": "ghana-nacca-primary-english-language-basic-1-3",
  "grade_or_stage": "BASIC 1",
  "topic_or_standard": "story structure",
  "focus_mode": "topic",
  "difficulty": "on_level",
  "practice_count": 5
}
```

## `teacher_guide_draft`

Required:

- `framework_id`
- `grade_or_stage`
- `topic_or_standard`

Optional:

| Argument                  | Default / bound           |
|---------------------------|---------------------------|
| `available_materials`     | null; max 2000 characters |
| `focus_mode`              | `topic`                   |
| `learner_context`         | null; max 2000 characters |
| `lesson_duration_minutes` | 45; range 10-240          |
| `local_context`           | null                      |
| `output_language`         | null                      |
| `snapshot_id`             | null                      |

## `student_handbook_section`

Required:

- `framework_id`
- `grade_or_stage`
- `topic_or_standard`

Optional:

| Argument            | Default / bound     |
|---------------------|---------------------|
| `focus_mode`        | `topic`             |
| `local_context`     | null                |
| `output_language`   | null                |
| `snapshot_id`       | null                |
| `target_word_count` | 500; range 150-1500 |

## `multigrade_lesson_plan`

!!! warning "Experimental, and it requires learning components"
    This workflow has no source-only fallback. A package containing no learning
    components is refused with `capability_unavailable` rather than degraded into
    parallel mono-grade plans under a multi-grade heading.

Plans one lesson for a classroom holding several grades at once. It separates the shared
teach-together core from grade-specific work by reading which learning components the
standards of each grade decompose to: a component supporting standards in more than one
of the requested grades is the candidate shared core; a component supporting only one is
that grade's differentiated work.

Required:

- `framework_id`
- `grades_in_room` — 2 to 8 distinct grades, as a JSON array such as `["4", "5", "6"]`
- `topic_or_standard`

Optional:

| Argument                  | Default / bound           |
|---------------------------|---------------------------|
| `focus_mode`              | `topic`                   |
| `learner_context`         | null; max 2000 characters |
| `lesson_duration_minutes` | 45; range 10-240          |
| `local_context`           | null                      |
| `output_language`         | null                      |
| `snapshot_id`             | null                      |

The rendered workflow instructs the host to resolve each grade's standards, call
`get_learning_components_for_standard` for each, and compare `supportedStandards` across
grades. It requires the result to state that a shared core rests on a model's judgement
that two standards decompose to the same component, **not** on a curriculum-authored
equivalence between those grades.

## `learning_progression_teaching_sequence`

Required: `framework_id`, `topic_or_standard` (1–512 characters).

| Optional argument                         | Default / bound                                                                          |
|-------------------------------------------|------------------------------------------------------------------------------------------|
| `focus_mode`                              | `topic`; also `statement_code`, `node_id`, `case_identifier_uuid`, `case_identifier_uri` |
| `local_grade_labels`, `normalized_grades` | Empty JSON arrays; up to 32 unique profile-valid values each                             |
| `snapshot_id`                             | null; pins unique-current once                                                           |
| `local_context`                           | null; at most 4,000 characters                                                           |
| `output_language`                         | null; optional language tag                                                              |

The client resolves a topic/code through the first search page of 10, or an exact node/CASE selector through `get_standard`, retaining at most three standards. It reads direct links with three calls per retained standard, one per connection kind in the order `outgoing_builds`, `incoming_builds`, `related` (at most nine calls). Each call reads one page of up to 25 links (fewer if the result reaches the size limit); a remaining `nextCursor` means that kind has more links than were read, and the client reports it. It then reads downstream builds (depth 8/nodes 30/edges 40) and, only for two explicitly selected retained standards, connecting paths (depth 6/paths 3). It retains at most five supporting LCs per standard. The result is an adaptable cited sequence, separating stored builds, nonsequential relates links and generated activities/ordering choices.

## `learning_progression_support_plan`

Required: `framework_id`, `identifier` (a JSON-object prompt argument selecting exact `node_id`, `case_identifier_uuid` or `case_identifier_uri`; selector text at most 512 characters). Code selection is not accepted by this prompt; resolve a code using search first.

Optional: `snapshot_id`, `local_context` (at most 4,000 characters), `output_language`, all null by default.

The client reads the target standard, then incoming builds and related links in two separate calls. Each call reads one page of up to 25 links (fewer if the result reaches the size limit) and does not follow `nextCursor`; a remaining cursor means that kind has more links than were read, and the client reports it. It also reads upstream builds (depth 3/nodes 20/edges 30), and LCs for the target plus at most three supporting standards (five LCs per standard retained). It proposes cited review/practice options and alternative next steps. Observations are caller reports; suggestions are generated pedagogy, not a mastery diagnosis or compulsory prerequisite.

## `learning_progression_curriculum_review`

Required: `framework_id`.

| Optional argument                               | Default / bound                                                                    |
|-------------------------------------------------|------------------------------------------------------------------------------------|
| `standard_identifiers`                          | Empty JSON array; at most 20 unique exact node/CASE/profile-enabled code selectors |
| `local_grade_labels`, `normalized_grades`       | Empty JSON arrays; at most 32 unique profile-valid values each                     |
| `statement_types`, `normalized_statement_types` | Empty JSON arrays; at most 32 unique profile-valid values each                     |
| `endpoint_scope`                                | `either`; also `both`, `source`, `target`                                          |
| `relationship_types`                            | Empty JSON array (both types); or `["buildsTowards"]`, `["relatesTo"]`, both; unique |
| `snapshot_id`, `output_language`                | null                                                                               |
| `local_context`                                 | null; at most 4,000 characters                                                     |

The workflow reads LP summary/statistics, then runs one discovery scan per selected relationship type in the fixed order `buildsTowards`, `relatesTo`. Each scan sets `relationshipTypes` to its single type, keeps the same exact selectors and endpoint filters, and may read up to three pages, so one type never uses up the other's pages. Each page holds up to 25 links (fewer if the result reaches the size limit), and the client records each page's actual count and cursor. A cursor left after a scan's third page means that type's review is incomplete. The client fully inspects at most ten selected exact relationships/provenance records in total (up to five per type when both types return links; unused slots go to the other type) and reads retained validation/unresolved evidence within policy. Package totals, filtered counts and the bounded reviewed subset are reported separately for each type and never added across types. The output contains coverage/warning/review questions, without asserting curriculum omission, pedagogical certification or cross-framework edges.

### Shared stored-progression workflow contract

MCP prompt names/arguments use snake_case. Complex values are JSON-array/object strings; for example `local_grade_labels` is `["PRIMARY ONE"]`, and `identifier` is `{"identifierType":"node_id","nodeId":"<actual-node-id>"}`. Do not enter comma-separated prose. Every workflow pins one exact snapshot, checks derivative rights, and renders deterministic client retrieval instructions; prompt retrieval itself runs neither evidence queries nor a model. Through `get_workflow_instructions` the same arguments use camelCase names and plain JSON arrays/objects.

All three retain source standards, generated LCs, stored generated edges and new pedagogy as separate tiers. Full provenance for used relationships is capped at ten resources, and evidence reading at 32 windows: reduce/defer cited recommendations if more evidence is needed. Keep bounds, warnings, coverage, unavailable/empty/partial results and denied-resource outcomes visible. Missing edges never invoke a hypothesis fallback. See [workflow examples](../guides/progression.md).

The existing `teacher_guide_draft`, `student_study_support`, `student_handbook_section` and `multigrade_lesson_plan` prompts also retrieve optional stored LP evidence: at most three standards, three one-page calls per standard (one per connection kind, at most nine; up to 25 links each), full provenance for at most ten used edges, plus LCs. They preserve useful output when LP is unavailable or sparse. A shared LC supplies generated support evidence, not a new LP or cross-grade equivalence edge.

## `administrator_alignment_review`

Required:

- `source_framework_id`
- `target_framework_id`
- `topic_or_query`

Optional:

| Argument                | Default / bound                          |
|-------------------------|------------------------------------------|
| `include_context_paths` | true                                     |
| `local_context`         | null                                     |
| `matches_per_framework` | 5; range 1-10                            |
| `output_language`       | null                                     |
| `search_mode`           | `text`; also `code_exact`, `code_prefix` |
| `source_grade_or_stage` | null                                     |
| `source_snapshot_id`    | null                                     |
| `target_grade_or_stage` | null                                     |
| `target_snapshot_id`    | null                                     |

The rendered workflow directs the host to use `compare_framework_evidence`. Retrieved
similarity remains candidate evidence, not an accepted alignment. Learning components
may appear in the comparison matrix as `[GENERATED-EVIDENCE / llm_inferred]` rows beside
source-asserted rows, under the shared generated-evidence disclosure, so
the human reviewer sees the tier next to each claim.

## `cross_framework_comparison`

Required:

- `framework_ids`: 2-8 distinct framework IDs
- `topic_or_query`

Optional:

| Argument                | Default / bound                           |
|-------------------------|-------------------------------------------|
| `include_context_paths` | true                                      |
| `local_context`         | null                                      |
| `local_grade_labels`    | empty; JSON-array prompt argument, max 64 |
| `matches_per_framework` | 5; range 1-10                             |
| `normalized_grades`     | empty; JSON-array prompt argument, max 64 |
| `output_language`       | null                                      |
| `search_mode`           | `text`; also `code_exact`, `code_prefix`  |
| `snapshot_ids`          | empty; JSON-array prompt argument, max 8  |

`framework_ids`, `snapshot_ids`, and grade-filter collections use JSON-array prompt input.
For example:

```text
["framework-a", "framework-b"]
```

Snapshot IDs are optional, with at most one selected snapshot per framework. Omission
uses unique-current routing.

Learning components may be compared across frameworks through
`search_learning_components`. The output contract requires a grain disclosure: components
from different frameworks were generated independently, possibly under different
decomposition instructions, dedup scopes, and pipeline versions, so similar wording does
not indicate comparable grain.

## Framework-local prompt overlays

A selected package may have an optional versioned prompt configuration. The overlay can
append to or replace designated soft-guidance sections, but it cannot override hard
server rules for:

- rights and attribution;
- evidence status;
- identifier namespaces;
- package isolation;
- tool/resource contracts; or
- required disclosures.

Prompt results expose whether an overlay was configured and include its ID, version, and
SHA-256 when present.

## Prompt access and errors

Generated-derivative workflows are subject to package rights policy. Expected prompt
errors include:

| Error code                   | Meaning                                                |
|------------------------------|--------------------------------------------------------|
| `prompt_access_denied`       | Rights policy blocks the generated-derivative workflow |
| `prompt_configuration_error` | Optional framework prompt configuration is invalid     |
| `prompt_rendering_error`     | Deterministic prompt rendering cannot complete safely  |
| `framework_not_found`        | Selected framework/snapshot is unavailable             |

Unexpected prompt failures are masked as:

```text
internal_error: The server could not render the prompt.
```

!!! note "Prompt metadata describes generated content"
    `epistemicStatus: llm_inferred` is attached to the prompt result metadata because the
    workflow is intended to produce model-generated content. It does not reclassify the
    underlying curriculum source evidence returned by tools and resources.

---

**Next:** [Errors, cursors, and limits](protocol-behavior.md)
