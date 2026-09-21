# Android profile

Add only when Android is a material target.

Minimum additions:

- committed Gradle wrapper and pinned compatible JDK/SDK/NDK versions where applicable;
- dependency locking/version catalogs or equivalent reproducible dependency policy;
- formatting/static analysis, unit tests, Android Lint and build gates;
- instrumentation/device validation only for behavior that cannot be proven more cheaply on the host;
- lifecycle-aware ownership for services, processes, threads, models, database handles and native resources;
- memory-pressure and trim/lifecycle behavior when large resident resources exist;
- native pointers/backend-specific structures never escape their owning boundary;
- emulator evidence is never presented as physical-device/production evidence.

## Operating-contract mapping

Keep Gradle/Android tooling native; map it to common intents in `.engineering/commands.json` rather than adding an unnecessary wrapper framework.

Typical mapping:

- `setup` — verify/install documented JDK/SDK components and use the committed Gradle wrapper;
- `doctor` — verify JDK, SDK, ADB and required device/emulator capability;
- `dev` — assemble/install/launch the supported debug variant when useful;
- `check` — format/static analysis + Android Lint + fast unit gates appropriate to the project;
- `test` — relevant unit/integration tests;
- `e2e` — critical complete app journeys using Compose UI Test, Espresso, UI Automator or established native equivalent;
- `build` — produce a uniquely identified debug/internal artifact;
- `smoke` — install and launch the built artifact, exercising a minimal real path;
- `package` — produce signed/unsigned release APK/AAB as appropriate without committing signing secrets;
- `clean` — remove only project-owned generated output;
- `stop` — `n/a` unless the project owns a helper/local server/process that needs explicit shutdown.

## Android development velocity

Treat delivery stage and risk profile as separate dimensions.

### `ITERATION`

Prefer the smallest affected Gradle tasks:

- touched-source formatter/static analysis when practical;
- affected Kotlin/Java compilation;
- focused JVM/unit tests;
- direct contract/consumer tests only when that boundary changed.

Do **not** mechanically run during every edit:

- broad `assembleDebugAndroidTest`;
- minified/release APK/AAB;
- full lint across unrelated modules;
- emulator startup;
- screenshot/video capture;
- native packaging for unrelated changes;
- exact-head remote preflight.

Those gates remain available; they move to the stage where their signal justifies their latency.

### `INTEGRATION`

When a coherent vertical slice is ready to converge into the shared development/integration branch, add gates based on actual Android risks and prove affected complete journeys automatically.

Examples:

| Risk | Typical integration gates |
| --- | --- |
| contained UI/ViewModel/domain behavior | affected compile + focused tests + relevant lint |
| public/shared API or Binder | owner + consumer contract tests + relevant emulator/integration evidence |
| persistence/migration | migration/restart/recovery tests |
| manifest/permissions | manifest/package/install checks implicated by the change |
| R8/ProGuard/release-only behavior | affected minified/release assembly |
| native/JNI/ABI | native host/package/ABI gates required by changed boundary |
| complete navigation/user journey | smallest relevant instrumentation/E2E journey |

For every affected critical journey, prefer the cheapest sufficient automated Android environment, normally emulator/instrumentation or a built APK installed on an emulator.

When UI/UX is materially part of the observable journey, integration evidence is `FULL_MEDIA`: bounded screenshot checkpoints plus one continuous screen recording from meaningful start through success or terminal failure. If an Activity/Compose surface is only an incidental harness for a non-visual system invariant, assertions may remain sufficient.

A required physical/OEM/target-environment confirmation does **not** block ordinary branch/PR integration into the shared development branch. Record the residual device gap and defer that confirmation to `RELEASE`.

Do not map every “Local AI”, lifecycle or UI change to `STRONG` merely because the feature area is important. Map concrete risk dimensions to gates.

### `RELEASE`

Use release/reference-grade confidence:

- full selected Gradle validation;
- R8/minified release/package as applicable;
- release-critical instrumentation/E2E;
- consumer/Binder compatibility where product-critical;
- artifact identity/package/install checks;
- every required representative physical/OEM/target-environment confirmation.

`FULL` is expected here and exceptional during ordinary feature iteration. Required real-device evidence is blocking here, not during normal integration into the development branch.

## Android validation routing

Before integration/release, `preflight-change` selects deterministic Android gates by risk and classifies each:

- `AGENT_LOCAL` when the agent has checkout/JDK/SDK/NDK/tooling;
- `REMOTE_AUTOMATED` when automatable but unavailable locally;
- `REAL_ENVIRONMENT` only when the claim genuinely depends on representative hardware/manual environment.

A ChatGPT Project that can inspect/write GitHub but cannot execute Gradle must **not** ask the user to run `./gradlew`, R8, Lint, unit tests or ordinary APK builds as its normal path. Required gates are `REMOTE_AUTOMATED`.

