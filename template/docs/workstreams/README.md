# Active workstreams

This directory contains only substantial work that currently needs explicit dependency/state coordination.

Do not create a workstream for a small local change that can be implemented and validated coherently in one task.

Use `_template.md` and the `plan-workstream` Skill. Each active workstream owns both plan and progress; do not create separate plan/progress/status files.

When all acceptance criteria are satisfied, use `finalize-workstream`: transfer durable current behavior to code/tests/feature/architecture/ADR/runbooks as applicable, update `current-state.md`, then delete the completed workstream by default.
