# Autonomous Mode

Use after the user approves the current development plan when Developer should
carry implementation through without pausing between atomic steps.

## Procedure

1. Start at the first approved step that is not `DONE`.
2. Set the step to `IN_PROGRESS`, implement it, run its self-check, then set it
   to `DONE` only when the expected outcome exists.
3. Continue directly to the next approved incomplete step.
4. Stop only for a blocking user question, a required material plan revision, a
   protocol failure handoff, expedited promotion, cancellation, or completion.
5. Keep progress persisted in the development plan so another session can resume
   from the first incomplete step.

Do not ask for routine confirmation between approved steps. User approval of the
current material plan is the execution authority for this mode.
