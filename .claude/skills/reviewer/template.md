# Reviewer Artifact Template

Both review kinds use this concise, resumable report. Use the fixed path and
provenance defined by **Workflow Artifact Provenance** in the protocol; do not
add a review-path field or a separate preferences/status file.

Prepend the block with the exact active ID and one concrete kind matching the
path and review state:

```markdown
<!-- STANDARDS
Artifact: REVIEW
Cycle: <Active Work.Id>
ReviewKind: IMPLEMENTATION | FINAL_DELIVERABLE
-->
```

---

# Review Report

`Cycle`: `<Active Work.Id>` `ReviewKind`: `IMPLEMENTATION | FINAL_DELIVERABLE`
`Status`: `IN_PROGRESS | BLOCKED | COMPLETE`

## Assessed Inputs and Scope

- Contract paths and content identities; cycle mode and current acceptance set
  in STANDARD, or bounded request in EXPEDITED.
- Repository baseline/comparison range and its basis, committed and dirty-tree
  content (including untracked/deleted paths), affected unchanged boundaries.
- Development, verification, context, prior reviews, documentation, relevant
  dependencies/configuration, and environment identities used in this
  assessment.
- Included/excluded areas and why; session/model visibility limitations under
  the protocol, without invented identity, capability, or freshness
  attestations.

## Contract and Evidence Assessment

| Obligation / criterion                      | Assessed evidence        | Current disposition                              |
| ------------------------------------------- | ------------------------ | ------------------------------------------------ |
| AC-NNN / design section, or bounded request | Artifact/check reference | Supported, finding, gap, or permitted dependency |

Account for every current AC and relevant technical criterion in STANDARD.
Separate criteria sharing an ID when evidence differs. In EXPEDITED, assess the
request without inventing IDs or requiring skipped artifacts. Retired IDs are
historical only. Distinguish Developer self-checks, Tester formal evidence, and
Reviewer diagnostics; explain what each result actually supports.

## Checks and Results

- Inspection performed or exact command and working directory.
- Assessed content, relevant environment/configuration, and when checked.
- Actual result, exit status when available, and concise useful log pointers.
- What the check establishes and its limits; distinguish unrun, unavailable,
  failed, skipped, interrupted, or inconclusive checks from satisfactory
  results.
- Reused prior evidence with applicability justification, or superseded result
  with the change that invalidates it. Never record secrets or full transcripts.

## Findings

### F-001 — concrete defect

`Severity`: `P0 | P1 | P2` `Status`: `OPEN | RESOLVED | WITHDRAWN` `Owner`:
`<role>` `FailureType`: `<canonical type>`

- **Reference:** exact file/line or artifact section, assessed content identity,
  and relevant AC/technical criterion when applicable.
- **Failure case:** concrete trigger or input and incorrect outcome.
- **Impact:** what breaks or could be lost, exposed, or made unreliable.
- **Evidence:** inspected behavior, reproducer, or actual check result
  supporting the defect; distinguish fact from uncertainty.
- **Smallest correction:** required outcome within the owner's authority.
- **Reassessment:** for resolution/withdrawal, Reviewer-checked evidence and
  reason; preserve useful history and do not accept author status alone.

Use stable report-local finding IDs, qualifying cross-report references with
path and ID. Apply severity and status definitions from Reviewer SKILL.md. Write
**No material findings** when none are established; do not fill a quota.

## Questions, Limitations, and Later Dependencies

Separate unknowns from established defects. For each material gap, record the
missing evidence, consequence for this gate, owner or required user action, and
next check. Explain why a non-material limitation does not prevent completion. A
blocking user question must match `Active Work.BlockedOn`.

Only permitted STANDARD implementation-stage later dependencies may remain at
completion. Record each under the same current AC with its owner and required
evidence. At final review, record the evidence resolving earlier dependencies;
unresolved dependencies cannot support a passing final gate. Use NONE when
empty.

## Progress and Conclusion

- Completed inspection and remaining areas/checks; next concrete action on
  pause.
- Changed inputs on resumption, invalidated conclusions, rechecked fixes and
  boundaries, and justification for retaining still-valid evidence.
- Whether this gate passes and why; unresolved findings/gaps must remain
  visible.
- Concise plain-language summary: can work move forward, what is wrong and its
  consequence, who fixes it, what was checked, and what remains unvalidated.
- Report/evidence references needed for handoff. State and recovery routing stay
  canonical in `STATE.md`; this report does not create a parallel workflow.

---

## Authoring Rules

Keep each section; use explicit NONE, no material findings, or not-yet-assessed
explanations rather than empty tables. `IN_PROGRESS` means assessment is
underway; `BLOCKED` means required correction or evidence prevents completion;
neither is passing. `COMPLETE` requires the shared Reviewer gate and applicable
protocol gate, not merely an empty finding list. Reopen it when changed inputs
invalidate that conclusion. Preserve the other kind's report and other cycles.
Keep useful history, but make current conclusions and next actions unambiguous.
