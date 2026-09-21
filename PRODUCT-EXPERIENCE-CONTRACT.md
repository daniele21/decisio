# Product Experience Contract

Version: 0.5.0

This contract defines stack-neutral UX/UI expectations for repositories that expose a material user interface. It standardizes **experience quality, decision order and evidence**, not a visual fashion, component framework or design tool.

Adopt it through the optional `product-ui` profile.

The governing rule is:

> A strong interface makes the user's next decision obvious, reveals complexity progressively, communicates system state clearly, and remains consistent, accessible and recoverable across the product lifecycle.

The ordering rule is:

> UX before UI. Interaction before motion. Structure before polish. Evidence before completion.

## 1. Applicability

Use this contract for applications with a meaningful UI: web apps, mobile apps, desktop apps, embedded product surfaces and comparable interactive products. Do not force it onto headless libraries, APIs or servers with no material user-facing interface.

The depth of product-experience reasoning must be proportional to the semantic impact of the change. A new workflow needs more design reasoning than a local spacing/token correction.

## 2. Product-experience decision order

For meaningful structural UX/UI work, reason in this order:

```text
USER OUTCOME
-> TASK MODEL
-> INFORMATION ARCHITECTURE / CRITICAL JOURNEY
-> INFORMATION + ACTION HIERARCHY
-> PROGRESSIVE DISCLOSURE / DEFAULTS
-> INTERACTIONS + STATES + FEEDBACK + RECOVERY
-> ADAPTIVE / PLATFORM BEHAVIOR
-> ACCESSIBILITY
-> DESIGN SYSTEM / COMPONENTS
-> MOTION
-> VISUAL POLISH / GRAPHICS
-> VALIDATION
```

Later layers may refine earlier decisions, but they must not silently replace unresolved earlier ones.

Do not begin with cards, gradients, animation, illustration, component selection or visual effects when the user task, flow or hierarchy is still unclear.

Motion, illustration and stylistic treatments must not be used to compensate for unresolved task-model, information-architecture, hierarchy, feedback or recovery problems.

## 3. Proportional design depth

Classify product-experience changes before applying process.

### Structural UX change

Examples include a new screen/surface, navigation model, onboarding, workflow, major dashboard/settings redesign or changed information architecture. Use the full decision sequence.

### Interaction change

Examples include dialogs/sheets, selection, drag/drop, progress, gesture behavior, state transitions or recovery changes. Start from the owning task/journey and reason through interaction, states, feedback, accessibility, adaptive behavior, component ownership and motion. Re-open IA/hierarchy only if the interaction changes them.

### Visual-only change

Examples include typography refinement, spacing, semantic color application, radius/elevation or icon treatment without changed task flow or interaction semantics. Start from the existing design-system/brand owner, preserve the settled task/flow and validate hierarchy/accessibility.

Do not create documentation/process ceremony merely because UI code changed. The goal is better decisions, not more artifacts.

## 4. User task model over internal architecture

The UI should model what the user is trying to accomplish, not expose internal architecture by default. Prefer user concepts such as `Record meeting`, `Transcribe`, `Review`, `Export` over implementation concepts such as selecting backends, workers, sessions or queues.

Technical controls may exist when users genuinely need them, but should not dominate the default experience.

Before choosing layout/components for a meaningful flow, identify the primary user, job/decision and successful outcome.

## 5. Information architecture and critical journeys

Every important screen/surface should make these questions easy to answer:

- Where am I?
- What is happening?
- What can I do here?
- What is the primary action?
- What happens next?
- How do I go back, cancel or recover?

Navigation, page structure and labels should be organized around user goals and stable mental models.

Critical journeys should be understandable as a bounded path such as:

```text
entry -> decision -> action -> feedback -> outcome -> next step/recovery
```

UI projects should explicitly identify critical journeys whose failure would materially damage the product experience. Examples may include first run/onboarding, primary create/use/save flow, persistence/restart, import/export, destructive/recovery behavior, authentication where applicable, or the product's core task.

Critical journeys should connect to the repository's `e2e` evidence strategy when lower-level tests cannot establish the full user outcome.

