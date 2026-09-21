---
name: provision-infrastructure
description: Design and implement persistent/shared infrastructure through the repository's declared IaC mechanism, preferring reproducible code over manual console setup and routing plan/apply validation by delivery stage and blast radius.
---

# Provision Infrastructure

Use for cloud/shared infrastructure changes or when an application feature requires new persistent infrastructure.

Read `.engineering/infrastructure.json` first, then the applicable cloud/profile guidance. Preserve a healthy existing IaC mechanism. If the project is new, cloud-hosted and has no established IaC mechanism, prefer Terraform unless a concrete repository constraint makes another tool materially better.

## 1. Establish ownership and target

1. State the application/system outcome that needs infrastructure.
2. Inventory the resources required: compute, network, storage/data, queues/events, IAM/trust, secrets/config references, observability, DNS/edge and deployment targets as applicable.
3. Identify environment/account/project/region boundaries and the intended non-production/production promotion path.
4. Identify existing resources that must be imported/adopted rather than recreated.
5. Record material data-retention, destructive-change, security, availability and cost constraints.

Do not start by clicking through a cloud console. Manual provider steps are reserved for external authority that cannot be represented safely in IaC.

## 2. Choose the smallest IaC shape

Prefer the simplest repository structure that makes ownership and environment composition clear.

For Terraform, a common starting point is `infra/terraform/` with optional `modules/` and `environments/` only when reuse/authority boundaries justify them.

Do not create modules merely to split every resource into another abstraction layer. Keep tightly-coupled feature resources together when that improves reviewability.

## 3. Design before apply

For each material resource answer:

- who owns it and which feature/runtime consumes it;
- lifecycle/retention/destruction semantics;
- trust/IAM/network boundary;
- state/data sensitivity;
- failure/retry/recovery behavior when applicable;
- scaling/concurrency/backpressure limit where applicable;
- material recurring cost driver;
- environment-specific differences.

For asynchronous AWS boundaries, also preserve the `aws-cloud` delivery/idempotency/retry/DLQ semantics.

## 4. Implement source-controlled infrastructure

Represent persistent/shared infrastructure in the declared IaC mechanism. Keep secret values out of source control and reference the established secret/configuration owner.

For Terraform:

- pin compatible Terraform/provider constraints;
- commit `.terraform.lock.hcl` when providers are used;
- never commit `.terraform/`, state or plan files;
- use remote isolated state with locking/concurrency protection for shared environments;
- make target account/project/region/environment explicit;
- prefer import/state-move operations over unsafe destroy/recreate when adopting existing resources.

Application and infrastructure changes that form one feature should be implemented/reviewed as one coherent vertical outcome.

## 5. Validate by stage

### ITERATION

Use only cheap feedback needed for the current edit, for example formatting, `terraform init -backend=false`, `terraform validate` or equivalent static checks. Do not run remote plans/E2E after every implementation commit by default.

### INTEGRATION

When the coherent feature is complete and ready for the shared development branch:

1. refresh exact source/base identity;
2. run the required IaC static/policy gates;
3. create the smallest material plan(s) for the intended non-production environment/class;
4. inspect create/update/replace/destroy plus IAM/network/data-retention/cost effects;
5. run application tests and affected cloud E2E only when provider/service semantics are material;
6. preserve the plan/evidence identity required by repository policy.

### RELEASE

Use protected production authority. Re-plan the exact promoted candidate when required, review destructive/high-blast-radius changes, apply, verify health and confirm rollback/forward-recovery obligations.

## 6. Drift and emergency changes

If infrastructure exists only in the console, inventory it and bring it under IaC safely. Import/adopt existing resources where necessary and iterate until the plan has no unintended mutation.

If an emergency console change is required, treat it as temporary operational divergence. Reconcile the desired change into IaC or intentionally roll it back promptly; do not create a second durable source of truth.

## 7. Output

Return a compact summary of:

- outcome and owned resources;
- IaC mechanism/root;
- environments/authority boundaries;
- state/secrets approach;
- material risks/cost drivers;
- iteration vs integration vs release validation;
- imports/migrations/manual external-authority steps;
- plan/apply status and remaining gaps.

Do not claim infrastructure is provisioned from source changes alone. Distinguish `CODED`, `PLANNED`, `APPLIED_NON_PROD` and `APPLIED_PROD` evidence explicitly.
