# Architecture

Status: active
Owner: repository
Read when: understanding or changing system boundaries, dependency direction, ownership or runtime composition

## System intent

<DESCRIBE_THE_SYSTEM_IN_A_FEW_PARAGRAPHS>

## Boundary map

```text
<input>
  -> <boundary/adapter>
  -> <domain/core owner>
  -> <infrastructure/runtime owner>
  -> <output>
```

Replace this with the simplest accurate map for the project. Do not force layers that the system does not need.

## Ownership

| Concern | Canonical owner | Direct consumers | Important invariants / regression evidence |
| --- | --- | --- | --- |
| <concern> | <path/module> | <paths/modules> | <short invariant and owning test/command> |

## Resource ownership

Document only significant long-lived/expensive resources here or link to the owning feature specification. For each, make owner/lifetime/bounds/cleanup discoverable.

| Resource | Owner | Lifetime | Bound/pressure policy | Cleanup |
| --- | --- | --- | --- | --- |
| <resource> | <owner> | <lifetime> | <bound> | <cleanup> |

## Trust and data boundaries

<DESCRIBE_LOCAL_NETWORK_REMOTE_PERSISTENCE_AND_SENSITIVE_DATA_BOUNDARIES>

## Composition roots

<LIST_THE_FEW_ENTRY_POINTS_THAT_ASSEMBLE_LONG_LIVED_SERVICES>

## Architecture fitness

<LIST_MACHINE_ENFORCED_BOUNDARIES_OR_TESTS_AND_THE_COMMANDS_THAT_VALIDATE_THEM>

## Durable decisions

Link accepted ADRs instead of repeating their rationale here.