## 6. Information and action hierarchy

Each surface should have an intentional hierarchy of primary, secondary, tertiary and destructive actions. Controls should look and behave like their semantic role. Repeated interaction patterns should remain consistent across the product.

Visual hierarchy should reflect decision hierarchy. A surface should not make many unrelated actions or information blocks appear equally dominant without a deliberate workflow reason.

Spacing, typography and grouping should communicate relationships before extra borders/cards are added merely to create structure.

## 7. Progressive disclosure

Reveal the minimum information and controls required for the user's current decision, while making deeper capability discoverable when needed.

Preferred hierarchy:

```text
essential
  -> contextual
  -> advanced
  -> expert / diagnostics
```

Avoid placing essential, advanced and debugging controls at the same visual level. Advanced configuration, raw data, logs, technical metrics and diagnostics should not dominate normal user journeys unless the product is explicitly an expert tool whose users need them continuously.

## 8. Cognitive load and information density

Completeness is not permission to show everything simultaneously.

Prefer summary -> detail, overview -> drill-down, primary -> secondary -> tertiary action hierarchy, normal use -> advanced configuration, and status -> diagnostics.

Avoid unnecessary walls of text, repeated labels, competing cards, excessive badges, simultaneous metrics and multiple equally dominant calls to action. Dense expert views are allowed when the workflow genuinely benefits from density, but the density must be intentional and navigable.

## 9. Sensible defaults

Normal use should work with strong defaults before the user configures every option.

```text
good default -> normal use
optional customization -> advanced user
expert override -> deep settings
```

Do not make users understand internal implementation details merely to complete the primary workflow.

## 10. Complete state design

Critical components and workflows must consider more than the happy path. Applicable states include:

```text
default
hover
focus
pressed
selected
disabled
loading
empty
success
warning
error
offline
permission-denied
partial-result
```

A state may be `n/a` when the platform/component cannot enter it, but unhandled loading/error/empty/disabled states are not acceptable for critical workflows.

## 11. Feedback and perceived performance

Every meaningful user action should produce timely, understandable feedback.

```text
action
  -> immediate acknowledgement
  -> progress/status when needed
  -> success/failure outcome
  -> clear next action
```

Use progress information when it is truthful and useful. Long-running work should not be represented by an indefinite spinner when meaningful phase/progress/status information is available. Background operations should expose persistent status when the user needs to know they are still running or completed.

Avoid introducing visible loading UI for operations that resolve so quickly that it creates flicker rather than clarity.

Skeletons should approximate the geometry of the content they replace rather than act as decorative placeholders.

## 12. Error prevention and recovery

Prefer prevention over warning, warning over failure, and recovery over dead ends.

Error messages should explain, when known, what failed, why or what constraint was violated, and what the user can do next. Use undo, reversible actions or recoverable states when safer and simpler than confirmation dialogs. Confirmation is appropriate when an action is irreversible or has meaningful external impact.

## 13. Responsive, adaptive and platform behavior

The interface should preserve content priority as available space, device posture, window size or input method changes. Do not treat responsive design as shrinking a desktop layout until it fits.

Projects should define supported layout classes/breakpoints/window ranges or platform-native adaptive behavior and test the important ones.

Use added desktop/tablet space to preserve context, reduce unnecessary navigation or support multi-pane workflows when that improves the task. Do not fill larger surfaces merely because space exists.

Cross-platform products should preserve product semantics while respecting platform-native navigation, touch/mouse/keyboard, focus, gesture and window-management expectations.

State that matters to the user's work should survive resizing/orientation/posture changes when technically applicable.

## 14. Accessibility

Accessibility is part of correctness, not visual polish.

Web products should target WCAG 2.2 AA or a stronger explicitly documented target. Native products should use platform accessibility APIs/guidelines and equivalent semantic requirements.

Applicable requirements include sufficient contrast, keyboard operability where relevant, visible/logical focus order, semantic assistive labels, text scaling/dynamic type, appropriately sized interaction targets, no critical meaning conveyed by color alone, reduced-motion support when animation is non-essential, and accessible error/status announcements.

