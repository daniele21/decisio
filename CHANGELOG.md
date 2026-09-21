# Changelog

## Unreleased

## 0.11.0 — 2026-09-07

Extends the baseline from strong agent-native software engineering into proportional **product engineering** without introducing PRD/process ceremony for implementation-only work:

- adds `PRODUCT-DEVELOPMENT-CONTRACT.md` as the canonical stack-neutral owner for product intent, proportional product-impact depth, value/usability/feasibility/viability risks, assumptions/evidence, shaping, success, rollout and post-release learning;
- introduces independent `PRODUCT_NONE`, `PRODUCT_LOCAL`, `PRODUCT_FEATURE` and `PRODUCT_STRATEGIC` depth so product reasoning scales with impact/uncertainty/reversibility rather than file count or engineering delivery stage;
- adds machine-readable `.engineering/product.json` and durable `docs/product.md` routing for product mission, users/consumers, problems/jobs, value, outcomes, non-goals, principles, quality attributes and success signals;
- adds the core `shape-product-change` Skill, allowing discovery to conclude BUILD, NARROW_SCOPE, CHOOSE_ALTERNATIVE or DO_NOT_BUILD and preferring the cheapest useful evidence over full implementation as an experiment;
- distinguishes acceptance, user/consumer outcome and product impact so `SHIPPED` is not silently treated as `PRODUCT_SUCCESS_CONFIRMED`;
- treats privacy, reliability, performance/resource budgets, compatibility, accessibility, developer experience and similar quality attributes as product requirements when they materially shape value, with engineering owners translating them into measurable invariants/evidence;
- extends the existing workstream rather than adding parallel PRD/progress artifacts: material product work may prepend a compact Product Intent/Risks/Success section before the engineering DAG;
- adds a bounded `product` agent context route and zero-dependency `verify_product_development.py`, wired into reference and adopter repository-health CI;
- updates the baseline standard/agent routing so product depth remains independent from `ITERATION -> INTEGRATION -> RELEASE` and `LEAN | SCOPED | STRONG | FULL`;
- bumps the reference baseline to **0.11.0** and registers the new copied Skill.

The 0.11.0 rule is: **problem -> outcome -> material risks/assumptions -> smallest sufficient solution -> evidence; ship safely, then learn only where real-use uncertainty remains.**

## 0.10.0 — 2026-09-06

Reduces repeated agent context and makes diagnosis, implementation and resumption more concrete:

- compresses adopter AGENTS and the structured-change/validate/preflight/remote procedures around canonical task/stage owners;
- upgrades documentation policy to schema 2 and measures full representative routes, including Skills/configuration, applicable scoped-guide chains and optional active workstreams, with bounded text/JSON reports;
- upgrades operating contract to 0.7.0 and execution contract to 0.4.0 with compact native selector/gate reporting, explicit source identity, gate reasons, evidence pointers and preserved failures/gaps;
- defines a short outcome/owner/invariant/proof statement for meaningful changes without mandatory extra plans;
- makes repeated-repair diagnosis evidence-driven, requiring a strategy change and new evidence after two unsuccessful repairs with the same signature;
- adds optional resume checkpoints to existing workstreams and preserves release obligations when closing integration plans;
- aligns copied procedures with material UI integration FULL_MEDIA and real-environment confirmation deferred to release;
- adds five reference behavioral scenarios and meaningful context-verifier regression tests; these do not install per-PR agent benchmarks in adopting projects;
- updates baseline metadata, verifiers, usage and explicit adoption/migration guidance together.

Context reports are estimates; behavioral smoke evaluation is distinct from measured end-to-end agent performance. No automatic migration of adopting repositories is implied.

## 0.9.2 — 2026-09-05

Makes the boundary between development integration and release acceptance explicit so real-environment testing no longer sits in every feature PR loop:

