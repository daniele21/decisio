# Brand assets

When `product-ui` is adopted, place only durable canonical brand assets here **if this repository is their true owner**.

Typical assets may include:

- primary/compact/monochrome logo variants;
- app icon source/export when applicable;
- favicon source/export for browser products.

If Figma, an external brand repository or another design-system source is canonical, do not duplicate assets here unnecessarily. Point `../brand-kit.json` to the real owner or to the minimal checked-in assets the application actually consumes.

Never commit font binaries merely to complete the brand kit. Record typography families/tokens in `brand-kit.json` and manage licensed/system fonts through the project's normal dependency/asset policy.
