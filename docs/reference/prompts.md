# Prompts

The server registers six deterministic prompt workflows. A prompt resolves accepted
package/profile context, applies rights and attribution rules, merges optional
framework-local guidance, and returns instructions for the connected MCP host model.

The server does not execute the generated educational or comparative content itself.

For workflow guidance, see [Use prompt workflows](../guides/prompts.md).

## Common prompt behavior

All prompts are registered at prompt version `1.1.0`.

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

## `inferred_progression_hypothesis`

Required:

- `framework_id`
- `topic_or_standard`
- at least one local or normalized grade scope must be provided for the evidence
  workflow to succeed

Optional:

| Argument             | Default / values                                    |
|----------------------|-----------------------------------------------------|
| `candidate_limit`    | 8; range 2-20                                       |
| `direction`          | `both`; also `earlier_to_later`, `later_to_earlier` |
| `focus_mode`         | `topic`                                             |
| `local_context`      | null                                                |
| `local_grade_labels` | empty; JSON-array prompt argument, max 32           |
| `normalized_grades`  | empty; JSON-array prompt argument, max 32           |
| `output_language`    | null                                                |
| `snapshot_id`        | null                                                |

Complex collection arguments are entered by MCP prompt clients as JSON-array strings,
for example:

```text
["BASIC 1", "BASIC 2", "BASIC 3"]
```

Do not enter comma-separated prose in place of the JSON array.

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
similarity remains candidate evidence, not an accepted alignment.

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