- defines `INTEGRATION` as automated confidence for a coherent vertical outcome entering the shared development/integration branch;
- requires affected critical E2E journeys to be proven automatically before integration when lower-level tests cannot establish the complete outcome;
- makes residual `REAL_ENVIRONMENT` requirements non-blocking at `INTEGRATION` and carries them explicitly to `RELEASE`;
- makes every required residual real-environment confirmation blocking for final stable/release readiness;
- strengthens material UI/UX integration journeys to `FULL_MEDIA` evidence by default: bounded screenshot checkpoints plus a continuous journey video, while preserving `ASSERTIONS` when UI is only an incidental harness for a non-visual system invariant;
- adds machine-readable integration/release stage policy to `.engineering/commands.json` and `.engineering/e2e.json`;
- adds `verify_stage_environment_policy.py` and wires it into both the reference template CI and adopted repository-health workflow;
- updates `preflight-change` readiness semantics so `AUTOMATED_PREFLIGHT_CONFIRMED` can integrate with real-environment evidence explicitly `DEFERRED_TO_RELEASE`, while `RELEASE_READY` additionally requires applicable real-environment gates to pass;
- updates the Android profile so emulator/instrumentation/built-APK E2E plus UI screenshots/video establish development-branch confidence, while physical/OEM/device-specific evidence becomes release acceptance by default;
- keeps early physical-device runs valid for diagnosis of explicitly hardware-specific defects without turning them into a standard branch/PR integration blocker;
- bumps the reference baseline and `preflight-change` source version to **0.9.2**.

The 0.9.2 rule is: **prove the feature automatically before dev; prove the residual target-environment delta before main/release.**

## 0.9.1 — 2026-09-03

Closes the remaining duplicate-validation gap after a green integration PR is merged with a content-preserving commit transformation:

- adds Git `source_tree` to validation evidence identity alongside exact head, target/base, required gates, profile and E2E identity;
- keeps exact-head evidence mandatory for the integration candidate itself and for normal RELEASE/reference-grade validation;
- allows repository-owned post-merge CI to reuse successful integration evidence after squash/rebase only when the merged commit has the exact same Git tree as the validated candidate and the push base exactly matches the target/base used by that validation;
- requires direct integration-branch pushes, moved bases, changed trees, broadened gates, stale evidence or otherwise unprovable identity to execute validation normally;
- distinguishes truthfully between `exact-head` reuse and `tree-equivalent` reuse rather than pretending an older run executed on the new commit object;
- adds machine-readable `post_merge_tree_equivalent_reuse_allowed`, `post_merge_tree_reuse_requires_same_target_base` and `direct_push_without_equivalent_evidence_must_validate` policy flags without changing operating contract `0.6.0`;
- updates `remote-preflight` and the execution capability contract so collaboration metadata and content-preserving merge metadata do not force redundant heavy work when the actual validated source and integration base are unchanged.

The 0.9.1 rule is: **reuse proof when content and integration relationship are provably equivalent; rerun when either changed.**

## 0.9.0 — 2026-09-02

Introduces a **Development Velocity** model so repositories can deliver coherent value incrementally without turning every edit or small PR into a release-grade validation waterfall:

