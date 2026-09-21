# repo-template-sw — Coding Agent Guide

This repository owns the reusable engineering baseline distributed to other projects. Keep it small, stack-neutral at the core, and safe to copy.

## Read only what the task requires

- `STANDARD.md` owns universal engineering invariants and maturity levels.
- `PRODUCT-DEVELOPMENT-CONTRACT.md` owns stack-neutral product intent, product-risk, assumption/evidence, shaping, success and learning semantics.
- `OPERATING-CONTRACT.md` owns universal setup/dev/test/E2E/build/smoke/package/artifact/runtime/cleanup semantics.
- `E2E-ENVIRONMENT-CONTRACT.md` owns universal E2E target-environment/fidelity semantics, delivery-stage environment policy and UI evidence modes.
- `EXECUTION-CAPABILITY-CONTRACT.md` owns delivery stages, risk-based validation depth, executor classification, remote-preflight/evidence-reuse and no-human-runner semantics.
- `PRODUCT-EXPERIENCE-CONTRACT.md` owns universal UX/UI semantics for repositories that opt into `product-ui`.
- `template/` owns files copied/specialized into projects.
- `template/.engineering/product.json` owns machine-readable adopter product-development applicability/routing.
- `template/.engineering/commands.json` owns the machine-readable adopter operating, development-velocity and execution-routing shape/defaults.
- `template/.engineering/e2e.json` owns machine-readable adopter E2E target environments, execution environments, stage policy, fidelity gaps, critical journeys and UI evidence policy.
- `template/docs/product.md` owns the adopter product source-of-truth template.
- `template/design/` owns opt-in adopter UX/brand contract templates.
- `template/skills/` owns project-local recurring workflows, including product shaping, validation/preflight/remote-preflight/workstream planning.
- `profiles/` owns optional stack/domain/product-surface additions and native mappings.
- `skills/adopt-engineering-standard/` owns first adoption/alignment.
- `skills/update-engineering-standard/` owns later migrations between baseline versions.
- `CHANGELOG.md` owns version deltas that matter to adopters.

Do not load every profile or Skill when changing one concern.

## Non-negotiable invariants

- The universal core must not depend on a specific language, framework, cloud, product-management framework, design tool, visual trend or application architecture.
- Product impact depth (`PRODUCT_NONE`, `PRODUCT_LOCAL`, `PRODUCT_FEATURE`, `PRODUCT_STRATEGIC`) is independent from engineering delivery stage and validation depth.
- Meaningful product work reasons from user/problem/outcome through material value/usability/feasibility/viability risks and assumptions before substantial implementation; discovery may narrow, change or reject a requested solution.
- Product reasoning is proportional: implementation-only work must not inherit feature/strategic product ceremony.
- Shipping proves delivery, not product impact. Post-release learning is required only when material real-use uncertainty remains, and telemetry is not mandatory by default.
- Product quality attributes such as privacy, reliability, compatibility, resource budgets, performance or developer experience are product requirements when they materially shape user/consumer value, then become measurable engineering invariants at their technical owners.
- Common command names define semantics, not a universal build tool; do not force wrappers merely for uniformity.
- Delivery stage (`ITERATION`, `INTEGRATION`, `RELEASE`) and validation depth (`LEAN`, `SCOPED`, `STRONG`, `FULL`) are independent dimensions.
- Ordinary implementation optimizes for sufficient confidence per feedback time; exact-head/full-diff/docs/preflight ceremony begins at integration readiness, not every private edit or draft update.
- `INTEGRATION` must satisfy affected automatable gates and critical E2E before the coherent outcome enters the shared development/integration branch; residual `REAL_ENVIRONMENT` requirements are declared and `DEFERRED_TO_RELEASE`, not normal integration blockers.
- `RELEASE` requires `FULL` release-grade evidence and every applicable blocking `REAL_ENVIRONMENT` confirmation before `RELEASE_READY`.
- Validation selectors identify risk dimensions and required gates before summarizing them as a profile; profiles must not become monolithic suite aliases.
- Required validation strength is independent from the current coding agent's execution environment.
- An automatable deterministic gate must not become a user task solely because the current agent lacks a shell, checkout, SDK or platform toolchain.
- Equivalent successful evidence should be reused instead of rerun: exact-head/base/gates for integration candidates, and post-merge tree-equivalent reuse only when the Git tree and target/base relationship are provably unchanged.
- When an equivalent local environment exists, local execution should precede CI confirmation; when it does not, repository-owned remote automation is a valid execution backend.
- E2E execution capability and environment fidelity are independent; emulator/simulator evidence must not be promoted into physical/target-environment evidence.
- UI E2E evidence is risk-based: `ASSERTIONS`, `SCREENSHOTS`, or `FULL_MEDIA`. A material UI/UX critical journey entering the shared integration branch uses `FULL_MEDIA` by default; UI that is merely an incidental harness for a non-visual invariant may remain assertion-only.
- Missing artifacts required by the selected UI evidence mode make evidence incomplete; the mode must not be downgraded after execution to obtain green status.
- Remote execution of change-branch code must preserve least privilege and must not gain production/signing/deployment secrets merely for convenience.
- Product-experience semantics define clarity/accessibility/recoverability, not one visual style or component framework.
- `product-ui` is opt-in and only appropriate for repositories with a material user-facing interface.
- A project remains self-contained after adoption; ordinary development must not require this repository at runtime.
- Template updates are explicit migrations, never invisible remote behavior changes.
- Prefer zero-dependency validation tooling when the standard library is sufficient.
- Do not duplicate universal rules across profiles or Skills; link to the canonical owner and add only procedure/specialization.
- `AGENTS.md` is routing/invariants, `.engineering/product.json` is product-development routing, `.engineering/commands.json` is project operation/development-velocity/execution routing, `.engineering/e2e.json` is E2E environment/evidence routing, Skills are conditional procedures, docs are durable facts, scripts/CI are deterministic enforcement/execution.
- Completed implementation plans are deleted by default after durable knowledge transfer; Git is implementation history.
- Parallel development should converge early onto the coherent vertical outcome; stacked publication is exceptional rather than implied by parallel branches.
- Material builds/artifacts/runtimes follow operating-contract identity, bounded-retention and zero-residue invariants without prescribing stack-native implementation details.
- UI products should use a declared design source of truth, semantic tokens, progressive disclosure and appropriate accessibility/critical-journey evidence without creating a second visual truth in generated media.
- Do not add a template file because it is merely common. Add it only when it protects a meaningful cross-project invariant or recurring workflow.
- Profiles add the smallest justified stack/domain/product delta; they do not become internal frameworks.
- Changes to required invariants, copied Skills or machine-readable semantics require a baseline version/changelog decision.

