# Feature documentation

Use this directory only for durable behavior that is important enough to need its own owner beyond code, tests and the architecture overview.

A feature document should explain:

- the user/system outcome;
- the canonical source owner;
- the public or domain contract;
- important constraints and failure semantics;
- how the behavior is verified.

Do not create one file per implementation task. Prefer code and tests when behavior is already obvious there.

Feature documents describe **current behavior**, not implementation progress. Active progress belongs in `docs/current-state.md` or an explicit workstream.
