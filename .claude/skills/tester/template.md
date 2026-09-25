# Tester Artifact Template

The verification report is Tester's concise, resumable assessment for one cycle.
Use the location and provenance defined by **Workflow Artifact Provenance** in
the protocol. Tests remain in the repository's established test locations. Both
modes use this format; do not create a separate preferences or status file.

Prepend the exact current-cycle provenance:

```markdown
<!-- STANDARDS
Artifact: VERIFICATION
Cycle: <Active Work.Id>
-->
```

---

# Verification Report

`Cycle`: `<Active Work.Id>` `Mode`: `VERIFY | REVERIFY` `Status`:
`IN_PROGRESS | BLOCKED | COMPLETE`

## Assessed Inputs

- Scope, architecture, context, and development-plan paths with relevant
  revisions/content identities; current acceptance set.
- Active-change source and test boundaries, including committed and dirty-tree
  content, relevant dependencies/configuration, and execution environment.
- Reason for this assessment or reconciliation; session-freshness visibility
  limitation when applicable. Do not claim a machine-certified fresh session.

## Acceptance Evidence

| AC / technical criterion | Tests or checks          | Disposition and evidence |
| ------------------------ | ------------------------ | ------------------------ |
| AC-NNN / design section  | Scenario/check reference | Result or gap reference  |

Use test paths and scenario names, commands, or inspections. Record verified
with result evidence, blocked/uncovered with the gap, or pending a later role
with its owner and required evidence.

Account for all current IDs and relevant technical criteria without rewriting
their meaning. Separate criteria sharing an ID when their evidence differs.
Retired references may remain in a concise superseded-evidence note, never as
current coverage. Presence of a test is not a passing result.

## Scenario Budget

| Source file | Reused coverage  | Active-change allocations | User additions |
| ----------- | ---------------- | ------------------------- | -------------- |
| Source      | Reused scenarios | Allocations               | Additions      |

Record any user additions with their targeted area/limit and user direction.
Apply the counting rules in `SKILL.md`; record cross-file assignments and
parameter/property counts when relevant. Preserve allocations across sessions
and modes, including invalidated/replaced scenarios. Do not list every unrelated
existing test. When blocked by the ceiling, name the unmet criterion, proposed
additional scenarios, and smallest requested increase.

## Execution Evidence

- Exact command and working directory (or precise inspection performed).
- Assessed revision/content and relevant environment/configuration; when run.
- Actual result, exit status if available, counts and log/artifact pointers when
  useful. Separate passes, failures, skips, and unrun/unavailable checks.
- Coverage/limitations: what the result establishes and what it does not.
- Still-valid prior Tester result reused and reason, or superseded result and
  why new evidence is required. Developer self-checks are not formal evidence.

Keep only enough detail to audit and resume; link useful logs rather than
copying terminal transcripts. Never record credentials or sensitive values.

## Open Findings and Dependencies

- Evidence/reproducer, affected AC or technical criterion, owning role, and
  required correction for each unresolved defect.
- Required unrun checks or uncovered obligations and the cause of each gap.
- Explicit later-role dependency, its AC, owner, and evidence still required.
- Blocking user question, if any, matching `Active Work.BlockedOn`.

## Resume or Handoff

Record the next concrete action on interruption, or the completion conclusion
and evidence locations for the receiving role. State which acceptance evidence
remains pending downstream. Supply enough context for the protocol's independent
Reviewer session and identify the requested review kind. Workflow state and
recovery routing remain canonical in `STATE.md`, not in this report.

---

## Authoring Rules

Keep Assessed Inputs, Acceptance Evidence, Scenario Budget, Execution Evidence,
and Resume or Handoff. Omit Open Findings and Dependencies only when empty. Use
explicit NONE or not-yet-run explanations rather than empty required tables.

`IN_PROGRESS` means verification is underway; `BLOCKED` means required work
cannot currently complete. Neither is passing evidence. `COMPLETE` means the
shared Tester gate passed, possibly with explicitly permitted later
dependencies. Reopen a completed report when reconciliation is needed. Keep
current evidence coherent, preserving only useful prior-result and allocation
history.
