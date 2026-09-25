# Documenter Artifact Template

Use one record across collaboration modes, targets, corrections, and resumption.
Use the fixed path and collision rules in **Workflow Artifact Provenance** in
the protocol. No documentation-path state field, separate preferences file, or
acceptance ledger is needed. Prepend the exact active-cycle provenance:

```markdown
<!-- STANDARDS
Artifact: DOCUMENTATION
Cycle: <Active Work.Id>
-->
```

---

# Documentation Record

`Cycle`: `<Active Work.Id>` `Status`: `IN_PROGRESS | BLOCKED | COMPLETE`
`Collaboration`: `AUTONOMOUS | GUIDED` `Target`:
`FILE | FOLDER | VERTICAL_SLICE | ACTIVE_CHANGE` `Target Detail`:
`<repository-relative path, capability, or active cycle>` `User Style`:
`NONE | <direct-child identifier>`

## Assessed Inputs and Boundary

- Active contract/context and supporting implementation, verification, review,
  and documentation paths with assessed content identities.
- Baseline/comparison range and its basis; relevant committed, staged, unstaged,
  untracked, moved/deleted, and affected unchanged content.
- Relevant dependencies, configuration, generation sources, and environment
  assumptions. HEAD alone cannot identify dirty content.
- Editing boundary and exclusions, with remaining cycle work beyond the target.
- Applicable style files and identities; selection changes and affected work.
- Relevant workflow context; refer to state for recovery and obligations rather
  than copying its stack. Separate self-authored progress/coordination from
  deliverable input identities.

## Documentation Work and Evidence

For each required surface or coherent group, record:

- Audience, purpose, file/section, and documentation need.
- Current AC references and relevant design sections/technical criteria, or a
  reason no documentation impact exists. Account for the current inventory
  through references; do not copy acceptance wording or create new requirement
  identities. Retired IDs are history only.
- Actual behavior and owner evidence inspected; relevant earlier documentation
  dependencies under the same AC IDs.
- Saved outcome and content identity, or evidenced no-change disposition;
  distinguish pending, partially applied, and inspected complete work.
- Checks/evidence references supporting that outcome; pending work and owner.

This is documentation evidence, not certification of all cycle acceptance or
another owner's completion. Ordinary documents remain reusable project assets.

## Checks and Applicability

- Inspection performed, or exact command and working directory, assessed
  content, relevant environment, and actual result/exit status.
- What it establishes and its limits; distinguish unavailable, unrun, failed,
  interrupted, skipped, or inconclusive checks. Record errors or why an attempt
  was not permitted. Never record secrets or invented execution.
- Prior evidence retained with applicability justification; superseded evidence
  with the input change that invalidated it.

## Discrepancies, Dependencies, and Remaining Work

Use stable local references (for example `D-001`) for discrepancies, not new
acceptance IDs. Record `OPEN | RESOLVED | WITHDRAWN`, affected path/identity and
AC/criterion, concrete evidence and impact, owner/canonical failure type (or
`NONE` for installer/protocol ownership), required correction, and verified
resolution or withdrawal reason. Preserve all unresolved items before routing
one. Link Reviewer findings without changing their dispositions.

Include material gaps, required documentation outside the selected target,
owner/user dependencies, and non-blocking limits with reasons. Record `NONE`
when sufficient assessment establishes no remaining item. A review or
synchronization reassessment waiting for this correction is still that owner's
work; do not claim it passed.

## Resume and Conclusion

- Next concrete action and inputs to reconcile on resumption.
- For GUIDED: the one pending step, exact destination/section and copy/paste
  content or durable reference, pre-edit identity, expected saved result, and
  remaining inspection/check. Record whether offered, applied but unchecked, or
  inspected; never treat “offered” or the user's “done” as proof of the edit.
- Blocking question matching `Active Work.BlockedOn`, or `NONE`.
- Verified owned correction, if any, with evidence and remaining full-gate work.
  For a **Documenter Corrective Return**, record why the protocol's conditions
  hold and, for each remaining documentation item, its unfinished prerequisite,
  owner, required evidence, and when to revisit it. Keep the record incomplete;
  reference current ACs when available without inventing future artifacts/IDs.
- Whether the selected target and full Documenter gate are each complete, and
  the resulting recovery/normal handoff. Reference state for authoritative
  routing. Full documentation completion is not cycle completion or sign-off.

---

## Authoring Rules

Keep required sections concise and substantive; use `NONE` or an explicit
not-yet-assessed explanation rather than empty fields. Persist enough to resume
without authoring chat. `IN_PROGRESS` means work remains; `BLOCKED` means a
required action or dependency prevents completion, including a pending guided
edit. `COMPLETE` means the full Documenter gate passed for current inputs.

Persist normalized mode, target, and explicit user-style choices; default to
AUTONOMOUS, ACTIVE_CHANGE, and NONE for new work without selections. Resume
persisted choices unless explicitly changed. A supplied file defaults new work
to FILE/AUTONOMOUS. Do not add approval status or a style-lock field.

Keep useful superseded evidence, reopen unsupported conclusions, and avoid
cosmetic rewrites or duplicate entries. A fully assessed no-change result uses
this same template and gate. Do not leave sample discrepancy text in the record.
