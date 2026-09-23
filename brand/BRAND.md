# Decisio brand kit

## Brand idea

The feather on wheels combines **lightness**, **motion** and **decision-making**. It should feel fast and intelligent rather than automotive: the feather is always the dominant idea, while the wheels and motion strokes communicate action.

## Logo system

- `assets/logos/decisio-mark.png` — primary symbol, transparent background.
- `assets/logos/decisio-logo-stacked.png` — primary stacked lockup, transparent background.
- `assets/logos/decisio-logo-horizontal.png` — horizontal lockup, transparent background.
- `*-for-dark.png` — color logo with white navy elements for dark backgrounds.
- `decisio-mark-monochrome-*.png` — single-color fallbacks.

The wordmark is supplied as artwork. Do not retype it when exact brand reproduction is required.

## Color

Primary brand gradient: `#03C27E` → `#02C9C1` → `#01C8F6`.

| Token | Hex | Use |
|---|---|---|
| Navy | `#112543` | Wordmark, wheels, primary text |
| Emerald | `#03C27E` | Gradient start, positive/accent |
| Teal | `#02C9C1` | Gradient midpoint |
| Azure | `#01C8F6` | Gradient end, energetic accent |
| Mint | `#65DFD5` | Secondary highlight |
| Ice | `#D2F2F1` | Soft surfaces / dividers |
| Off-white | `#F7FAFC` | Light brand surfaces |

## Typography

Recommended product/documentation stack: **Inter** (or the platform system sans fallback). For code and technical snippets use **JetBrains Mono**. These typefaces support the logo rather than replace the supplied wordmark artwork.

## Usage rules

- Keep clear space around the logo of at least **25% of the mark width**.
- Keep the standalone mark at **32 px or larger** for normal UI; use the prepared small icon exports below that size.
- Prefer white/off-white or deep navy backgrounds.
- Do not skew, rotate, outline, add shadows, or change the green→cyan gradient direction arbitrarily.
- Do not detach or reposition individual wheels/feather segments.
- For dark backgrounds use the provided `*-for-dark.png` variants.

## Ready-made digital assets

- `assets/icons/`: app icon and favicon-sized marks.
- `assets/graphics/github-social-preview-1280x640.jpg`: GitHub social preview.
- `assets/graphics/readme-hero-1600x500.jpg`: README/site hero.
- `assets/graphics/decisio-pattern.png`: supporting brand pattern.
- `tokens/brand.css` and `tokens/brand-tokens.json`: reusable product/design tokens.

## Production note

The approved master supplied here is raster artwork. For print, large-format use, or editable design-system components, redraw the approved geometry as true SVG/vector paths rather than auto-tracing a raster export.