## Change workflow

1. Identify the canonical owner: universal standard, product-development contract, operating contract, E2E contract, execution/development-velocity contract, product-experience contract, copied template, optional profile, adoption/update procedure or validation tooling.
2. Check direct consumers because copied template/Skill/contract changes alter future coding-agent behavior.
3. Prefer a small compatible change. If adopter behavior changes materially, update `VERSION` and `CHANGELOG.md` coherently.
4. Keep template files usable after project specialization; do not bake repository-specific paths/build systems/product-management tools/design tools into the universal core.
5. When changing product-development semantics, update `PRODUCT-DEVELOPMENT-CONTRACT.md`, `.engineering/product.json`, product source template, verifier, product/workstream routing and adoption/update guidance together.
6. When changing operating/execution/development-velocity semantics, update machine-readable defaults, verifier, applicable Skills/profiles and adoption/update guidance together.
7. When changing E2E fidelity/evidence semantics, update `E2E-ENVIRONMENT-CONTRACT.md`, `.engineering/e2e.json`, verifier, validation/preflight routing and applicable profile/adoption/update guidance together.
8. When changing product-experience semantics, update `PRODUCT-EXPERIENCE-CONTRACT.md`, `product-ui`, design templates, verifier, Skills and adoption/update guidance together.
9. Run template validation before publishing.

## Validation

```bash
python3 template/scripts/verify_repository.py --root template --template-mode
python3 template/scripts/verify_operations.py --root template --template-mode
python3 template/scripts/verify_e2e.py --root template --template-mode
python3 template/scripts/verify_stage_environment_policy.py --root template --template-mode
python3 template/scripts/verify_product_development.py --root template --template-mode
python3 template/scripts/verify_product_experience.py --root template --template-mode
python3 template/scripts/verify_docs.py --root template --template-mode
python3 template/scripts/verify_agent_context.py --root template --template-mode
python3 -m unittest discover -s tests -v
```

Inspect the full diff and ensure no placeholder intended for adopter specialization leaked into universal claims as if it were already configured.

For significant agent-guidance changes, use the read-only decision scenarios in `evals/README.md`; report behavioral smoke separately from measured implementation performance.