- separates delivery stage from validation depth: `ITERATION -> INTEGRATION -> RELEASE` is now independent from `LEAN | SCOPED | STRONG | FULL`;
- makes `ITERATION` the default implementation loop, optimized for fast formatter/static/affected-compile/focused-test feedback without mandatory exact-head, complete-diff, durable-doc, remote-preflight or release-grade E2E ceremony;
- moves exact-head/base freshness, complete-diff review and affected durable-documentation freshness to the `INTEGRATION` checkpoint, when a coherent observable vertical outcome is actually ready to converge;
- keeps `RELEASE` explicitly reference-grade, with `FULL` validation plus release-critical build/package/E2E and residual environment evidence;
- upgrades `.engineering/commands.json` to contract `0.6.0` with machine-readable `development_velocity`, risk-to-gate selector output, evidence-reuse policy and validation-economics semantics;
- changes validation selection from primarily profile/suite-oriented to **risk dimensions -> concrete required gates -> profile shorthand**, so an important feature-area label does not automatically trigger unrelated broad validation;
- upgrades `EXECUTION-CAPABILITY-CONTRACT.md` to `0.3.0`, preserving `AGENT_LOCAL`, `REMOTE_AUTOMATED` and `REAL_ENVIRONMENT` while making delivery stage, required-gate selection and equivalent evidence reuse first-class;
- updates `preflight-change` and `remote-preflight` to reuse successful equivalent evidence for the same exact source head, material target/base relationship, required gates/profile and E2E environment/evidence mode before starting another expensive remote run;
- explicitly removes PR number, draft/ready state, labels/comments and other collaboration-only metadata from evidence identity, preventing replacement PRs or ready-state transitions from forcing unchanged validation to rerun;
- updates `plan-workstream` so a vertical slice means an observable user/system outcome, while technical layers are normally subtasks and parallel branches converge early onto a coherent feature/integration branch;
- makes stacked publication exception-only: stacked PRs remain valid when levels are independently mergeable/reviewable/value-bearing, while sync-only parent/child PRs are treated as coordination smells;
- upgrades `E2E-ENVIRONMENT-CONTRACT.md` and `.engineering/e2e.json` to `0.2.0`, replacing the 0.8.1 unconditional screenshot+video rule with risk-based UI evidence modes: `ASSERTIONS`, `SCREENSHOTS`, `FULL_MEDIA`;
- retains `FULL_MEDIA` for claims that materially depend on motion/animation, timing/progression, navigation/transition sequencing, lifecycle visibility, gesture continuity or release/product acceptance, while allowing assertion-only evidence when UI is incidental to a non-visual system claim;
- preserves the `E2E_EVIDENCE_INCOMPLETE` invariant: evidence required by the selected mode must be present, identity-bearing, privacy-safe and bounded, and the mode may not be silently downgraded after execution;
- rewrites the Android profile around staged validation: focused compile/unit/direct-contract gates during iteration; Binder/persistence/lifecycle/native/manifest/R8/package/complete-journey gates only when their concrete integration risk requires them; full breadth at release;
- simplifies the ordinary PR template around outcome, risks, required gates, reused/new evidence, applicable E2E, affected durable docs and remaining gaps, while adding a separate release-specific checklist;
- changes documentation timing so unsettled implementation may iterate without repeatedly churning README/current-state/workstream files, while affected canonical docs remain mandatory before integration;
- introduces validation economics as a recommended feedback loop over gate duration, flake rate, unique regression signal and overlap, with the goal of moving high-signal cheap evidence earlier and expensive low-frequency evidence to the checkpoint where it adds value;
- compresses and realigns `STANDARD.md`, `OPERATING-CONTRACT.md`, root/adopter guidance and adoption/migration Skills so the standard itself no longer carries contradictory 0.8.1 publication/media semantics;
- bumps the reference baseline and the affected core Skill source versions to **0.9.0**.

The 0.9.0 delivery model is: **iterate cheaply -> integrate a coherent vertical outcome with exact risk-based evidence -> release with full confidence; reuse evidence instead of rerunning unchanged proof.**

The 0.8.1 screenshot+video requirement remains below as historical release documentation; 0.9.0 supersedes its unconditional applicability with the risk-based evidence modes above rather than removing useful media-capture infrastructure.

## 0.8.1 — 2026-08-31

Strengthens implementation/documentation completeness and makes inspectable UI E2E media evidence mandatory without replacing project-native E2E tooling:

