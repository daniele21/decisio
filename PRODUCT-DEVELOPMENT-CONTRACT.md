# Product Development Contract

Version: 0.1.0

This contract defines stack-neutral product-development expectations for repositories that represent a product, platform, developer tool, reusable capability or other software whose value must be reasoned about beyond code correctness.

It standardizes **product intent, decision order, evidence and learning**, not one product-management framework, planning tool, roadmap format or organizational process.

The governing rules are:

> Outcomes before output. Evidence before commitment. Product reasoning must be proportional to product risk.

> A meaningful product change should move from problem -> desired outcome -> material assumptions/risks -> smallest sufficient solution -> evidence, rather than from idea -> feature list -> implementation.

> Shipping proves delivery. Product success requires evidence that the intended outcome improved.

## 1. Applicability

Use this contract when software is expected to create durable value for users, developers, operators, customers or another explicit product consumer.

Pure implementation maintenance may classify as `PRODUCT_NONE` even inside a product repository. A headless library or internal platform may still be a product when it has real consumers, supported outcomes and lifecycle obligations.

Do not force product ceremony onto typo fixes, mechanical refactors, test-only changes, formatting, equivalent dependency maintenance or other work that does not materially change product behavior.

The project declares applicability and routing in `.engineering/product.json`.

## 2. Product source of truth

When applicable, the repository must maintain a concise durable product source of truth, normally `docs/product.md`, that answers:

- who the primary users/consumers are;
- which important problems/jobs the product owns;
- its value proposition and meaningful differentiators;
- core outcomes and explicit non-goals;
- product principles that constrain decisions;
- product quality attributes that are part of the value proposition;
- how product success is observed at a useful level.

This source describes the product that exists and the direction that currently governs decisions. It is not an implementation diary, backlog dump or mandatory long-form PRD.

Feature details remain with their canonical feature/contract owner. Architecture remains with architecture. UX/UI semantics remain with the Product Experience Contract.

## 3. Product change depth

Classify product impact before adding process.

### `PRODUCT_NONE`

No material change to supported user/consumer behavior or product promise.

Examples: local refactor, test repair, CI maintenance, formatting, documentation correction that does not alter product intent.

No product brief is required.

### `PRODUCT_LOCAL`

A small change to already-settled behavior whose problem and solution direction are clear.

Establish only the user/consumer impact, expected outcome and observable acceptance needed to avoid implementing the wrong local behavior.

### `PRODUCT_FEATURE`

A new capability or meaningful change to an existing workflow/public behavior.

Establish problem, primary user/consumer, desired outcome, non-goals, material product risks/assumptions, product-quality constraints, success evidence and acceptance before committing to substantial implementation.

### `PRODUCT_STRATEGIC`

A material change to target user, product boundary, positioning/value proposition, trust model, platform, business/distribution model or other decision that can invalidate large areas of downstream design/engineering.

Use stronger discovery: problem evidence, alternatives, product risks, assumptions, decision evidence, success signals, rollout/compatibility implications and learning plan.

Depth is driven by impact, uncertainty and reversibility, not by ticket size.

## 4. Product intent before solution

For `PRODUCT_FEATURE` and `PRODUCT_STRATEGIC`, establish at minimum:

```text
USER / CONSUMER
-> PROBLEM / JOB
-> DESIRED OUTCOME
-> WHY IT MATTERS / EVIDENCE
-> NON-GOALS
```

Do not let a requested component, screen, endpoint or implementation mechanism silently become the problem definition unless the solution has already been deliberately settled.

A coding agent may still implement a directly specified solution when intent is clear, but should surface a material conflict with durable product intent instead of optimizing the wrong local request.

## 5. Four product risks

Consider four independent product risks at proportional depth:

- **VALUE** — will the intended user/consumer care enough for the change to create meaningful value?
- **USABILITY** — can the intended user/consumer understand and successfully use the resulting behavior?
- **FEASIBILITY** — can the solution meet the required technical, operational, security, performance and lifecycle constraints?
- **VIABILITY** — is the behavior sustainable for the product/ecosystem, including support, compatibility, policy, cost or business constraints that materially apply?

Not every change has meaningful uncertainty in every dimension. Mark a risk low or N/A rather than inventing ceremony.

Usability depth for material interfaces is refined by `PRODUCT-EXPERIENCE-CONTRACT.md`. Feasibility depth is refined by the engineering/operating/execution contracts.

## 6. Assumptions and evidence

Treat an important uncertain belief as an assumption instead of silently promoting it to fact.

For material assumptions record only what is needed to make a decision:

```text
ASSUMPTION
-> CONSEQUENCE IF WRONG
-> CURRENT EVIDENCE
-> CHEAPEST USEFUL FALSIFICATION / CONFIRMATION
-> DECISION
```

Useful product evidence may include representative-user observation, structured feedback, support signals, existing usage, prototype/usability evidence, dogfooding, benchmark/technical spike, market/alternative evidence, privacy-safe telemetry or a bounded experiment.

Choose the least expensive and least invasive evidence sufficient for the decision. Do not build the entire solution merely to test an assumption that a smaller experiment can falsify.

Discovery may validly conclude `DO_NOT_BUILD`, `NARROW_SCOPE` or `CHOOSE_ALTERNATIVE`.

## 7. Shape the smallest sufficient solution

Once product intent and material uncertainty are understood:

