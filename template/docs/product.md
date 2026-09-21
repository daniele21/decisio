# Product

This document owns concise durable product truth. Keep it current, decision-relevant and short enough for a new maintainer or coding agent to understand the product before shaping a material feature.

Do not turn it into a backlog, historical diary, exhaustive PRD or duplicate of architecture/feature documentation.

## Mission

<REPLACE_WITH_WHY_THIS_PRODUCT_EXISTS_AND_THE_DURABLE_OUTCOME_IT_ENABLES>

## Primary users / consumers

- <REPLACE_WITH_PRIMARY_USER_OR_CONSUMER_AND_CONTEXT>

## Core problems / jobs

- <REPLACE_WITH_IMPORTANT_PROBLEM_OR_JOB_THIS_PRODUCT_OWNS>

## Value proposition

<REPLACE_WITH_THE_VALUE_CREATED_FOR_THE_PRIMARY_USER_OR_CONSUMER>

## Meaningful differentiation

- <REPLACE_WITH_A_REAL_DIFFERENTIATOR_OR_REMOVE_IF_NOT_APPLICABLE>

## Core outcomes

- <REPLACE_WITH_AN_OBSERVABLE_USER_OR_CONSUMER_OUTCOME>

## Non-goals

- <REPLACE_WITH_A_BOUNDARY_THE_PRODUCT_DELIBERATELY_DOES_NOT_OWN>

## Product principles

- <REPLACE_WITH_A_DURABLE_DECISION_RULE_THAT_SHOULD_CONSTRAIN_FEATURE_CHOICES>

## Product quality attributes

Record only quality attributes that materially shape product value. Technical thresholds/budgets belong with their engineering owner.

| Attribute | Importance | Product promise / principle | Technical owner |
| --- | --- | --- | --- |
| <privacy/reliability/performance/etc.> | <critical/high/normal> | <durable product requirement> | <owner path/doc> |

## Success signals

Use the least invasive evidence sufficient to understand whether the product creates its intended value. Not every project needs analytics.

- Acceptance: <how supported behavior is proven correct>
- Outcome: <how the primary user/consumer outcome is observed>
- Product impact: <adoption/task-success/quality/support/other signal when material>

## Canonical product sources

- Product development routing: `.engineering/product.json`
- Architecture: `docs/architecture.md`
- Current integrated/blocked/next truth: `docs/current-state.md`
- Feature behavior: `docs/features/`
- Product experience, when `product-ui` applies: `design/ux-contract.json` and `design/brand-kit.json`
- Delivery/build/E2E routing: `.engineering/commands.json` and `.engineering/e2e.json`

Update this file only when durable product mission, target user/consumer, owned problem, value, boundaries, principles, core outcomes or material product-quality promises change. Feature-local implementation detail belongs elsewhere.
