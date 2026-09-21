# Terraform profile

Add when Terraform is the repository's infrastructure-as-code mechanism.

This profile refines [`INFRASTRUCTURE-AS-CODE-CONTRACT.md`](../../INFRASTRUCTURE-AS-CODE-CONTRACT.md). It does not make Terraform mandatory for all repositories and must not replace a healthy existing CDK, CloudFormation, OpenTofu, Pulumi or other established IaC mechanism solely for consistency.

For a new cloud project with no established IaC standard, Terraform is the preferred default unless a repository-specific constraint justifies another tool.

## Minimum expectations

- Terraform source is versioned and is the normal owner of persistent/shared infrastructure changes.
- `.terraform.lock.hcl` is committed when providers are used; `.terraform/`, plans and state files are not committed.
- provider and Terraform version constraints are explicit enough to make plans reproducible.
- shared environments use remote state with isolation and locking/concurrency protection.
- environment/account/project/region targets are explicit and cannot silently fall back to production.
- secret values are not stored in source-controlled `.tfvars`, generated plans or documentation; secret resources/references/policies may be defined in Terraform.
- reusable modules exist only where reuse or ownership boundaries justify them; do not create module layers for aesthetic symmetry.
- `terraform fmt -check` and `terraform validate` are cheap iteration/integration gates.
- a material `terraform plan` is required before apply and is reviewed for create/update/replace/destroy, policy/network/data-retention and cost effects.
- feature/change branches do not receive production apply authority.
- imports/state moves/replacements are treated as explicit migration operations with rollback/recovery consideration.

## Suggested layout

A common layout is:

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

Use a flatter layout when the infrastructure is small. Structure follows ownership and reuse, not a required folder count.

## State

For shared environments prefer a backend that provides durable remote state plus locking or equivalent concurrency protection. Isolate environments so a development plan/apply cannot address production state accidentally.

Treat state as sensitive operational data. Terraform may record resolved values in state even when the source expression is marked sensitive, so secret-handling policy must protect the backend as well as source control.

Do not commit:

```text
.terraform/
*.tfstate
*.tfstate.*
*.tfplan
crash.log
crash.*.log
```

Do commit `.terraform.lock.hcl` unless the repository has a documented exceptional reason not to.

## Environment composition

Prefer one shared implementation with explicit environment inputs/composition over copied dev/staging/prod trees that drift independently.

Separate trees/modules are valid where different lifecycle/authority/architecture genuinely requires them. Avoid Terraform workspaces as an automatic answer to every environment-separation problem; choose state/environment boundaries from failure and authority requirements.

## Plan and apply policy

During `ITERATION`:

- run formatting/validate/static policy only when useful to falsify the current edit;
- do not run remote plans after every commit by default;
- do not apply shared infrastructure merely to prove syntax.

At `INTEGRATION`:

- produce the smallest plan(s) needed for the coherent feature candidate;
- pin source/base identity and intended environment class;
- inspect destructive/replacement behavior and high-risk policy/network/data changes;
- run representative non-production integration/E2E only when provider/service semantics matter.

At `RELEASE`:

- production plan/apply uses protected release authority;
- re-check the final plan against the promoted artifact/source;
- require applicable approval/real-environment confirmation for destructive or high-blast-radius changes;
- verify post-apply health and rollback/forward-recovery path.

## AWS composition

When AWS is the runtime, compose `terraform` with `aws-cloud` rather than duplicating AWS-specific semantics here.

Typical pairing:

```text
Python AWS service
-> python + aws-cloud + terraform

AWS AI service
-> python + aws-cloud + terraform + ai-systems

AWS agentic service
-> python + aws-cloud + terraform + ai-systems + agentic-ai
```

`aws-cloud` owns AWS service/runtime/security/event-delivery semantics. This profile owns Terraform-specific state, plan/apply and repository lifecycle semantics.

## Validation examples

Cheap deterministic checks commonly include:

```bash
terraform fmt -check -recursive
terraform init -backend=false
terraform validate
```

A real plan normally requires the selected backend/provider credentials and therefore belongs in the declared integration/release execution path rather than every implementation commit.

Policy/security scanners such as TFLint, Checkov, tfsec or provider-specific tooling may be added when they provide useful signal; the profile does not require a particular scanner.

## Drift and adoption

For manually-created existing infrastructure, inventory and import safely rather than destroying/recreating resources to satisfy the profile. Iterate until the plan is free of unintended mutation, then make Terraform the normal owner.

Emergency console changes must be reconciled into Terraform promptly or intentionally rolled back. Persistent console drift is not a second supported source of truth.
