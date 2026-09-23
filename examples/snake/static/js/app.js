/**
 * Decisio Snake Web App - Main Application Controller
 * Orchestrates the game loop, user interactions, telemetry updates, and component rendering.
 */

import { loadConfig, getConfig, getInitialTheme, applyTheme, toggleTheme } from "./config.js";
import { fetchStatus, postStep, postReset } from "./api.js";
import { drawBoard } from "./board-renderer.js";
import { setPhase, updateRuntimeBadges, renderMetrics, renderSystemTelemetry } from "./metrics-renderer.js";
import { renderVerdict, renderChoices, renderConstraints } from "./verdict-renderer.js";
import { renderLog } from "./log-renderer.js";
import { renderInspector, renderOverlay } from "./model-io-renderer.js";

const $ = (selector) => document.querySelector(selector);

// UI Element References
const ui = {
  board: $("#board"),
  toggle: $("#toggleBtn"),
  step: $("#stepBtn"),
  reset: $("#resetBtn"),
  hold: $("#holdRange"),
  holdLabel: $("#holdLabel"),
  themeToggle: $("#themeToggleBtn"),
  modelBadge: $("#modelBadge"),
  modeBadge: $("#modeBadge"),
  score: $("#scoreMetric"),
  length: $("#lengthMetric"),
  move: $("#moveMetric"),
  phase: $("#phaseMetric"),
  verdict: $("#verdict"),
  verdictArrow: $("#verdictArrow"),
  verdictTitle: $("#verdictTitle"),
  verdictSub: $("#verdictSub"),
  choices: $("#choices"),
  constraints: $("#constraints"),
  latency: $("#latencyMetric"),
  roundtrip: $("#roundtripMetric"),
  tokens: $("#tokensMetric"),
  reuse: $("#reuseMetric"),
  modelLine: $("#modelLine"),
  scorerLine: $("#scorerLine"),
  executionLine: $("#executionLine"),
  log: $("#decisionLog"),
  logCount: $("#logCount"),
  ioMoveLabel: $("#ioMoveLabel"),
  modelInput: $("#modelInput"),
  modelOutput: $("#modelOutput"),
  overlay: $("#gameOverlay"),
  overlayTitle: $("#overlayTitle"),
  overlayText: $("#overlayText"),
  topbarHostBadge: $("#topbarHostBadge"),
  topbarHostText: $("#topbarHostText"),
  systemSection: $("#systemSection"),
  sysHost: $("#sysHost"),
  sysOs: $("#sysOs"),
  sysChip: $("#sysChip"),
  sysCores: $("#sysCores"),
  sysRam: $("#sysRam"),
  sysRss: $("#sysRss"),
  sysThreads: $("#sysThreads"),
  sysPid: $("#sysPid"),
  sysModelChip: $("#sysModelChip"),
  sysScorerChip: $("#sysScorerChip"),
  sysBoardChip: $("#sysBoardChip"),
  sysPyChip: $("#sysPyChip"),
  tabLogCount: $("#tabLogCount"),
};

// Application State
let status = null;
let displayState = null;
let lastRecord = null;
let selectedRecord = null;
let activeRequest = null;
let logRows = [];
let phase = "observe";
let running = false;
let busy = false;
let decidingStarted = null;
let decidingTicker = null;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

function currentConstraints() {
  if (lastRecord && (phase === "act" || selectedRecord === lastRecord)) {
    return lastRecord.constraints;
  }
  if (busy && status?.constraints) return status.constraints;
  return (
    lastRecord?.constraints ||
    status?.constraints || {
      safe_actions: [],
      candidate_features: {},
      filtered_actions: {},
    }
  );
}

function inspectorRequest() {
  if (selectedRecord) return selectedRecord.request;
  if (busy && activeRequest) return activeRequest;
  if (lastRecord) return lastRecord.request;
  return status?.next_request || null;
}

function inspectorRecord() {
  return selectedRecord || lastRecord || null;
}

function render() {
  const config = getConfig();
  updateRuntimeBadges(ui, status, lastRecord);
  renderMetrics(ui, displayState, status, lastRecord);
  renderSystemTelemetry(ui, status, config);
  renderVerdict(ui, busy, phase, decidingStarted, status, lastRecord);
  renderChoices(ui, currentConstraints(), lastRecord?.decision || null, busy, phase);
  renderConstraints(ui, currentConstraints());

  renderLog(ui, logRows, selectedRecord, (record) => {
    selectedRecord = record;
    renderLog(ui, logRows, selectedRecord, (r) => { selectedRecord = r; render(); });
    renderInspector(ui, inspectorRequest(), inspectorRecord(), busy, status, selectedRecord, lastRecord);
  }, config.panels?.max_log_entries || 60);

  renderInspector(ui, inspectorRequest(), inspectorRecord(), busy, status, selectedRecord, lastRecord);
  renderOverlay(ui, status, lastRecord);

  const boardState = displayState || status?.state;
  drawBoard(ui.board, boardState, currentConstraints(), lastRecord?.decision || null, phase, config.board);

  if (ui.toggle) ui.toggle.textContent = running ? "Pause" : "Start";
  if (ui.step) ui.step.disabled = busy || running || !status?.alive || status?.limit_reached;
  if (ui.reset) ui.reset.disabled = busy;
}