- introduces an explicit documentation-impact contract in `template/docs/README.md` so code and durable documentation ship together;
- splits README ownership into **identity** (title/summary/why, primary audience/outcome) and **usage** (setup/run/use/configuration/public examples), allowing usage changes without opportunistically rewriting stable mission/positioning;
- requires existing feature documentation to update in the same change whenever the durable behavior it describes changes, while still avoiding one-document-per-trivial-feature churn;
- updates `template/AGENTS.md` and `finalize-workstream` so documentation impact is assessed from resulting behavior and mapped to the correct canonical owner before a change/workstream is considered complete;
- updates `preflight-change` with an explicit `DOCUMENTATION_IMPACT` matrix and `DOCS_CURRENT_WITH_IMPLEMENTATION` gate; stale affected documentation blocks publication readiness;
- updates the adopter README template with explicit `Use` and `Configuration` surfaces so the shortest successful public path has a clear owner distinct from architecture/history;
- updates the pull-request template to report README identity/usage, feature docs, architecture, ADR, security/data, operations, product-experience and current-state impact independently;
- deliberately keeps semantic documentation freshness in review/preflight rather than pretending a static documentation checker can prove that prose matches behavior;
- upgrades `E2E-ENVIRONMENT-CONTRACT.md` to `0.1.1` and establishes the rule that every critical journey traversing a UI must produce **both screenshot checkpoints and a complete journey video** as bounded evidence artifacts;
- defines screenshots as fast inspection evidence for materially important UI checkpoints/final reachable state, while the continuous video preserves sequence, navigation, transitions, loading/progress behavior and terminal success/failure context;
- makes a UI E2E run with passing assertions but missing screenshots or video `E2E_EVIDENCE_INCOMPLETE`, preventing it from satisfying complete preflight/release evidence;
- adds machine-readable `.engineering/e2e.json` principle `ui_journey_screenshot_and_video_artifacts_required` and enforces it in `verify_e2e.py`;
- updates `validate-change` and `preflight-change` so artifact presence/identity/privacy/retention is checked before `AUTOMATED_PREFLIGHT_CONFIRMED`, with explicit `E2E_MEDIA_ARTIFACTS` reporting;
- updates the PR template to expose inspectable screenshot and video artifact references per UI-bearing journey;
- specializes Android E2E guidance around native/established screenshot capture plus emulator/device screen recording, without forcing a new cross-platform E2E framework;
- updates adoption, usage and migration guidance so existing repositories preserve stronger E2E tooling while adding only missing screenshot/video capture, CI upload and evidence-gating behavior;
- bumps the reference baseline to **0.8.1**, with `validate-change` and `preflight-change` source versions updated accordingly.

The UI E2E evidence rule is now: **assertions prove the outcome; screenshots make key states inspectable; video proves the executed sequence; all three are required for complete automated UI-journey evidence.**

## 0.8.0 — 2026-08-28

Makes E2E validation explicitly environment-aware so final physical/manual/target testing confirms residual environment-specific risk instead of becoming the first time a complete workflow is exercised:

- introduces `E2E-ENVIRONMENT-CONTRACT.md` with the governing rule **final target-environment validation should confirm residual environment-specific claims, not become the first complete-system test**;
- separates **execution capability** (`AGENT_LOCAL`, `REMOTE_AUTOMATED`, `REAL_ENVIRONMENT`) from **environment fidelity** (`host_or_fake`, `simulated_or_emulated`, `representative_virtual`, `representative_physical`, `target_environment`);
- adds `.engineering/e2e.json` as the machine-readable owner for E2E applicability, target environments, execution environments, material dimensions, fidelity gaps and critical-journey mappings;
- adds zero-dependency `verify_e2e.py` and wires it into template/adopter repository-health CI;
- requires E2E-applicable repositories to identify the target environment and the automated environments used before final validation instead of treating all E2E runs as equivalent evidence;
- updates `validate-change` and `preflight-change` so E2E selection follows both blast radius and the cheapest sufficient declared environment fidelity, escalating only when the product claim depends on missing target dimensions;
- requires E2E evidence to report the actual environment/fidelity used and prevents emulator/simulator evidence from being promoted into physical/target-environment claims;
- strengthens L1/L2 maturity so critical journeys explicitly retain residual fidelity gaps and high-value workflows use the highest practical automated fidelity before final target validation;
- specializes Android guidance around host/JVM -> emulator -> built APK on emulator -> representative physical device -> target/OEM confirmation, while preserving native Compose UI Test/Espresso/UI Automator tooling;
- specializes local-AI guidance so small deterministic model/runtime E2E proves orchestration while representative model/backend/hardware evidence remains required for memory, throughput, thermals and accelerator-specific claims;
- updates adoption/migration guidance so existing strong E2E frameworks are preserved while target/fidelity semantics are layered onto them rather than replaced.

