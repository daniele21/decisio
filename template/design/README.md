# Product design contract

This directory is used when the repository adopts the optional `product-ui` profile.

Canonical files:

- `ux-contract.json` — machine-readable product-experience semantics specialized for the project: users/jobs, decision order, hierarchy/disclosure, states, accessibility, adaptive behavior, motion purpose and graphics roles;
- `brand-kit.json` — semantic visual identity/design-token source used by the project or linked to the true design-system owner, including concrete motion language/tokens;
- `assets/` — durable brand assets only when this repository is their true owner;
- `reference/` — a bounded set of optional key product views, never generated regression history.

The project-local `skills/design-product-experience/SKILL.md` owns the recurring procedure for meaningful UX/UI changes. It keeps user outcome/task/IA/hierarchy ahead of components, motion and visual polish while scaling the depth of the process to the semantic impact of the change.

Keep only durable design truth and key reference views here. Do not accumulate exported screenshots, duplicate mockup revisions or generated design artifacts as a parallel source of truth.

The project must identify the canonical design owner (for example Figma, code-first design system or in-repo source files) in `ux-contract.json`.

`ux-contract.json` answers **what experience constraints and semantics apply**. `brand-kit.json` answers **how the product expresses them visually**, including typography, spacing, colors, iconography, imagery and motion values. Do not duplicate a stronger external/code design-system owner merely to populate these files.

If an external owner is canonical, these files act as a compact routing/contract layer rather than duplicating that system.

Generated regression screenshots/traces/videos belong in CI artifacts/evidence with bounded retention, not normal source history.
