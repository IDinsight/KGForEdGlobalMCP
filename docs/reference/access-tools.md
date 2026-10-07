# Evidence and workflow access tools

Two read-only tools give clients that work only through tools the same evidence and
workflow instructions that native MCP resources and prompts provide. They reuse the
existing resource and prompt services: rights, size limits, exact package identity and
rendered wording are the same on every route. Neither tool runs a model, follows links
on the caller's behalf, or creates relationships.

Use native resource reads and the native prompt picker when your client offers them.
Use these tools when it does not, when a returned link cannot be opened from the
client's attachment menu, or when you deliberately work through tool calls only.

## `read_evidence`

Reads the full permitted content of one `kgfegmcp://` resource in bounded UTF-8 windows.

| Field             | Type                 | Default | Notes                                                                      |
|-------------------|----------------------|---------|----------------------------------------------------------------------------|
| `uri`             | string, 1–4,096      | —       | `kgfegmcp://catalog` or a URI from one of the 14 templates                 |
| `maxContentBytes` | integer, 1–32,768    | 16,384  | Upper bound for this window; a window can be smaller to fit result limits  |
| `cursor`          | string, 1–4,096      | null    | Only a `page.nextCursor` value returned by this tool for the same request  |

```json
{"request":{"uri":"kgfegmcp://framework/nigeria-nerdc-mathematics-primary-1-3/snapshot/nigeria-nerdc-mathematics-primary-1-3%40undated%2Bbc5e769ed26f/relationship/0129f5d5-42fd-52cb-bcf2-ec07c47103e7/provenance"}}
```

### Where URIs come from