function startTicker() {
  stopTicker();
  decidingTicker = window.setInterval(() => {
    if (busy && phase === "decide") {
      renderVerdict(ui, busy, phase, decidingStarted, status, lastRecord);
    }
  }, 100);
}

function stopTicker() {
  if (decidingTicker != null) {
    window.clearInterval(decidingTicker);
    decidingTicker = null;
  }
}

async function oneMove() {
  if (busy || !status?.alive || status?.limit_reached) return;
  busy = true;
  selectedRecord = null;
  activeRequest = status?.next_request || null;
  setPhase(ui, "decide");
  phase = "decide";
  lastRecord = null;
  decidingStarted = performance.now();
  startTicker();
  render();

  try {
    const record = await postStep();
    stopTicker();
    lastRecord = record;
    selectedRecord = record;
    displayState = record.before_state;
    render();

    const holdMs = ui.hold ? Number(ui.hold.value) : 750;
    await sleep(holdMs);
    setPhase(ui, "act");
    phase = "act";
    render();
    await sleep(260);

    status = record.status;
    activeRequest = status.next_request;
    displayState = record.after_state;
    logRows.unshift(record);
    setPhase(ui, "observe");
    phase = "observe";
    render();
  } catch (error) {
    running = false;
    stopTicker();
    setPhase(ui, "observe");
    phase = "observe";
    if (ui.verdict) {
      ui.verdict.classList.remove("deciding");
      ui.verdict.classList.add("idle");
    }
    if (ui.verdictArrow) ui.verdictArrow.textContent = "!";
    if (ui.verdictTitle) ui.verdictTitle.textContent = "Request failed";
    if (ui.verdictSub) ui.verdictSub.textContent = error.message;
  } finally {
    busy = false;
    decidingStarted = null;
    render();
  }

  if (running && status?.alive && !status?.limit_reached) {
    await sleep(120);
    if (running) oneMove();
  } else if (!status?.alive || status?.limit_reached) {
    running = false;
    render();
  }
}

async function reset() {
  if (busy) return;
  running = false;
  try {
    status = await postReset();
    displayState = status.state;
    activeRequest = status.next_request;
    lastRecord = null;
    selectedRecord = null;
    logRows = [];
    setPhase(ui, "observe");
    phase = "observe";
    render();
  } catch (error) {
    console.error("Reset error:", error);
  }
}

// Event Bindings
if (ui.toggle) {
  ui.toggle.addEventListener("click", () => {
    if (!status?.alive || status?.limit_reached) return;
    running = !running;
    render();
    if (running && !busy) oneMove();
  });
}

if (ui.step) ui.step.addEventListener("click", () => oneMove());
if (ui.reset) ui.reset.addEventListener("click", () => reset());

if (ui.hold) {
  ui.hold.addEventListener("input", () => {
    if (ui.holdLabel) ui.holdLabel.textContent = `${ui.hold.value} ms`;
  });
}

if (ui.themeToggle) {
  ui.themeToggle.addEventListener("click", () => {
    toggleTheme();
  });
}

window.addEventListener("resize", () => {
  const boardState = displayState || status?.state;
  drawBoard(ui.board, boardState, currentConstraints(), lastRecord?.decision || null, phase, getConfig().board);
});

window.addEventListener("themechanged", () => {
  render();
});

function initTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanes = document.querySelectorAll(".tab-pane");

  tabButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const targetId = btn.dataset.tab;
      if (!targetId) return;

      tabButtons.forEach((b) => {
        const isActive = b === btn;
        b.classList.toggle("active", isActive);
        b.setAttribute("aria-selected", isActive ? "true" : "false");
      });

      tabPanes.forEach((pane) => {
        pane.classList.toggle("active", pane.id === targetId);
      });
    });
  });
}

// Bootstrap Application
(async () => {
  const config = await loadConfig();
  const theme = getInitialTheme();
  applyTheme(theme);
  initTabs();

  if (config.gameplay?.default_hold_ms && ui.hold) {
    ui.hold.value = config.gameplay.default_hold_ms;
    if (ui.holdLabel) ui.holdLabel.textContent = `${config.gameplay.default_hold_ms} ms`;
  }

  try {
    status = await fetchStatus();
    displayState = status.state;
    activeRequest = status.next_request;
    render();
  } catch (error) {
    if (ui.verdictArrow) ui.verdictArrow.textContent = "!";
    if (ui.verdictTitle) ui.verdictTitle.textContent = "Server unavailable";
    if (ui.verdictSub) ui.verdictSub.textContent = error.message;
  }
})();