Automated accessibility checks are useful but do not replace manual/assistive-technology validation for important flows.

## 15. Design system

Brand identity describes how the product looks; the design system describes how the UI is constructed.

Projects should identify canonical reusable components and their states/variants rather than creating visually similar one-off controls repeatedly.

Typical primitives include buttons, inputs, selects, toggles, navigation, tabs, cards, lists/tables, dialogs, popovers, toasts, progress, tooltips, empty states and error states.

> Do not create a new visual component when the existing design system can express the same semantic role without harming usability.

Applicable states/variants should be defined at the canonical component owner instead of reimplemented inconsistently per screen.

## 16. Brand kit and visual language

A UI product should define a durable brand/visual identity source of truth when branding is applicable.

The brand kit should cover as applicable product name, logo variants, application icon, favicon for browser products, semantic color system, typography, spacing scale, radius/elevation treatment, iconography style, motion language, light/dark theme behavior, imagery/illustration style, and voice/microcopy principles.

Use semantic design tokens rather than scattering raw visual values through the codebase. Prefer names such as `color.surface`, `color.textPrimary`, `color.primary`, `color.success`, `color.warning`, `color.error`, `color.border` and `color.focus`.

The universal contract defines why visual/motion choices exist; the project brand/design system owns exact values such as colors, type scale, spacing, duration, easing and spring parameters.

## 17. Motion semantics

Motion is an interaction tool before it is decoration.

Every meaningful animation should serve at least one product purpose:

- feedback;
- continuity between related surfaces/elements;
- spatial relationship;
- state transition;
- progress;
- attention;
- hierarchy;
- meaningful completion/celebration.

Motion should follow the geometry and causality of the interaction. A drawer should emerge from its owning edge; a gesture-driven surface should track the gesture directly; a shared/container transition should preserve identity when that continuity helps orientation.

Frequent interactions should use restrained, fast motion. Larger or less frequent transitions may be more expressive when they communicate structure. Avoid long decorative sequences that make repeated work feel slower.

Prefer smooth/simple motion over visually ambitious motion that causes dropped frames, delayed input feedback or unstable layout.

Projects should encode motion values in the canonical design system/brand tokens rather than scattering arbitrary durations/easings through components.

Reduced-motion preferences must be respected when motion is non-essential. Replace movement/zoom with a simpler transition such as a fade when appropriate rather than merely speeding the same intense motion up.

Do not animate simply because the platform/API makes animation easy.

## 18. Graphics, imagery and data visualization

Graphics should have a product role before a decorative role.

Useful roles include:

- explanation/education;
- orientation;
- onboarding;
- empty-state support;
- status/progress;
- meaningful completion;
- data visualization;
- restrained brand expression.

Functional UI must remain understandable and operable without decorative imagery.

Do not use decorative illustrations, gradients, particles, 3D objects or other visual novelty where they compete with the user's primary task or imply hierarchy that does not exist.

Data visualization should answer a user question or support a decision. Prefer the chart/visual encoding that communicates the needed comparison, trend, relationship or distribution rather than the most visually elaborate chart.

## 19. Typography, spacing, color and surfaces

Use a small intentional typographic hierarchy and spacing scale rather than many arbitrary values.

Use proximity/spacing to communicate grouping before adding containers everywhere. Cards, borders, shadows and elevation should reflect meaningful grouping/layering rather than decorate every block.

Color should be semantic where it carries status or action meaning, and critical meaning must not depend on color alone.

Trend-specific treatments such as glass effects, large gradients, extreme corner radii or decorative shadows are project choices, not baseline requirements.

## 20. Design source of truth and key reference views

The repository must declare the canonical source for product design: Figma, design files in-repo, code-first design system or another explicit owner.

Do not accumulate uncontrolled screenshot versions such as `final2`, `new-final` or duplicate mockup folders.

Maintain only the key reference views necessary to communicate the product system, for example the primary/home surface, main workspace, critical settings/configuration surface, representative loading/empty/error states, and critical user journeys.

