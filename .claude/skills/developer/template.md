# Developer Artifact Template

This file is the authoritative artifact shape and authoring contract for the
persisted development plan owned by Developer.

The plan translates the active implementation contract into atomic, resumable
build steps. It is not a replacement for scope, architecture, formal testing,
review, or documentation.

Keep the artifact concise. Preserve `DEV-NNN` identifiers for the active cycle;
do not renumber completed steps when revising the plan.

Every development plan is a STANDARDS cycle-owned artifact. Prepend this block
and replace the placeholder with the exact active cycle ID. The provenance
`Cycle` and the visible `Cycle` field below must always agree.

```markdown
<!-- STANDARDS
Artifact: DEVELOPMENT
Cycle: <Active Work.Id>
-->
```

---

# Development Plan

`Cycle`: `<Active Work.Id>` `Mode`: `AUTONOMOUS | STEPWISE | CODE_WITH_ME`
`User Style`: `<style-name | NONE>` `User Style Locked`: `false | true`
`Status`: `PROPOSED | APPROVED | IN_PROGRESS | COMPLETE`

## Implementation Contract

- `Scope`: `<Active Work.Scope | NONE>`
- `Architecture`: `<Active Work.Architecture | NONE>`
- `Request`: `<brief active request summary>`

## Build Steps

### DEV-001 — concise implementation outcome

`Status`: `PENDING | IN_PROGRESS | DONE` `Depends On`: `NONE | DEV-NNN, ...`
`Acceptance`: `AC-NNN, ... | EXPEDITED_REQUEST`

**Goal**

Describe the coherent implementation outcome this step produces.

**Affected Area**

Identify likely modules, components, paths, boundaries, or data areas. Use file
paths only when they are established enough to be useful; do not pretend a file
is known before repository inspection supports it.

**Expected Outcome**

State what should observably exist or behave differently when the step is done.
Write this so a later Tester can understand what implementation surface is
relevant without treating `DEV-NNN` as the requirement source.

**Self-Check**

List the smallest relevant Developer-level check: build, compile, typecheck,
lint, existing test command, targeted runtime sanity check, inspection, or other
established mechanism. Record the actual command and working directory, result,
relevant assessed revision or dirty-tree content, and any limitation when the
self-check runs. This is implementation feedback, not formal Tester
verification. Keep the evidence sufficient for the protocol's fresh-session
Tester or Reviewer handoff.

**Implementation Notes**

Record only non-obvious local choices or resume information. Omit when empty.

---

## Plan Notes

Record only cross-step sequencing or resume information that cannot be expressed
on an individual step.

---

## Authoring Rules

- Create steps from the active request, completed scope/design when present, and
  relevant repository evidence; do not invent new requirements or architecture.
- Set `User Style` only from an explicit user selection or a previously
  persisted selection for this development plan. Store the direct-child
  `user-styles/<identifier>.md` filename stem only: for example, both `tony` and
  `tony.md` persist as `tony`. Use `NONE` otherwise; `NONE` is reserved for no
  selected user style. Never infer a profile from identity, repository
  ownership, prior usage, or filename, and never store a path as the identifier.
- Start a new plan with `User Style Locked: false`. Allow selecting, changing,
  or clearing `User Style` only before first approval, while the plan remains
  `PROPOSED`. First approval covers the selection, including `NONE`, and sets
  `User Style Locked: true` for the rest of the cycle. Never reset the lock on
  revision, recovery, promotion, or a collaboration-mode switch, even if the
  plan returns to `PROPOSED`. A different style requires a new cycle and plan;
  replacing the current cycle's plan does not unlock it.
- On resume, reload the persisted user style before implementation. If the
  locked file is unavailable, stop until it is restored rather than clearing or
  substituting the style. `User Style Locked` is required; a missing field is an
  invalid plan and blocks implementation until corrected.
- In `STANDARD`, reference the current Scoper-owned `AC-NNN` identifiers covered
  by each implementation step. Do not redefine their wording or use `DEV-NNN` as
  substitute requirement identity.
- In `EXPEDITED`, use `EXPEDITED_REQUEST` rather than fabricating acceptance
  IDs.
- Give each step one coherent implementation outcome. Split work when steps have
  materially different dependencies, observable outcomes, or failure surfaces.
- Do not split mechanically by file, function, or estimated duration.
- Keep dependencies acyclic and explicit when order matters.
- Make the expected outcome concrete enough to distinguish `DONE` from partial
  work.
- Keep self-checks proportional to the step and prefer project-established
  commands. Do not create Tester-owned tests as part of the plan.
- Preserve existing `DEV-NNN` identifiers across plan revisions. Add new IDs for
  genuinely new steps. When recovery or rework invalidates the expected outcome
  of a completed step, reopen only the affected step to `PENDING` or
  `IN_PROGRESS` rather than renumbering it.
- Reopening an existing step to correct implementation under unchanged approved
  intent does not require duplicate user approval. A material change to build
  steps, dependencies, behavior, or technical approach returns the plan to
  `PROPOSED` and requires approval before implementation.
- If a plan originated in `EXPEDITED` and the cycle is later promoted to
  `STANDARD`, reconcile it before further implementation: update the Scope and
  Architecture references, replace `EXPEDITED_REQUEST` with current `AC-NNN`
  mappings, preserve still-valid `DEV-NNN` identities, and reopen invalidated
  steps. Bookkeeping-only reconciliation does not require duplicate approval; a
  material implementation-plan change does.
- `PROPOSED` means implementation is blocked on user approval. `APPROVED` means
  the user approved the current material plan. `IN_PROGRESS` means at least one
  approved step has started or a completed plan has been reopened for
  correction. `COMPLETE` means every current approved step is `DONE` and
  Developer's completion gate otherwise passes.
