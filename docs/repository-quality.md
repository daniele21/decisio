# Repository quality and adoption

Status: active improvement plan  
Owner: repository  
Last reviewed: 2026-09-26

## Goal

A new technical user should be able to discover Decisio, understand the stateful-runtime thesis,
run a real local model, trust the evidence boundary, integrate through a small supported API and
contribute without learning hidden repository rules.

This document owns repository usability, reproducibility, adoption and release-facing hardening.
Product scope remains in `docs/product.md`; integrated truth remains in `docs/current-state.md`.

## Current assessment

The repository foundation is now substantially stronger than the original bootstrap:

- `main` presents Decisio rather than the source template;
- README/brand assets explain stable-context reuse and include a real Snake demo;
- GGUF + llama.cpp is the canonical local runtime;
- dependency resolution is locked with `uv.lock`;
- CI, repository-health checks, package build/install smoke, license, contribution and security
  guidance exist;
- benchmark contracts separate short/fresh scorer evidence, repeated-state evidence and Snake
  controller quality;
- current architecture distinguishes implemented owners from planned components.

The remaining work is no longer "add more docs". It is to close evidence, reduce adoption friction
and make repository governance match the engineering discipline already encoded in CI.

## Active axes

- PRODUCT: `PRODUCT_FEATURE` for the one-command onboarding flow; the core product boundary is
  unchanged.
- DELIVERY: `ITERATION` until the adoption candidate is ready for integration.
- VALIDATION: `FULL` because this candidate also corrects the repository-owned E2E validation
  contract; selector/validation configuration changes force full validation.
- EXECUTION: `AGENT_LOCAL` for deterministic tests and `REMOTE_AUTOMATED` for pinned real-model
  CPU evidence. Representative hardware claims remain bound to their declared environment.

## Product intent for adoption hardening

- **User:** engineers evaluating or integrating Decisio for repeated bounded local-LLM decisions.
- **Problem:** the repository is technically rigorous, but first-run setup, stale cross-document
  references and the lack of a small public session API still create unnecessary adoption friction.
- **Outcome:** one obvious first run, consistent durable truth, exact-head runtime evidence, then one
  stable integration surface once the evidence contract supports freezing it.
- **Non-goals:** no hosted service, no hidden model download in benchmark paths, no universal scorer
  promotion, no release claim before the repository release contract is satisfied.
- **Risks:** VALUE `LOW`; USABILITY `MEDIUM`; FEASIBILITY `LOW` for onboarding and docs,
  `MEDIUM` for the future public API; VIABILITY `LOW`.

## Remaining gaps, in order

### RQ-01 — Close the core stateful evidence

**Priority: P0**

The product claim is stable-context reuse over changing state. Promotion therefore requires evidence
that reuse preserves the fresh result and reduces physical model work under the pinned runtime
identity.

Current evidence boundaries:

- 0.8B real-model smoke proves the mechanism and directional token reduction;
- the pinned 2B short/fresh semantic-v2 gate remains a recorded FAIL and is not rewritten;
- repeated-state gate v3 decides only the scoped semantic-v2 repeated-state question;
- Snake controller quality is separate from cache efficiency;
- representative 2B Snake screening and a later holdout remain pending.

Done when the relevant exact-head evidence is retained and `docs/current-state.md` records the
result without broadening the claim beyond the benchmark contract.

### RQ-02 — Keep durable truth consistent

**Priority: P0**

`README.md`, `CONTRIBUTING.md`, `CHANGELOG.md`, architecture, current state and benchmark docs
must agree on:

- Qwen3.5-2B Q4_K_M + llama.cpp CPU as the primary reference evidence identity;
- 0.8B and Metal as separate smoke/operational identities;
- semantic-v2 short/fresh failure;
- stateful reuse as the primary product thesis;
- `DecisionSession` as planned until the evidence/API contract is frozen.

Old 4B/BF16 promotion language must not survive in active contributor guidance.

### RQ-03 — Make the first real run one command

**Priority: P1**

After dependency installation, a user should not need to discover a model URL, filename or checksum
before seeing Decisio work.