The E2E model is now: **prove invariants low -> prove the complete workflow automatically -> increase environment fidelity only where material -> leave only irreducible target-environment deltas for final confirmation.**

## 0.7.0 — 2026-08-26

Makes preflight execution-capability and blast-radius aware so strong validation neither turns the repository owner into a manual CI runner nor forces full CI on every ordinary PR:

- introduces `AGENT_LOCAL`, `REMOTE_AUTOMATED` and `REAL_ENVIRONMENT` validation execution classes through `EXECUTION-CAPABILITY-CONTRACT.md`;
- establishes the **no-human-runner principle**: an automatable deterministic gate must not be delegated to the user solely because the current coding agent cannot execute it locally;
- keeps **CI should confirm, not discover** when the agent has an equivalent local environment, while explicitly allowing CI/repository automation to become the execution backend when it does not;
- introduces blast-radius validation profiles `LEAN`, `SCOPED`, `STRONG` and `FULL`, with deterministic `auto` selection as the normal path;
- defines `LEAN` for docs/governance/cheap universal guards, `SCOPED` for contained owner/module changes, `STRONG` for cross-boundary/release-sensitive changes, and `FULL` for promotion/release or changes where narrowing cannot safely be trusted;
- requires selectors to fail safe stronger for unknown executable paths and to force `FULL` when CI-scope/global-build/dependency-inventory/toolchain machinery that controls skipping is itself modified;
- allows automatic escalation and explicit stronger overrides, while forbidding silent downgrade below the `auto` profile;
- adds `READY_FOR_REMOTE_PREFLIGHT` and `AUTOMATED_PREFLIGHT_CONFIRMED` alongside the local-capable `READY_FOR_CI` path;
- upgrades `.engineering/commands.json` to operating contract `0.5.0` with machine-readable execution-capability, validation-profile, remote-fallback and remote-preflight security requirements;
- adds the core `remote-preflight` Skill for triggering the narrowest sufficient remote automation, reading logs, classifying failures, fixing the owning cause and retriggering without asking the user to run the same command;
- upgrades `preflight-change` to select validation depth from blast radius and then classify every required gate by the current agent's actual execution capability;
- strengthens Android guidance so Gradle, Kotlin compilation, Lint, R8/minification, unit tests and ordinary APK/package builds are `REMOTE_AUTOMATED` rather than user tasks when a ChatGPT Project lacks Android tooling;
- defines a least-privilege pattern for PR-triggered remote validation: trusted requesters, exact-head pinning, same-repository heads by default, no production/signing/deployment secrets in the code-execution job, and separate reporting permission when needed;
- updates agent/contributor/PR routing and machine verifiers so repositories must preserve selected profile plus the distinction between agent-local, remote-automated and real-environment evidence.

The delivery model is now: **reason -> determine blast radius -> select the narrowest sufficient profile -> classify executor -> automate deterministic validation -> diagnose/fix autonomously -> request human/device evidence only when genuinely non-automatable.**

## 0.6.0 — 2026-08-26

Moves coding-agent quality assurance decisively before remote CI and makes delivery readiness a first-class engineering contract:

