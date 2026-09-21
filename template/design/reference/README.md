# Key product reference views

Use this directory only when `product-ui` is adopted and the project benefits from small in-repo visual references.

Keep a bounded set of intentional views, for example:

- primary/home surface;
- main working surface;
- critical settings/configuration surface;
- representative loading/empty/error states;
- a critical responsive/adaptive layout when useful.

Do not keep every iteration, generated visual-regression baseline, test screenshot or exported Figma frame here.

The canonical source of truth must be declared in `../ux-contract.json`. If Figma or the production design system is canonical, these files are supporting references only and should be refreshed or removed when stale.
