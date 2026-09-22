---
name: finalize-workstream
description: Close a completed active workstream by validating completion, transferring only durable current knowledge to canonical docs/tests, updating repository state, removing temporary planning material and checking for broken/duplicate documentation.
---

# Finalize Workstream

## Principle

Implementation plans are working memory. Code/tests/current durable docs are long-term memory. Git history preserves how the implementation happened.

Completed plans are deleted by default.

A workstream is not documentation-complete merely because its code and tests are complete. The durable documentation affected by the resulting behavior must describe the system as it exists now.

## Workflow

1. Read the workstream goal, invariants, DAG, acceptance and validation.
2. Confirm every required slice is `DONE` at the declared delivery stage. An integration workstream may close after required automated acceptance passes when residual real-environment obligations are transferred to the canonical release owner/journey with `DEFERRED_TO_RELEASE`, acceptance and evidence pointers. A release workstream cannot close with required real-environment evidence missing. Never delete the only record of a deferred release obligation.
3. Inspect the resulting code/contracts/tests rather than trusting the plan's narrative.
4. Assess documentation impact from the final observable behavior. Use `docs/README.md` when ownership is unclear.
5. Extract only knowledge that future maintainers/users need about the system **as it exists now**:
   - core project purpose, primary audience or primary outcome -> README identity sections;
   - setup, prerequisites, run/start, public configuration, public CLI/API/UI usage or examples -> README usage sections;
   - architecture/ownership changes -> `docs/architecture.md`;
   - durable non-obvious feature behavior -> existing/new `docs/features/` owner;
   - material design decision/rationale -> ADR;
   - security/trust/data-lifecycle contract -> `SECURITY.md` and/or owning architecture/feature doc;
   - operational procedure -> existing/new runbook only when genuinely recurring;
   - canonical command semantics -> `.engineering/commands.json`;
   - executable invariant -> tests/tooling when possible.
6. Treat README identity and usage independently. Do not rewrite mission/positioning merely because a feature or command changed. Do update setup/run/use/configuration/examples when the old path would now be incomplete, wrong or misleading.
7. Do not transfer PR numbers, commit diaries, sequence-of-implementation notes or resolved temporary blockers into durable docs.
8. Update `docs/current-state.md` to remove the workstream and expose the next current target/blocker.
9. Delete the completed workstream file by default.
10. Preserve it only when independent audit/regulatory/release/historical value exists; mark it historical and ensure it is not routed as current truth.
11. Search for stale links/references, instructions, examples and configuration claims affected by the completed workstream and update them.
12. Run repository/docs/agent-context validation and relevant project tests.

## Completion questions

- Can a future agent understand current behavior without the plan?
- Can a new user/developer follow the README's current setup/run/use path successfully?
- If README usage changed, did we avoid opportunistically rewriting still-valid identity/mission copy?
- Is every durable fact in exactly one appropriate canonical owner?
- Are existing feature docs current for the behavior they describe?
- Did we avoid copying implementation history into current docs?
- Is current state now smaller and truthful?
- Is the completed plan gone unless there is a concrete retention reason?

A successful finalization should normally reduce active planning/context size while leaving durable documentation no less truthful than the implementation.