The supported repository demo path is:

```bash
uv sync --frozen --extra llama --extra dev
uv run python -m examples.snake.demo --open
```

The runner downloads only the pinned 0.8B smoke artifact, verifies SHA-256 and caches it under
`models/`. A custom GGUF remains explicit with `--model`.

This path is functional onboarding, not representative product evidence.

### RQ-04 — Expose one stable library entry point

**Priority: P1, BLOCKED BY RQ-01**

Normal consumers should not assemble backend + scorer internals manually.

The smallest intended surface remains a high-level session that owns:

- model/backend construction;
- stable decision context;
- bounded choice requests;
- direct stateful readout;
- explicit fresh-vs-reuse behavior where needed;
- typed result, probability status and provenance;
- deterministic close/resource lifecycle.

Do not freeze this API merely to complete repository hardening. Implement it only after the runtime
contract and supported default semantics are sufficiently proven.

### RQ-05 — Protect the default branch and improve GitHub discovery

**Priority: P0 for protection, P1 for discovery**

Repository settings should match the code-level discipline:

- protect `main`;
- require PR-based integration and the repository's required deterministic checks;
- disallow force pushes to `main`;
- set a concise repository description;
- add topics such as `llm`, `llama-cpp`, `gguf`, `local-llm`, `qwen`,
  `decision-making` and `inference`;
- use the prepared social preview from the brand kit.

These are GitHub repository settings rather than source-controlled product behavior.

### RQ-06 — Establish a deliberate alpha release path

**Priority: P1, BLOCKED BY RQ-01/RQ-04**

Build/install smoke already exists in CI, and package version/changelog are Decisio-specific.

Before the first promoted alpha:

- decide the supported public API surface;
- run the repository-defined release validation profile;
- retain exact candidate/base and required real-environment evidence;
- build immutable wheel/sdist artifacts with checksums;
- publish release notes that preserve experimental/evidence boundaries.

Do not create a "release" merely because a version string already exists.

### RQ-07 — Finish public repository hygiene

**Priority: P1/P2**

Implemented or active:

- Apache-2.0 license;
- contribution/security guides;
- PR template;
- structured bug and feature issue forms;
- package metadata/project URLs;
- branded README assets.

Remaining:

- remove or further isolate the root `template/` tree when it is no longer needed as baseline source
  material;
- consider CODEOWNERS / Code of Conduct when contributor volume makes them useful rather than adding
  ceremony pre-emptively.

## Candidate implementation status

| Item | State | Acceptance |
| --- | --- | --- |
| Contributor/changelog drift cleanup | ACTIVE | no current 4B/BF16 promotion guidance remains |
| One-command pinned Snake demo | ACTIVE | download/checksum/launch behavior has deterministic tests |
| Package discovery metadata | ACTIVE | wheel metadata exposes keywords, classifiers and project URLs |
| Structured issue intake | ACTIVE | bug reports request reproducible runtime identity; proposals start from user outcome |
| Exact-head 0.8B real-model smoke | PENDING | fresh/reused equivalence and physical-token reduction pass on candidate |
| 2B repeated-state gate v3 | PENDING | unchanged precommitted gate records PASS/FAIL on candidate |
| Stable `DecisionSession` | BLOCKED | RQ-01 evidence is sufficient to freeze supported semantics |
| First alpha release | BLOCKED | API + release contract satisfied |
| Branch protection / GitHub topics | PENDING REPOSITORY SETTING | source changes cannot substitute for the setting |

## Definition of repository success

Decisio reaches the intended repository quality when a new developer can:

1. understand the core product boundary in under a minute;
2. run a real local demo without discovering an undocumented model setup step;
3. distinguish smoke evidence from representative benchmark evidence;
4. understand what returned scores do and do not mean;
5. integrate through a small supported API rather than experimental internals;
6. reproduce benchmark claims from exact model/runtime/fixture identities;
7. find contribution, security and release expectations directly;
8. trust that `main` cannot bypass the checks the repository declares mandatory;
9. see only current Decisio product truth in active documentation.

More documentation is not the goal. **Less ambiguity and lower adoption friction are.**