1. identify the smallest coherent solution that can create the desired outcome;
2. compare credible lower-cost/lower-complexity alternatives when the solution is not already settled;
3. make non-goals explicit;
4. preserve product principles and quality attributes;
5. avoid speculative flexibility whose value has not been established.

A technically elegant solution is not preferred when a materially simpler solution satisfies the product outcome and invariants.

## 8. Product quality attributes

Quality attributes that materially affect user/consumer value are product requirements, not engineering afterthoughts.

Examples include:

- privacy/data locality;
- security/trust;
- reliability/recoverability;
- latency/perceived performance;
- memory/CPU/GPU/battery/thermal budgets;
- offline behavior;
- accessibility;
- compatibility/support surface;
- portability;
- developer experience;
- cost where it changes viable product behavior.

`docs/product.md` should identify the attributes that shape the product promise. Technical owners then translate them into measurable invariants, budgets and validation evidence.

## 9. Product experience and engineering handoff

Product shaping does not replace UX or engineering design.

The intended order is:

```text
PRODUCT INTENT / OUTCOME / RISKS
        -> PRODUCT EXPERIENCE (when applicable)
        -> ENGINEERING SHAPE / OWNERSHIP / INVARIANTS
        -> IMPLEMENTATION / VALIDATION
```

For material UI work, hand the settled user/outcome/constraints into `design-product-experience` rather than restarting from visual components.

Engineering participates before solution commitment when feasibility, performance, security, lifecycle or platform constraints can materially change the product solution.

## 10. Define success at three levels

Distinguish:

### Acceptance

Did the implemented behavior satisfy the intended contract?

### Outcome

Did the user/consumer become materially more able to achieve the desired result?

### Product impact

Did the change improve a meaningful product signal such as activation, adoption, retention, task success, support friction, trust, reliability or another declared product goal?

Not every change needs quantitative telemetry. Evidence may be deterministic, qualitative, operational or quantitative according to the claim and privacy constraints.

`SHIPPED` is not equivalent to `PRODUCT_SUCCESS_CONFIRMED`.

## 11. Release and rollout

For product-impacting release changes, consider as applicable:

- target channel/audience;
- compatibility and migration;
- data/schema behavior;
- feature gating/staged rollout;
- fallback/rollback;
- support/documentation readiness;
- release notes and discoverability of the capability.

Release engineering proves a distributable candidate. Product rollout governs how users safely receive and understand the change.

## 12. Observe and learn

For `PRODUCT_FEATURE` and especially `PRODUCT_STRATEGIC`, identify the post-release question when material:

```text
What would we want to know after real use that pre-release validation cannot prove?
```

Examples:

- is the capability discovered/adopted?
- does the primary journey succeed?
- did failure/support friction decrease?
- did experienced latency/resource behavior remain acceptable?
- did the change create an unintended workflow or compatibility cost?

Do not collect telemetry without product value. Prefer privacy-preserving and proportionate evidence.

Durable learning should update the owning product/feature/architecture/test contract. Do not accumulate a permanent research diary in active implementation plans.

## 13. Product evolution, compatibility and deprecation

Supported product capabilities have a lifecycle:

```text
introduce -> support -> evolve -> deprecate -> remove
```

Material public/consumer-facing removals should identify compatibility impact, migration path, communication and support window appropriate to the product.

Do not preserve obsolete behavior forever by default, but do not break supported consumers merely to simplify implementation without an explicit product/compatibility decision.

## 14. Product workstreams

Use the existing workstream mechanism only when persistent coordination is justified.

For `PRODUCT_FEATURE`/`PRODUCT_STRATEGIC`, a workstream may include a compact Product Intent section before the engineering DAG. It should contain only current decision inputs: user/problem/outcome, product depth, material risks/assumptions, success evidence and non-goals.

Do not create separate PRD/plan/progress/status files for the same change when the existing workstream can carry the bounded information.

The work graph should still decompose by coherent observable vertical outcomes, with technical layers as subtasks where appropriate.

## 15. Product maturity

For repositories where product development is applicable:

### L0 — Product-defined

- primary users/consumers and core problems/jobs are explicit;
- value proposition, core outcomes and non-goals are explicit;
- material product quality attributes are identified;
- meaningful changes can be distinguished from implementation-only work.

### L1 — Product-managed

L0 plus:

- `PRODUCT_FEATURE`/`PRODUCT_STRATEGIC` work states problem, outcome, product risks and success evidence before substantial implementation;
- important assumptions are distinguished from facts and tested proportionately;
- UX/engineering decisions preserve the same product intent;
- release/rollout/compatibility implications are handled where material.

### L2 — Product-learning

L1 plus:

- significant released changes identify useful post-release questions/evidence where pre-release validation is insufficient;
- product evidence changes priorities or product behavior when it contradicts assumptions;
- product health is understood through relevant adoption/task-success/quality signals without requiring invasive telemetry;
- compatibility/deprecation decisions are deliberate and documented.

## 16. Product Definition of Done

A material product change is complete when the applicable path is coherent:

```text
PROBLEM / USER
-> DESIRED OUTCOME
-> MATERIAL RISKS + ASSUMPTIONS
-> SMALLEST SUFFICIENT SOLUTION
-> PRODUCT QUALITY CONSTRAINTS
-> UX + ENGINEERING SHAPE
-> ACCEPTANCE + VALIDATION
-> RELEASE / ROLLOUT
-> POST-RELEASE QUESTION / LEARNING (when material)
```

Not every change requires every step. No later implementation or visual polish should silently substitute for an unresolved earlier product decision that could materially change what should be built.
