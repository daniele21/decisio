# Infrastructure as Code Contract

Version: 0.1.0

This contract defines the repository-level expectations for persistent/shared infrastructure. It standardizes lifecycle, ownership and reproducibility without forcing one cloud provider or one IaC framework.

The governing rule is:

> Persistent/shared infrastructure is code-owned. Manual console configuration is an exception, not the operating model.

The tool-selection rule is:

> Preserve a fit-for-purpose existing IaC mechanism. For a new cloud project with no established IaC standard, Terraform is the preferred default unless a repository-specific reason justifies another tool.

## 1. Applicability

Use this contract when the repository owns or materially configures cloud/shared infrastructure such as compute, networking, storage, databases, queues, identity/policy, secrets/configuration owners, observability, DNS, deployment targets or managed AI services.

Purely local applications with no shared infrastructure may set `.engineering/infrastructure.json` to `n/a`.

## 2. Source of truth

Infrastructure topology, configuration and lifecycle must be reproducible from versioned source plus intentionally external secret values/credentials.

Console-only or ad-hoc CLI mutation of shared infrastructure is drift unless explicitly recorded as emergency/exception handling and reconciled back into code immediately afterward.

Do not place secret values in source control. Secret *resources*, access policy and references belong in IaC; secret values belong in the repository's declared secret/configuration owner.

## 3. Tool selection

Do not migrate a healthy existing CDK, CloudFormation, OpenTofu, Pulumi or other IaC implementation solely for template uniformity.

For new cloud projects without an existing standard, prefer Terraform because it provides provider-neutral declarative infrastructure, explicit planning and a broad ecosystem. A project may choose another mechanism when its platform, team or product constraints make that mechanism materially better.

Record the selected mechanism and infrastructure root in `.engineering/infrastructure.json`.

## 4. Repository structure

Keep infrastructure close enough to the product repository that application and infrastructure changes can be reviewed together when they form one feature.

A typical Terraform layout is:

```text
infra/terraform/
├── modules/
│   ├── app/
│   ├── data/
│   ├── networking/
│   └── observability/
└── environments/
    ├── dev/
    ├── staging/
    └── prod/
```

This layout is illustrative, not mandatory. Prefer the smallest structure that keeps reusable modules, environment composition and ownership understandable.

## 5. Environment separation

Development, staging and production must not rely on ambiguous implicit defaults for account/project/subscription, region or destructive authority.

Environment-specific values should be explicit inputs/configuration rather than copied source trees where practical. Separate state/authority so a development operation cannot accidentally mutate production.

## 6. Plan before apply

A material infrastructure change follows:

```text
change
-> format/static validation
-> provider/module validation
-> plan/diff
-> review risk and destructive effects
-> apply to intended environment
-> post-apply verification
```

The plan/diff is the primary pre-apply artifact. Review create/update/replace/destroy behavior, IAM/trust changes, network exposure, data-retention effects and cost-sensitive resources before apply.

Feature branches must not receive production apply authority merely for convenience.

## 7. State

IaC state is operational data, not normal source code.

For shared Terraform/OpenTofu environments:

- use remote state;
- isolate state by environment/account/project boundary;
- enable locking or an equivalent concurrency guard;
- protect state because it may contain sensitive metadata/values;
- never commit `.tfstate` files;
- preserve the provider dependency lock file when the tool uses one.

State migration/import is a controlled operation. Importing an existing manually-created resource is preferable to recreating it unsafely when adoption begins.

## 8. Drift and imports

When infrastructure already exists manually:

1. inventory the actual resources and owners;
2. decide which resources the repository should own;
3. write the IaC representation;
4. import/adopt existing resources where safe;
5. compare plan against reality until unintended mutation is eliminated;
6. only then make IaC the normal change path.

Do not blindly recreate production infrastructure to achieve aesthetic consistency.

## 9. Risk routing

Infrastructure validation strength follows blast radius, not line count.

Treat these as stronger-risk by default:

- IAM/trust/resource policy;
- public/private networking and ingress/egress;
- encryption/key policy;
- stateful databases/storage/indexes;
- retention/destructive lifecycle;
- cross-account/project/region boundaries;
- queue retry/DLQ/redrive semantics;
- concurrency/reserved capacity/throttling;
- production deployment/promotion authority;
- resources with material recurring cost.

At `ITERATION`, run only cheap local format/validate/static checks needed for the current edit. Expensive remote plans or cloud integration checks belong at `INTEGRATION` when the coherent feature is ready. Production apply and destructive/privileged confirmation belong at `RELEASE` unless the repository explicitly defines a safer non-production path.

## 10. Application + infrastructure feature ownership

When an application feature requires infrastructure, design them as one vertical outcome rather than implementing the application first and configuring the cloud manually afterward.

Preferred sequence:

```text
feature outcome
-> architecture and resource inventory
-> trust/data/failure/cost boundaries
-> IaC implementation
-> application implementation
-> integration plan + application validation
-> affected E2E through representative infrastructure when needed
-> shared development integration
-> release promotion/apply
```

## 11. Agent behavior

For infrastructure work, agents use `.engineering/infrastructure.json` plus `skills/provision-infrastructure/SKILL.md`.

An agent should not end a normal cloud implementation by instructing the user to create persistent resources manually when those resources can be represented safely in the repository's IaC mechanism.

Manual steps remain appropriate for irreducibly human/provider-owned actions such as account creation, billing/legal acceptance, protected credential issuance, DNS registrar authority or other external authority that cannot be automated safely.
