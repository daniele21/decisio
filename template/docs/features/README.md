# Feature documentation

Feature documents describe durable current behavior, constraints, ownership and verification when those facts are not sufficiently discoverable from public contracts, tests and architecture documentation.

When an implemented change alters behavior already owned by a feature document, update that feature document in the same change. When a new cross-module, operationally important or otherwise non-obvious capability needs durable explanation, create or extend the smallest appropriate feature owner before calling the change complete.

Do not create one file per small feature. Prefer code/tests for obvious behavior and a bounded document for cross-module or operationally important capabilities. Do not create documentation churn when code, public contracts and tests already make the durable behavior clear.

A feature document should normally answer:

- user/system outcome;
- canonical owner and important consumers;
- public/domain contract;
- persistence/data lifecycle when relevant;
- resource/failure semantics when relevant;
- important constraints;
- verification/evidence.

It must describe the feature **as it exists now** and must not contain implementation progress, PR history or a completed task diary.
