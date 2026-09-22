# Security

Decisio is an experimental local inference library. It is not currently a hosted service and should not be treated as a safety-critical decision authority without workload-specific validation.

## Reporting a vulnerability

Please do not publish suspected vulnerabilities, credentials, sensitive prompts or private benchmark data in a public issue.

Use GitHub's private vulnerability-reporting flow from the repository Security tab when it is available. If private reporting is unavailable, contact the repository maintainer through their GitHub profile before sharing exploit details publicly.

Include enough information to reproduce the issue safely:

- affected commit/version;
- environment and dependency versions;
- minimal reproduction;
- expected and observed behavior;
- security impact;
- whether untrusted model input, model artifacts or local files are involved.

## Security boundaries

Decisio treats supplied evidence as data rather than instructions, but prompt injection resistance is not a security boundary by itself.

Applications remain responsible for deterministic authorization, policy enforcement, resource limits and action execution. Decisio should rank only alternatives that the owning application has already established as valid to consider.

Model downloads and caches are governed by the upstream model host and local runtime. Pin model revisions for reproducible or security-sensitive deployments.

Do not place secrets or sensitive user data in benchmark fixtures or retained public evidence artifacts.
