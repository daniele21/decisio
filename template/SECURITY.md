# Security policy

## Reporting

<REPLACE_WITH_PRIVATE_SECURITY_REPORTING_CHANNEL_OR_POLICY>

Do not publish exploitable vulnerability details in a public issue before a remediation path is agreed.

## Repository baseline

- secrets, signing material, private tokens and credentials are never committed;
- example configuration uses non-secret placeholders;
- sensitive user content/private paths are excluded from normal logs and telemetry;
- trust boundaries and any remote/cloud processing are explicit;
- local-only behavior must never silently fall back to remote processing;
- dependency/security scanning is configured according to the project's threat model;
- temporary files, imports, caches and persisted sensitive data have cleanup/deletion semantics;
- destructive migrations or account/data deletion paths require explicit tests/review appropriate to their risk.

Document project-specific supported versions, threat assumptions and response process during adoption.