- introduces the rule **CI should confirm, not discover** for deterministic repository failures that can be reproduced locally;
- adds a machine-readable `publication_gate` to `.engineering/commands.json` without forcing a universal wrapper command or replacing stack-native tooling;
- adds the core `preflight-change` Skill, which establishes `READY_FOR_CI` only after material ambiguity is resolved, the intended target base is fresh, the complete diff is reviewed, and every required locally reproducible deterministic gate passes on the exact head;
- distinguishes iteration validation (`validate-change`) from final publication readiness (`preflight-change`);
- adds an explicit material-ambiguity protocol: inspect canonical repository evidence first, then ask the user when unresolved alternatives would materially change behavior, contracts, persistence, security, lifecycle, compatibility, acceptance criteria or UX;
- adds a failure root-cause protocol that classifies failures before modifying production code and prohibits test suppression or repeated symptom patching without a new falsifiable hypothesis;
- makes stacked/base-dependent work conditional until dependencies land and exact-head/base validation is refreshed;
- requires deterministic local/CI parity where practical so GitHub Actions invokes the same project-owned validation semantics used by developers/agents;
- strengthens PR readiness reporting with PASS/FAIL/PENDING/N/A evidence and explicit CI-only/device/hardware pending gates;
- extends Android guidance so cheap format/lint/compile/unit gates are expected before publication rather than being delegated to Actions;
- adds L2 feedback through CI first-pass health so recurring avoidable failures are systematically moved earlier into preflight.

The delivery model is now: **reason first -> validate locally -> prove exact-head readiness -> CI confirms -> stronger real-environment evidence completes the claim.**

## 0.5.0 — 2026-08-23

Makes product-experience reasoning an explicit, ordered and proportional workflow instead of a flat collection of UX/UI requirements:

- `PRODUCT-EXPERIENCE-CONTRACT.md` now defines the default decision order: user outcome -> task model -> information architecture/critical journey -> information/action hierarchy -> progressive disclosure/defaults -> interactions/states/feedback/recovery -> adaptive/platform behavior -> accessibility -> design system/components -> motion -> visual polish/graphics -> validation;
- new core `design-product-experience` Skill routes meaningful structural UX, interaction and motion/visual-system changes through that order while keeping visual-only edits proportional;
- `template/AGENTS.md`, `structured-change` and `validate-change` now route meaningful `product-ui` work through the new Skill and explicitly prohibit using motion/graphics/polish to compensate for unresolved structure;
- `design/ux-contract.json` now records primary users/jobs/surfaces, decision-model invariants, purposeful motion semantics and functional-before-decorative graphics roles;
- `design/brand-kit.json` now separates product-owned motion language/tokens (durations, easing, spring/bounce, reduced-motion strategy) from universal UX motion semantics;
- motion is standardized by purpose (feedback, continuity, spatial relationship, state transition, progress, attention, hierarchy, meaningful completion) without forcing universal timings/easings;
- graphics/imagery are treated as functional product tools before decoration, and functional UI must remain understandable without decorative imagery;
- `verify_product_experience.py` validates the new machine-readable decision, motion, graphics and brand-motion contract fields while still avoiding false claims that CI can judge beauty/usability;
- `verify_repository.py` and baseline Skill metadata include `design-product-experience`;
- `product-ui`, adoption and update guidance now preserve proportional design depth and provide an explicit 0.4.x -> 0.5.x migration path.

The central product-experience rule is now: **UX before UI. Interaction before motion. Structure before polish. Evidence before completion.**

## 0.4.0 — 2026-08-17

Adds an optional, stack-neutral Product Experience Contract for repositories with a material user interface:

- `PRODUCT-EXPERIENCE-CONTRACT.md` covering information architecture, progressive disclosure, cognitive load, sensible defaults, action hierarchy, complete UI states, feedback, error recovery, accessibility, adaptive layout, brand/design-system ownership, critical journeys and UX evidence;
- optional `product-ui` profile that preserves platform-native interaction/tooling rather than imposing one visual framework;
- `design/ux-contract.json` and `design/brand-kit.json` template contracts;
- zero-dependency `verify_product_experience.py`, enforced in template CI and automatically `N/A` for adopted repositories without `product-ui`;
- canonical design source-of-truth and key-reference-view requirements instead of uncontrolled mockup/screenshot revisions;
- semantic brand/design tokens instead of scattered raw visual values;
- progressive disclosure and intentional hierarchy as requirements for primary interfaces;
- loading/empty/error/disabled states and actionable recovery treated as correctness concerns;
- WCAG 2.2 AA or stronger declared target for web, with equivalent platform accessibility semantics for native apps;
- responsive/adaptive behavior that preserves content priority;
- critical user journeys linked to E2E where lower-level tests cannot prove the full outcome;
- visual/accessibility/E2E evidence following bounded retention, identity and zero-residue cleanup;
- L0/L1/L2 product-UI maturity for progressively stronger UX, accessibility, regression and usability evidence.

