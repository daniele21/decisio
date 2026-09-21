# E2E Environment Fidelity Contract

Version: 0.2.1

This contract defines how adopted repositories choose end-to-end execution environments and evidence so automated E2E remains representative enough for the claim without turning every change into release-grade real-environment validation.

The governing rules are:

> A coherent change entering the shared development/integration branch must already prove its affected complete workflow automatically.

> Final target-environment validation confirms residual environment-specific claims at `RELEASE`; it is not a normal blocker for every branch/PR -> integration merge.

> E2E evidence strength follows the claim and stage. Assertions, screenshots and full journey media are distinct evidence modes.

This contract complements, rather than replaces, the project operating contract and execution-capability model.

- `OPERATING-CONTRACT.md` defines what `e2e` means and how the run behaves.
- `EXECUTION-CAPABILITY-CONTRACT.md` defines delivery stage, validation depth and who/where can execute a gate.
- `.engineering/e2e.json` defines target environments, execution environments, critical journeys, stage policy, fidelity gaps and UI evidence policy.

## 1. Execution capability is not environment fidelity

These are independent dimensions.

Execution capability answers:

> Which executor can run this gate in the current session?

Environment fidelity answers:

> How closely does the environment used by the gate represent the target environment relevant to the product claim?

Examples:

| Evidence | Execution capability | Environment fidelity |
| --- | --- | --- |
| Android instrumentation on a CI emulator | `REMOTE_AUTOMATED` | `simulated_or_emulated` |
| Browser E2E on a supported virtual browser/OS | `REMOTE_AUTOMATED` | often `representative_virtual` |
| Automated physical device farm | `REMOTE_AUTOMATED` | `representative_physical` |
| Validation on the actual supported customer/device configuration | `REAL_ENVIRONMENT` | `target_environment` |

Never promote simulator/emulator evidence into a physical-device claim merely because the run is automated and green.

## 2. Delivery-stage policy

### `INTEGRATION`

Before a coherent vertical slice enters the shared development/integration branch:

- all affected deterministic gates must pass;
- affected complete workflows that cannot be proven lower must run automatically as E2E;
- the cheapest sufficient declared automated environment is used;
- residual physical/target-environment gaps are recorded explicitly;
- those residual `REAL_ENVIRONMENT` gaps do **not** normally block integration.

For a material UI/UX critical journey, integration evidence defaults to `FULL_MEDIA`: bounded screenshots plus one continuous journey video. If UI is only an incidental harness for a non-visual system invariant, `ASSERTIONS` may remain sufficient.

### `RELEASE`

Stable promotion/release candidates use release-critical automated E2E plus full release validation. Every real-environment confirmation marked required by the release claim is blocking before final release readiness.

A real-environment run may still happen earlier for diagnosis of a hardware-specific issue. That does not move the standard release gate into every feature-integration loop.

## 3. Fidelity classes

Use these stack-neutral fidelity classes in `.engineering/e2e.json`:

1. `host_or_fake` — useful whole-flow orchestration with material substitutes/fakes or a host environment that does not represent the target runtime.
2. `simulated_or_emulated` — a simulator/emulator reproduces important platform behavior but not all target hardware/runtime characteristics.
3. `representative_virtual` — the real software/runtime surface executes in a virtual/container/host environment representative enough for the stated claim.
4. `representative_physical` — the workflow executes on real hardware representative of the supported target class.
5. `target_environment` — the actual target environment or a configuration equivalent for the claim being validated.

Higher fidelity is not automatically better for every test. Prefer the cheapest reliable automated environment that proves the integration claim; reserve residual target-specific confirmation for release.

## 4. Environment dimensions

Representativeness is claim-specific. Declare only material dimensions, for example:

- operating system/platform and version family;
- CPU architecture/ABI;
- browser/engine;
- device class/form factor;
- native/runtime backend;
- GPU/NPU/accelerator availability;
- memory/storage constraints;
- permissions/sandbox/process lifecycle;
- network topology/external dependency;
- packaged/distributed artifact surface;
- hardware sensors/audio/camera peripherals;
- thermal/power conditions when they materially affect correctness or performance.

Two environments can share a fidelity class while representing different dimensions. Record known gaps explicitly.

## 5. Critical-journey design

E2E remains intentionally small. Keep deterministic local invariants in unit/integration/contract tests and select a bounded set of complete critical journeys whose correctness depends on the assembled system.

For every critical journey declare:

- the user/system outcome being claimed;
- whether it traverses a UI through `ui_surface`;
- the minimum UI evidence mode when a UI is involved;
- target environment(s);
- automated environment(s);
- minimum automated fidelity;
- residual fidelity gaps;
- whether real-environment confirmation is `required`, `conditional` or `not_required`.

When no automated environment can truthfully exercise a required journey, record the automation gap explicitly. Do not silently convert the workflow into an informal human test.

A journey that cannot be automated but is required to prove ordinary application behavior represents an automation capability gap, not a reason to make the user the recurring integration test runner.

## 6. UI evidence modes

UI presence does not automatically imply that the UI itself is the changed claim.

### `ASSERTIONS`

Use when the UI is incidental to the workflow and the changed invariant is better proven by deterministic assertions.

Examples:

- Binder reconnect semantics exercised through an activity only as a harness;
- persistence/restart behavior where visual appearance is unchanged;
- background ownership or process-lifecycle behavior whose truth is not encoded in layout/motion.

