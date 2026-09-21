# AWS cloud profile

Add when AWS is a material runtime, integration or deployment surface.

This profile maps the universal operating, validation and E2E contracts onto AWS-native infrastructure without requiring one compute model or IaC tool.

Minimum additions:

- infrastructure topology and service ownership are explicit enough to identify request/event boundaries, persistence owners and trust boundaries;
- infrastructure is reproducible through the repository's established IaC mechanism; console-only production configuration is treated as drift unless explicitly justified;
- IAM follows least privilege for humans, CI and runtime identities; change-branch automation does not receive production, signing or deployment authority merely for convenience;
- secrets and sensitive configuration use an explicit secret/configuration owner rather than source control or ad-hoc environment copying;
- asynchronous work defines delivery semantics, idempotency, retry/backoff, timeout, concurrency/backpressure and dead-letter/recovery behavior where applicable;
- serverless/container workloads define bounded runtime, memory/concurrency expectations and failure behavior rather than relying on platform defaults implicitly;
- event-driven boundaries distinguish at-least-once delivery from exactly-once business effects; duplicate delivery must not silently duplicate irreversible effects;
- persistence choices are driven by access/consistency/retention requirements; DynamoDB, S3, relational stores, queues and caches are not interchangeable implementation details;
- environment/account/region boundaries and promotion paths are explicit for material infrastructure;
- CloudWatch/OpenTelemetry or established equivalents expose enough logs, metrics and traces to diagnose request/event identity, retries, throttling, dependency failures and cost/latency regressions;
- infrastructure and AI/external-service cost drivers have explicit ownership and representative measurement where cost materially affects product value or reliability;
- rollback/recovery semantics exist for deployable services, stateful migrations and infrastructure changes whose failure cannot be corrected safely by a simple forward deploy.

## AWS service mapping

Use native services when they fit the required semantics; do not add services only to resemble a reference architecture.

Typical mappings include:

- object/blob storage -> S3;
- functions/event consumers -> Lambda;
- container workloads -> ECS/Fargate or the project's established container platform;
- deterministic workflow orchestration -> Step Functions;
- durable queues/backpressure -> SQS;
- pub/sub notifications -> SNS;
- event routing/integration -> EventBridge;
- key-value/document access patterns -> DynamoDB;
- relational workloads -> Aurora/RDS or an established managed relational store;
- model/foundation-model access -> Bedrock where adopted;
- logs/metrics/traces -> CloudWatch plus OpenTelemetry-compatible instrumentation;
- secrets -> Secrets Manager/Parameter Store according to the project's security model;
- encryption keys -> KMS where customer-managed key policy is material.

The mapping is illustrative, not prescriptive. Preserve a stronger existing AWS platform abstraction or platform-engineering layer rather than bypassing it for profile compliance.

## Failure and delivery semantics

For every material async boundary, record enough durable design truth to answer:

1. What is the unit of work and stable idempotency key?
2. What delivery guarantee does the transport actually provide?
3. Which failures are retried, after what delay/backoff and for how long?
4. What is the maximum useful concurrency and what provides backpressure?
5. Where does poisoned/unrecoverable work go?
6. Which side effects are safe to repeat and which require deduplication or transactional protection?
7. What evidence proves recovery rather than only the happy path?

Do not claim exactly-once processing merely because duplicate business effects are prevented. Transport delivery and business idempotency are separate claims.

## Operating-contract mapping

Map repository-native AWS tooling to `.engineering/commands.json` instead of forcing wrappers.

- `doctor` should verify required CLI/IaC/runtime tooling, credentials/account/region intent and non-secret local prerequisites without printing secrets;
- `check` should include IaC/static/policy validation that is deterministic and cheap enough for the selected risk;
- `test` should cover domain logic, serializers/contracts, idempotency and failure policy without requiring live AWS when substitutes prove the invariant;
- `e2e` should exercise complete request/event workflows through representative disposable infrastructure when AWS service semantics are material;
- `build`/`package` should preserve deployable artifact identity independently from mutable deployment state;
- deploy/promotion commands must make target environment/account/region explicit and must not be hidden behind ambiguous defaults;
- `clean` removes only project/run-owned local or ephemeral cloud test resources with bounded scope and explicit ownership.

## AWS E2E environment fidelity

Do not collapse local mocks, emulators and real AWS into one confidence claim.

A useful progression is:

```text
pure domain/contract tests
-> local substitutes/emulators where useful
-> disposable real AWS integration environment
-> representative staging account/topology
-> target production environment for residual protected-authority/topology claims
```

Real AWS is required only when the claim depends materially on AWS behavior such as IAM policy evaluation, event delivery, throttling, service integrations, runtime/package behavior, managed consistency or network boundaries. Keep expensive live-cloud validation scoped to the smallest workflow that proves the risk.

For integration/release evidence record the material service/topology identity, region/account class where relevant, deployable artifact/source identity and known fidelity gaps. Never use production data or production write authority merely to make E2E realistic.

## Infrastructure change risk

Treat changes touching the following as potentially stronger-risk even when the code diff is small:

- IAM/trust/resource policies;
- networking/private connectivity;
- encryption/key policy;
- queue retry/DLQ/redrive behavior;
- concurrency/reserved capacity/throttling;
- stateful schema/index/storage changes;
- cross-account/region boundaries;
- production deployment/promotion logic;
- destructive lifecycle/retention policies.

Validation strength should follow the concrete blast radius, not the number of Terraform/CDK/CloudFormation lines changed.