Copy URIs unchanged from tool results: progression results carry `standardUri`,
`relationshipUri`, `provenanceUri`, `manifestUri`, `summaryUri`, `validationUri`,
`unresolvedUri` and artifact URIs. The seven workflows in
[`get_workflow_instructions`](#get_workflow_instructions) also render an **EVIDENCE
LINKS** block with exact manifest, interpretation-profile, validation, unresolved and LP
summary URIs for the pinned snapshot, plus per-record patterns for standards, standard
provenance, a standard's learning components, learning components and their provenance.
Replace `{nodeId}` in a pattern with an exact outer node ID or learning-component ID from
a tool result; returned UUIDs need no further encoding. An unreplaced `{nodeId}` fails.

The tool accepts only exact resource addresses. Queries, fragments, ports, user
information, empty or extra path segments, encoded separators, dot segments and double
encoding are rejected with `invalid_evidence_uri`. A percent-encoded spelling of a valid
URI is accepted and returned in its canonical form in `metadata.canonicalUri`.

### Result

| Field           | Meaning                                                                                       |
|-----------------|-----------------------------------------------------------------------------------------------|
| `metadata`      | The native resource metadata: canonical URI, resource kind, representation, exact package/profile/snapshot identity, source-artifact hashes, whole-resource `contentSha256` and `byteLength` |
| `content`       | This window's text, decoded from the original UTF-8 bytes                                     |
| `contentStatus` | `full` only when this window is the whole resource; otherwise `partial`, including the last window of a multi-window read |
| `page`          | `startByte`, `endByteExclusive`, `returnedBytes`, `totalBytes`, `maxContentBytes`, `isComplete`, `nextCursor`, `nextRequest`, `chunkSha256` and the result `limits` |
| `evidenceNotice`| How to continue and join windows                                                              |

To read a whole record, call again with `page.nextRequest` unchanged until
`page.isComplete` is `true`, then join the `content` windows in order. The joined bytes
reproduce `metadata.contentSha256`. Byte offsets count the original resource bytes;
`chunkSha256` covers only the returned window. Windows always end on a Unicode character
boundary.

Cursors are opaque and bound to the canonical URI, the resource content hash, its
metadata identity, `maxContentBytes` and the next byte position. An edited, stale or
mismatched cursor fails with `invalid_cursor`. Paging does not raise native limits: every
call reapplies rights, exposure class, source-read and return-size checks, and a resource
that is denied natively is denied here too.

Measured on the current Nigeria snapshot with the default window: the diagnostic
relationship provenance (12,275 bytes) and the target standard's provenance arrive in one
window; the manifest (22,348 bytes) needs two; Ghana Mathematics' dedicated unresolved
record (42,831 bytes) needs three.

## `get_workflow_instructions`

Returns the complete rendered instructions of one native prompt workflow as a tool
result. `request.workflowName` selects one of seven workflows:

| `workflowName`                           | Same arguments as native prompt                          |
|------------------------------------------|----------------------------------------------------------|
| `learning_progression_teaching_sequence` | [`learning_progression_teaching_sequence`](prompts.md#learning_progression_teaching_sequence) |
| `learning_progression_support_plan`      | [`learning_progression_support_plan`](prompts.md#learning_progression_support_plan)           |
| `learning_progression_curriculum_review` | [`learning_progression_curriculum_review`](prompts.md#learning_progression_curriculum_review) |
| `teacher_guide_draft`                    | [`teacher_guide_draft`](prompts.md#teacher_guide_draft)                                       |
| `student_study_support`                  | [`student_study_support`](prompts.md#student_study_support)                                   |
| `student_handbook_section`               | [`student_handbook_section`](prompts.md#student_handbook_section)                             |
| `multigrade_lesson_plan`                 | [`multigrade_lesson_plan`](prompts.md#multigrade_lesson_plan)                                 |

The other request fields are that prompt's arguments in camelCase (`framework_id` becomes
`frameworkId`), with the same defaults and limits. Unlike native prompt arguments, arrays
and selector objects are sent as JSON values, not JSON strings:

```json
{"request":{"workflowName":"learning_progression_support_plan","frameworkId":"nigeria-nerdc-mathematics-primary-1-3","snapshotId":"nigeria-nerdc-mathematics-primary-1-3@undated+bc5e769ed26f","identifier":{"identifierType":"node_id","nodeId":"e399b510-48bb-58ee-abda-61460a5a853b"},"localContext":"Learners explain the whole but confuse equal-sized parts.","outputLanguage":"en"}}
```

Unknown workflow names, extra fields and invalid values fail validation.
`administrator_alignment_review` and `cross_framework_comparison` remain native prompts
only.

The result contains `rendered` (the same prompt render result as the native prompt,
including the full `message`, prompt version and prompt-configuration identity),
`effectiveRequest` (the validated request with defaults filled in), the pinned `package`
reference, `profileSha256`, `manifestSha256` and an `instructionsNotice`. For identical
validated arguments and the same snapshot, `rendered.message` is identical to the native
prompt message.

The tool only renders instructions. The client then makes the listed tool calls, reads
evidence, and composes the cited answer. If the complete instructions cannot fit the
result limits, the call fails with `workflow_instructions_too_large`; instructions are
never clipped or continued with a cursor.

## Output and limits

Both tools return the complete result as one canonical JSON text block (sorted keys,
compact separators, Unicode preserved) plus the same object as `structuredContent`.
Parsing the text yields exactly the structured result, so a client that reads only text
loses nothing. The whole emitted result, text and structured copy together, must fit in
1,048,576 UTF-8 bytes and 100,000 characters.

## Errors

| Error code                        | Meaning                                                                               |
|-----------------------------------|---------------------------------------------------------------------------------------|
| `invalid_evidence_uri`            | Not one exact supported `kgfegmcp://` address                                         |
| `resource_not_found`, `standard_not_found` | The addressed resource, record or artifact does not exist in that snapshot (native error codes are kept) |
| `resource_access_denied`          | Rights, exposure class or native size policy blocks the resource (for example bulk artifacts) |
| `unsupported_evidence_format`     | Authorized bytes are not UTF-8 text and cannot be paged                               |
| `evidence_result_too_large`       | Not even one character of content fits beside the metadata within result limits       |
| `invalid_cursor`                  | Cursor altered, stale or not for this request                                         |
| `framework_not_found`             | Framework or snapshot unavailable                                                     |
| `prompt_access_denied`, `prompt_configuration_error`, `prompt_rendering_error` | Same meaning as for the native prompt         |
| `workflow_instructions_too_large` | Complete instructions exceed result limits; use the native prompt or shorter caller context |

Error text never includes denied content or local file paths.

---

**Next:** [Resources and URI templates](resources.md)