Before dispatching a new remote run, reuse successful equivalent evidence for the same exact head, material base relationship, required gates/profile and E2E environment/evidence mode. Recreating a PR or moving draft -> ready does not by itself justify rerunning 8–15 minutes of unchanged Android validation.

When equivalent agent-local Gradle capability exists, cheap formatting/compile/unit failures should normally be discovered before CI. When it does not, CI/repository automation is a valid execution backend rather than a process defect.

## Android E2E environment fidelity

Specialize `.engineering/e2e.json` around Android dimensions that materially affect the product.

A useful fidelity ladder is:

```text
host/JVM or fake-backed workflow
-> emulator/instrumentation workflow
-> built APK installed on emulator
-> automated representative physical device/device farm when justified
-> residual target/OEM physical-device confirmation at release
```

Not every project/change needs every rung.

Typical mappings:

- Android host/JVM logic -> `host_or_fake`;
- Android emulator/AVD -> `simulated_or_emulated`;
- real supported APK on representative physical device farm -> `representative_physical`;
- actual supported/OEM device configuration -> `target_environment` for claims it truly represents.

Keep E2E small and critical: first launch, primary create/use/save flow, persistence/restart, IPC/Binder or consumer-app integration, import/export or representative failure/recovery when product-critical.

Prefer lower-level deterministic tests for logic that does not require a complete app/device workflow.

## Android UI E2E evidence modes

A journey touching an Activity/Compose surface does not automatically require video when the UI is only incidental. Material UI/UX integration journeys do.

### `ASSERTIONS`

Use when UI is incidental to a non-visual claim, for example:

- Binder reconnect/recovery;
- durable job ownership;
- persistence/restart semantics;
- background process/lifecycle behavior whose visual sequence is not the claim.

### `SCREENSHOTS`

Use for bounded stable-state inspection where the configured journey is not itself a material UI/UX integration outcome:

- hierarchy/layout;
- copy/content;
- error/recovery state;
- progressive disclosure;
- adaptive/window behavior;
- stable accessibility-visible semantics where screenshots are useful inspection evidence.

Use native/established screenshot capture and keep checkpoints bounded.

### `FULL_MEDIA`

Use for a material UI/UX integration outcome and whenever correctness depends on observing time/sequence:

- end-to-end user navigation being integrated into the shared development branch;
- animation/motion;
- transition/navigation sequencing;
- loading/progress timing;
- foreground/background visibility transitions;
- gesture continuity;
- release/product acceptance of a critical journey.

For `FULL_MEDIA`, produce the required stable screenshots plus one continuous device/emulator screen recording from meaningful start through success or terminal failure.

Artifact names/metadata must identify journey, exact run/build/environment. Upload through normal CI artifact mechanisms with bounded retention and privacy-safe content.

Missing media required by the **selected evidence mode** is `E2E_EVIDENCE_INCOMPLETE`. Do not downgrade the mode after the run to make it green.

## Physical-device evidence

Physical/OEM evidence is a **release acceptance layer** by default. It should not sit in the normal branch/PR -> development integration loop.

The final physical/OEM run should primarily validate residual device-specific gaps such as:

- ABI/native backend behavior;
- memory/GPU/unified-memory pressure;
- OEM lifecycle/process behavior not faithfully emulated;
- audio/camera/sensor routing;
- thermals/performance;
- TalkBack/usability evidence requiring a representative environment.

Broken navigation, persistence, Binder/IPC wiring, install/launch, request/response flow or ordinary restart/recovery defects should move into earlier deterministic/emulator evidence whenever practical.

A developer may still run a physical device earlier for diagnosis of an explicitly hardware-specific problem. That diagnostic run does not turn real-device testing into a standard integration blocker.

## Build/resource lifecycle

Each material APK/AAB build carries unique build identity distinct from marketing product version. Put product version, build ID and source revision in artifact name/manifest and use Android `versionCode`/`versionName` consistently with release requirements.

Keep bounded successful local artifacts. Device/emulator E2E must clean run-owned app data, fixtures, helper processes and localhost listeners on success/failure/cancellation. Screenshot/video evidence is bounded execution evidence, not committed durable design truth.

## Android validation economics

Where practical track expensive gates such as AndroidTest assembly, emulator boot/run, native build, minified release assembly and packaging for:

- duration;
- flake rate;
- unique regressions caught;
- overlap with cheaper gates.

Use the result to place high-signal cheap checks in `ITERATION`, affected automated integration gates in `INTEGRATION`, and real-device/release-grade breadth in `RELEASE`.

The objective is not fewer Android tests. It is faster evidence at the stage where each test provides the most value.