Assertions may still emit failure screenshots opportunistically.

### `SCREENSHOTS`

Use when bounded stable visible states need inspection but the complete UI/UX journey itself is not the material integration claim.

Examples include stable hierarchy, copy, layout, recovery states, adaptive behavior or another visually inspectable checkpoint.

Capture only materially important checkpoints and the final reachable state. Screenshots remain bounded evidence, not a parallel design source of truth.

### `FULL_MEDIA`

Use when UI/UX is materially part of the integration outcome or when the claim depends on sequence over time, including materially relevant:

- end-to-end navigation or interaction entering the shared integration branch;
- motion/animation;
- timing/progression/loading behavior;
- navigation or transition sequencing;
- foreground/background/lifecycle visibility;
- gesture continuity;
- release/product acceptance.

`FULL_MEDIA` includes the necessary stable screenshots plus one continuous journey video from meaningful start through success or terminal failure.

The selected mode may be stronger than the journey's configured minimum when the current change/stage requires it.

## 7. Fidelity ladder

The preferred progression is:

```text
unit / component
    -> integration / contract
    -> automated E2E in the cheapest sufficient environment
    -> built/package-artifact E2E when material
    -> integration into shared development branch
    -> release-critical automated E2E
    -> residual target/real-environment confirmation
```

Do not execute every rung mechanically. Validation follows delivery stage, blast radius and claim strength.

A final physical/manual release test should primarily discover defects caused by the remaining fidelity delta: device-specific lifecycle, OEM/runtime behavior, real hardware, thermals, accelerator/backend differences, protected external environments, accessibility/usability judgement or similar constraints that cannot be reproduced earlier.

Ordinary workflow defects such as broken navigation, persistence, IPC/protocol integration, packaging/installability or basic restart/recovery should move into earlier automation whenever practical.

## 8. Built artifact and target surface

When the product claim concerns distributable behavior, prefer E2E against the built/package artifact rather than only a development runner when material.

Artifact execution does not eliminate environment-fidelity gaps. A real APK on an emulator remains emulator evidence for hardware-dependent claims.

## 9. Selection and escalation

During `ITERATION`, `INTEGRATION` or `RELEASE`:

1. identify whether the change affects a critical journey;
2. read `.engineering/e2e.json` including `stage_policy`;
3. select the narrowest affected journey subset;
4. choose the UI evidence mode required by the changed claim and stage;
5. use the cheapest declared automated environment that proves the claim;
6. at `INTEGRATION`, satisfy all affected automated journey evidence and record residual target gaps without blocking on them;
7. at `RELEASE`, run release-critical journeys and close every required real-environment gap;
8. never downgrade environment fidelity or UI evidence after execution merely to obtain a green result.

A repair that changes platform/runtime/packaging/native/hardware assumptions may legitimately broaden automated integration evidence and may alter which residual release gaps exist.

## 10. Evidence

E2E evidence should identify enough context to understand what was actually proven:

- journey/test identity;
- source/build/run identity;
- delivery stage;
- execution environment ID;
- fidelity class;
- selected UI evidence mode;
- material platform/device/browser/runtime dimensions;
- artifact surface used;
- known gaps or residual real-environment requirement;
- relevant privacy-safe logs/traces/screenshots/videos.

Evidence completeness depends on the selected mode:

- `ASSERTIONS` — required deterministic assertions and ordinary failure evidence are present;
- `SCREENSHOTS` — assertions plus required screenshot checkpoints are present;
- `FULL_MEDIA` — assertions plus required screenshots and continuous journey video are present.

If a required artifact for the selected mode is missing, report `E2E_EVIDENCE_INCOMPLETE`. Do not silently downgrade the mode after execution to turn a run green.

On failure, preserve bounded useful evidence when technically possible. If the run fails before UI rendering or recording can begin, report the pre-UI/pre-recording failure truthfully rather than fabricating media.

All evidence must remain identity-bearing, privacy-safe and bounded by artifact-retention policy.

## 11. Platform specialization

Profiles may add the smallest platform-specific mapping without redefining the universal fidelity or evidence model.

Examples:

- Android distinguishes host tests, emulator/instrumentation, built APK on emulator, physical device farms and OEM/target release evidence.
- macOS/iOS distinguishes host/unit execution, simulators where applicable, packaged app execution and real-device/platform release evidence.
- browser/web distinguishes mocked/dev-server flows from supported browser/OS/deployment combinations.
- local-AI systems distinguish small deterministic model/runtime E2E from representative model/backend/hardware release evidence for memory, throughput, thermals and accelerator-specific behavior.

The common requirement is **same semantics, native implementation**. Media capture should use established platform/framework tooling rather than forcing one universal library.

## 12. Completion rule

An affected critical journey is integration-ready when:

- required lower-level deterministic evidence passes;
- required automated E2E passes at the declared automated environment fidelity;
- evidence required by the selected UI mode is complete;
- built/package execution is covered when material;
- residual fidelity gaps are explicit.

It is release-ready only when, in addition:

- release-critical automated evidence passes;
- every applicable `real_environment_confirmation: required` gap passes in the representative/target environment.

`AUTOMATED_PREFLIGHT_CONFIRMED` therefore means automated integration evidence is complete even when residual real-environment evidence is explicitly deferred. `RELEASE_READY` means those required residual release gaps are also closed.
