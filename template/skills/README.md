# Core project-local Skills

These Skills are copied into adopting repositories and versioned with the project. They encode recurring procedures that should not inflate the root `AGENTS.md`.

Core set:

- `plan-workstream` — create a bounded dependency-aware active plan only when coordination is justified;
- `shape-product-change` — classify material product impact, establish user/problem/outcome, expose material product risks/assumptions and shape the smallest evidence-supported solution before substantial implementation;
- `structured-change` — preserve ownership, simplicity, ambiguity, resource/failure/data invariants during meaningful changes;
- `design-product-experience` — reason through meaningful UX/UI work in the correct order, with proportional depth, before implementation/polish;
- `validate-change` — choose the narrowest sufficient validation while iterating and diagnose failures at their owning invariant;
- `preflight-change` — establish exact-head/base automated-validation readiness and classify required gates as agent-local, remote-automated or real-environment;
- `remote-preflight` — trigger, inspect and iterate repository-owned remote deterministic validation when the current agent lacks equivalent local execution capability, without delegating automatable tests to the user;
- `provision-infrastructure` — design and implement persistent/shared infrastructure through the declared IaC mechanism, using plan/apply and environment authority proportional to stage and blast radius;
- `finalize-workstream` — transfer durable knowledge and delete completed plans by default;
- `review-reference-quality` — perform an L0/L1/L2 gap review before important milestones.

Projects may specialize local copies. Record customization in `.engineering/baseline.json` so future baseline migrations merge rather than overwrite local procedure.

`shape-product-change` is conditional in use: `PRODUCT_NONE` implementation work bypasses it, `PRODUCT_LOCAL` needs only local outcome/acceptance reasoning, and `PRODUCT_FEATURE`/`PRODUCT_STRATEGIC` use it before substantial implementation. Product depth is independent from engineering delivery stage and validation depth.

`design-product-experience` is conditional in use: headless repositories keep the Skill dormant, while repositories adopting `product-ui` use it for meaningful structural UX, interaction or motion/visual-system changes. Local visual-only token/style edits should stay proportional rather than expanding into unnecessary design process.

`preflight-change` is a publication boundary, not a replacement for the fast edit-test loop. Keep a feature PR draft while substantial implementation is still changing. Moving the coherent candidate to ready-for-review is the default transition into `INTEGRATION`; expensive remote validation must not be attached mechanically to each iteration commit.

`provision-infrastructure` is conditional in use: `.engineering/infrastructure.json` may remain `n/a` for projects without shared infrastructure. Cloud repositories use it to keep infrastructure reproducible, avoid console drift and route Terraform/other IaC planning and apply authority by stage.

Do not create a Skill for one-off instructions. A Skill is justified when a procedure recurs, is conditional, has non-obvious ordering/hazards, or saves substantial repeated agent context.
