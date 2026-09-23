/**
 * Decisio UI Configuration & Theme Management
 */

const THEME_KEY = "decisio_theme";

const DEFAULT_CONFIG = {
  theme: {
    default: "dark",
    allow_toggle: true,
    pattern_background: true,
    accent: "emerald"
  },
  board: {
    snake_style: "brand-gradient",
    glow_effects: true,
    show_candidate_overlays: true,
    show_grid: true
  },
  gameplay: {
    default_hold_ms: 750,
    speed_presets: [100, 250, 500, 750, 1000, 1500]
  },
  panels: {
    show_model_io: true,
    show_decision_log: true,
    show_runtime_metrics: true,
    max_log_entries: 100
  },
  branding: {
    title: "Decisio Snake",
    mark_svg_light: "/decisio-mark.svg",
    mark_svg_dark: "/decisio-mark-dark.svg"
  }
};

let activeConfig = { ...DEFAULT_CONFIG };

export async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    if (res.ok) {
      const remote = await res.json();
      activeConfig = {
        ...DEFAULT_CONFIG,
        ...remote,
        theme: { ...DEFAULT_CONFIG.theme, ...(remote.theme || {}) },
        board: { ...DEFAULT_CONFIG.board, ...(remote.board || {}) },
        gameplay: { ...DEFAULT_CONFIG.gameplay, ...(remote.gameplay || {}) },
        panels: { ...DEFAULT_CONFIG.panels, ...(remote.panels || {}) },
        branding: { ...DEFAULT_CONFIG.branding, ...(remote.branding || {}) },
      };
    }
  } catch (err) {
    console.warn("Could not fetch /api/config, using default config:", err);
  }
  return activeConfig;
}

export function getConfig() {
  return activeConfig;
}

export function getInitialTheme() {
  const saved = localStorage.getItem(THEME_KEY);
  if (saved === "light" || saved === "dark") {
    return saved;
  }
  return activeConfig.theme?.default || "dark";
}

export function applyTheme(theme) {
  document.documentElement.dataset.theme = theme;
  localStorage.setItem(THEME_KEY, theme);

  // Update theme icons
  const sunIcon = document.getElementById("themeIconSun");
  const moonIcon = document.getElementById("themeIconMoon");
  if (sunIcon && moonIcon) {
    sunIcon.hidden = theme !== "dark";
    moonIcon.hidden = theme === "dark";
  }

  // Update brand mark logo based on theme
  const brandLogo = document.getElementById("brandLogo");
  if (brandLogo) {
    brandLogo.src = theme === "dark"
      ? (activeConfig.branding?.mark_svg_dark || "/decisio-mark-dark.svg")
      : (activeConfig.branding?.mark_svg_light || "/decisio-mark.svg");
  }

  // Trigger event for canvas redraw
  window.dispatchEvent(new CustomEvent("themechanged", { detail: { theme } }));
}

export function toggleTheme() {
  const current = document.documentElement.dataset.theme === "light" ? "light" : "dark";
  const next = current === "dark" ? "light" : "dark";
  applyTheme(next);
  return next;
}
