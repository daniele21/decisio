# Product UI profile

Add when the repository exposes a material user-facing interface.

This profile applies `PRODUCT-EXPERIENCE-CONTRACT.md` without forcing a design tool, UI framework or visual style.

Minimum additions:

- a declared design/brand source of truth;
- project-specific `design/ux-contract.json` and `design/brand-kit.json`;
- primary users/jobs/surfaces identified for the product experience;
- an explicit product-experience decision model that keeps user outcome/task/IA/hierarchy ahead of motion/visual polish;
- clear information architecture and primary-action hierarchy;
- progressive disclosure for advanced/expert/diagnostic complexity;
- sensible defaults for primary workflows;
- explicit loading/empty/error/disabled and other applicable states;
- accessibility target and platform-appropriate evidence;
- responsive/adaptive behavior across supported sizes/devices;
- semantic design tokens and canonical reusable components;
- purposeful motion semantics plus a project-owned motion language/tokens when motion is used;
- functional-before-decorative graphics/imagery semantics;
- key reference views/mockups for primary surfaces and important states;
- named critical user journeys linked to E2E when lower-level tests are insufficient;
- bounded visual/accessibility/E2E failure evidence with zero-residue cleanup.

## Design workflow

Use the project-local `design-product-experience` Skill for meaningful UX/UI work.

The default ordering is:

```text
user outcome
-> task model
-> IA / critical journey
-> hierarchy / disclosure / defaults
-> interactions / states / feedback / recovery
-> adaptive / platform
-> accessibility
-> design system
-> motion
-> visual polish / graphics
-> validation
```

Apply the depth proportionally: structural UX changes use the full sequence; interaction changes start from the owning task/journey and affected interaction layers; visual-only token/style changes preserve the settled flow and remain local.

## Platform mapping

Use native conventions and strongest existing tooling. Web/TypeScript may prefer Playwright for new browser E2E suites. Android should use native accessibility and UI/E2E tooling. macOS should preserve keyboard/focus/accessibility conventions and use XCTest/XCUITest or established equivalents. Cross-platform apps should remain platform-appropriate rather than forcing identical interactions everywhere.

## Motion and graphics

Motion must serve a product purpose such as feedback, continuity, spatial relationship, state transition, progress or attention. Frequent interactions should remain restrained, gesture-driven motion should follow input directly, performance takes priority over decorative complexity, and reduced-motion behavior must be defined where applicable.

Graphics/imagery should explain, orient, support onboarding/empty/status/data or express brand without becoming necessary to understand functional UI.

The exact motion character, durations/easing/springs, imagery style and visual tokens belong to the project's canonical brand/design system, not this universal profile.

## Design ownership

Declare whether the design source of truth is Figma, code-first, in-repo design files or another explicit owner. Keep only key reference views necessary to communicate product intent; do not create a screenshot archive that drifts from production.

## Validation

Use component/state tests for deterministic behavior, E2E for critical complete journeys, accessibility automation plus manual checks where needed, visual regression for stable high-value surfaces where useful, and representative-user usability evidence for important/high-risk flows when justified.

A visually attractive happy-path screenshot is not sufficient evidence of a production-ready product experience.