Mockups are reference evidence, not parallel truth that silently diverges from production UI.

## 21. Microcopy and language

UI text is part of the interaction contract. Prefer concise, concrete labels based on user goals. Avoid exposing internal implementation terminology without user value. Error/status text should help the user decide what to do next. Terminology should remain consistent across navigation, controls, documentation and errors.

## 22. Debug and expert surfaces

Diagnostics are valuable, especially in technical/local-AI products, but they should be intentionally separated from normal product interaction. Expose raw logs, JSON, low-level metrics and expert configuration through advanced/diagnostic surfaces unless they are central to the user's primary job.

## 23. UX validation and regression protection

Use the narrowest useful evidence for the claim being made. Depending on the stack/project, useful evidence includes component/unit tests, integration tests, E2E for critical journeys, automated accessibility checks, visual-regression tests for stable high-value surfaces, manual keyboard/screen-reader/device checks, and representative-user usability tests for important/high-risk workflows.

Visual-regression testing should protect important visual contracts, not freeze every incidental pixel and make intentional design change unnecessarily painful.

A screenshot can support a visual claim but cannot by itself prove interaction behavior, accessibility, recovery, adaptive behavior or usability.

## 24. E2E and experience evidence lifecycle

UI E2E/visual/accessibility evidence follows the same identity and zero-residue principles as the Project Operating Contract.

A run should have enough identity to associate evidence with source/build/environment. Failed E2E may retain screenshots, traces, videos or logs as bounded CI artifacts.

After the run, project-owned browser/device sessions, servers, ports, downloads, test users/data, temporary profiles and other ephemeral state must be cleaned.

## 25. Experience maturity

For repositories adopting `product-ui`:

### L0 — Healthy product UI

- product experience contract is specialized for the project;
- primary users/jobs and design source of truth are identified;
- core information architecture and critical journeys are named;
- product-experience decision order is preserved for meaningful structural work;
- primary action hierarchy and progressive disclosure are intentional;
- critical loading/empty/error/disabled states exist;
- accessibility target is declared;
- responsive/adaptive scope is declared;
- key design/reference views are identified;
- design tokens/component ownership prevent obvious UI drift;
- motion/graphics semantics are deliberate rather than purely decorative.

### L1 — Production-ready product UI

L0 plus:

- critical journeys have automated E2E evidence when lower-level tests are insufficient;
- important accessibility behavior has automated and/or manual evidence appropriate to the platform;
- high-value responsive/adaptive layouts are tested;
- user-facing failures provide actionable recovery paths;
- visual regression protects stable high-risk surfaces where valuable;
- primary flows have been heuristically reviewed against this contract;
- significant motion has a documented purpose and reduced-motion/performance behavior where applicable.

### L2 — Reference-grade product UI

L1 plus:

- representative-user usability evidence exists for important or high-risk workflows where justified;
- critical UX regressions are protected by E2E/accessibility/visual evidence appropriate to the product;
- product telemetry/research can answer meaningful experience questions without compromising privacy;
- design-system drift and duplicated components/tokens are actively controlled;
- significant UX changes evaluate cognitive load, information hierarchy and recovery behavior rather than only visual appearance;
- motion/graphics/visual polish remain subordinate to task effectiveness and platform performance.

## 26. Product experience Definition of Done

A UI-affecting change is complete only when the applicable experience claim is supported across the relevant portion of this sequence:

```text
USER OUTCOME / TASK MODEL
-> INFORMATION ARCHITECTURE / JOURNEY
-> HIERARCHY / DISCLOSURE / DEFAULTS
-> INTERACTIONS / STATES / FEEDBACK / RECOVERY
-> ADAPTIVE / PLATFORM
-> ACCESSIBILITY
-> DESIGN SYSTEM / BRAND
-> MOTION / VISUAL / GRAPHICS (when applicable)
-> E2E / REGRESSION / USABILITY EVIDENCE
-> CLEANUP / ARTIFACT EVIDENCE
```

Not every UI change needs every level, but no applicable earlier level should be silently skipped because later visual work is easier to implement or demonstrate.