The experience model follows **same semantics, native implementation**: projects converge on clarity, accessibility, progressive disclosure and recoverability without being forced into identical visuals, component libraries or design tools.

## 0.3.0 — 2026-08-17

Adds end-to-end validation as a first-class but stack-neutral part of the project operating contract:

- new canonical `e2e` command intent in `.engineering/commands.json`;
- E2E is recommended rather than universally mandatory, and may be `n/a` only when no meaningful whole-system/user journey exists;
- L1 expects automated end-to-end evidence for critical workflows when lower-level tests cannot establish the complete user/system outcome;
- L2 expects stronger coverage of critical journeys, representative failure/recovery paths and real artifact/device execution where applicable;
- E2E is explicitly distinct from `smoke`: smoke proves minimal runtime/artifact viability, E2E proves a complete workflow outcome;
- E2E runs inherit the zero-residue contract for processes, listeners, browser/device sessions, downloads, test data, temporary workspaces, logs, screenshots, traces and videos;
- failure evidence such as traces/screenshots/logs is treated as bounded CI artifact evidence with build/run identity;
- TypeScript/web guidance prefers Playwright for browser E2E unless an equally strong established solution already exists;
- Android guidance maps E2E to Compose UI Test/Espresso/UI Automator or the established native equivalent;
- macOS guidance maps E2E to XCTest/XCUITest or the established native equivalent;
- Python/server guidance maps E2E to real-process/API workflows rather than introducing browser tooling where no browser exists;
- validation Skills and agent routing now use the canonical `e2e` intent when the blast radius crosses a complete workflow boundary.

This remains **same semantics, native implementation**: the baseline requires the evidence boundary, not one universal E2E framework.

## 0.2.0 — 2026-08-16

Adds a common, stack-neutral project operating contract while preserving native tooling per repository:

- canonical command intents for `setup`, `doctor`, `dev`, `check`, `test`, `build`, `smoke`, `package`, `stop` and `clean`;
- machine-readable `.engineering/commands.json` contract;
- zero-dependency operating-contract validation in project and template CI;
- unique build identity and artifact-lineage semantics;
- immutable successful artifacts with staging/promote behavior, manifests and SHA-256 checksums;
- default local retention of the latest two successful builds per lineage;
- temporary CI-artifact vs durable release-artifact storage policy;
- generated `BUILD_CHANGELOG.md` delta for every successful comparable build;
- localhost/runtime ownership rules: loopback default, collision-aware ports, graceful shutdown and no residual project-owned listeners;
- zero-residue lifecycle rules for processes, sockets, locks, temp data, test databases, logs, caches and other ephemeral resources;
- repeatability and post-clean verification as reference-grade expectations;
- Android, macOS, Python, TypeScript and local-AI profile guidance aligned to the common command/lifecycle semantics.

This is a semantic baseline migration: adopted repositories must classify and implement the relevant operating-contract deltas rather than only bumping metadata.

## 0.1.0 — 2026-08-16

Initial agent-native reference engineering baseline:

- universal L0/L1/L2 engineering standard;
- project-local agent operating model;
- disposable workstream planning lifecycle;
- core reusable coding-agent skills;
- token and documentation budgets;
- zero-dependency repository health checks;
- adoption and update workflows;
- optional stack/domain profile model.
