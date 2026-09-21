# Optional profiles

Profiles extend the universal engineering baseline with a small set of stack-, domain- or product-surface-specific expectations. They are guidance packs, not frameworks and not mandatory dependencies.

A profile should exist only when multiple repositories benefit from the same non-obvious rules or validation pattern.

Profiles map universal contracts onto native stack/product behavior. They must not force a universal task runner, E2E framework, cloud framework, AI framework, design tool or visual style merely to make repositories look identical.

Current profile families:

- `python` — packaging, lockfiles, typing/test conventions, process/API E2E, Python CI and native local-server/build lifecycle mapping;
- `typescript` — package-manager locking, typecheck/lint/test/build, generated-asset boundaries, native dev-server/build mapping and Playwright-preferred browser E2E when a new framework is needed;
- `android` — Gradle wrapper/toolchain, dependency locking, lint/static/unit/instrumented validation, native UI E2E and APK/AAB identity/smoke mapping;
- `macos` — native lifecycle, packaging/signing, filesystem paths, XCTest/XCUITest-style E2E, built-artifact smoke validation and representative device validation;
- `aws-cloud` — AWS IaC/runtime/security/event-delivery semantics, least privilege, retries/idempotency/backpressure, cloud observability and environment-fidelity mapping;
- `terraform` — Terraform-specific state, lockfile, environment composition, plan/apply, import/drift and stage-aware infrastructure validation semantics;
- `ai-systems` — production AI behavior identity, deterministic/probabilistic boundaries, model/prompt/retrieval evaluation, grounding, AI observability and cost/latency quality evidence;
- `agentic-ai` — bounded agent autonomy, tool contracts, state/memory boundaries, authorization/policy, trajectory evaluation, multi-agent justification and deterministic orchestration shells;
- `local-ai` — model/resource lifecycle, memory pressure, admission/backpressure, complete pipeline E2E, benchmark identity and owned local-runtime cleanup;
- `product-ui` — ordered user-outcome-first UX reasoning, progressive disclosure, information/action hierarchy, cognitive-load control, complete UI states, accessibility, adaptive layouts, semantic motion/graphics, brand/design-system ownership, critical journeys and UX regression evidence for products with a material interface.

Stack profiles primarily refine [`OPERATING-CONTRACT.md`](../OPERATING-CONTRACT.md). Infrastructure tooling profiles such as `terraform` refine [`INFRASTRUCTURE-AS-CODE-CONTRACT.md`](../INFRASTRUCTURE-AS-CODE-CONTRACT.md). Domain/capability profiles such as `ai-systems` and `agentic-ai` refine the universal product/operating/validation contracts only where AI behavior introduces additional non-obvious invariants. `product-ui` primarily refines [`PRODUCT-EXPERIENCE-CONTRACT.md`](../PRODUCT-EXPERIENCE-CONTRACT.md).

Profiles are composable. Use the smallest applicable set and avoid copying overlapping rules into the project. `agentic-ai` normally composes with `ai-systems`; `local-ai` and `ai-systems` are complementary when a product both runs models locally and depends on probabilistic AI quality/evaluation. `terraform` normally composes with a cloud/runtime profile such as `aws-cloud` rather than duplicating provider-specific semantics.

Examples:

```text
Android local-AI app
-> android + local-ai + ai-systems + product-ui

macOS desktop app
-> macos + product-ui

TypeScript web app
-> typescript + product-ui

headless Python API
-> python

AWS service with Terraform
-> python + aws-cloud + terraform

AWS AI service with deterministic model calls/retrieval
-> python + aws-cloud + terraform + ai-systems

AWS agentic AI service
-> python + aws-cloud + terraform + ai-systems + agentic-ai
```

A project records adopted profiles in `.engineering/baseline.json`, maps native commands in `.engineering/commands.json`, records infrastructure applicability/mechanism in `.engineering/infrastructure.json`, and copies/specializes only the local guidance and contracts it actually needs.

Do not create an organization-specific template merely because several repositories share a company name. First extract reusable technology/domain invariants into generic profiles; add an organization overlay only when multiple repositories share stable company-specific rules such as security, tenancy, deployment, governance or operational boundaries that are not appropriate for the universal baseline.
