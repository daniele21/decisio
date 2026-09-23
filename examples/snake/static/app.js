"use strict";

const DIRECTIONS = ["up", "right", "down", "left"];
const ARROWS = { up: "↑", right: "→", down: "↓", left: "←" };
const DELTAS = { up: [0, -1], right: [1, 0], down: [0, 1], left: [-1, 0] };

const $ = (selector) => document.querySelector(selector);
const ui = {
  board: $("#board"),
  toggle: $("#toggleBtn"),
  step: $("#stepBtn"),
  reset: $("#resetBtn"),
  hold: $("#holdRange"),
  holdLabel: $("#holdLabel"),
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
  requestJson: $("#requestJson"),
  responseJson: $("#responseJson"),
  overlay: $("#gameOverlay"),
  overlayTitle: $("#overlayTitle"),
  overlayText: $("#overlayText"),
};

let status = null;
let displayState = null;
let lastRecord = null;
let logRows = [];
let phase = "observe";
let running = false;
let busy = false;
let decidingStarted = null;
let decidingTicker = null;

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const formatMs = (seconds) => seconds == null ? "—" : `${Math.round(seconds * 1000)} ms`;
const formatPct = (value) => value == null ? "—" : `${(Number(value) * 100).toFixed(1)}%`;

function modelLabel(model) {
  if (!model) return "model";
  const name = model.artifact_filename || model.model || model.backend || "model";
  const quant = model.quantization ? ` · ${model.quantization}` : "";
  return `${name}${quant}`;
}

function runtimeLabel(model) {
  if (!model) return "—";
  const device = model.device || "local";
  const threads = model.n_threads
    ? `${model.n_threads}/${model.n_threads_batch || model.n_threads} threads`
    : "";
  return [device, threads].filter(Boolean).join(" · ");
}

function setPhase(next) {
  phase = next;
  document.querySelectorAll(".phase").forEach((node) => {
    node.classList.toggle("active", node.dataset.phase === next);
  });
  ui.phase.textContent = next;
}

function constraintsForView() {
  if (phase !== "observe" && lastRecord?.constraints) return lastRecord.constraints;
  return status?.constraints || lastRecord?.constraints || {
    safe_actions: [],
    filtered_actions: {},
  };
}

function decisionForView() {
  return lastRecord?.decision || null;
}

function updateRuntime() {
  const model = status?.model || lastRecord?.decision?.model || {};
  ui.modelBadge.textContent = modelLabel(model);
  ui.modelLine.textContent = modelLabel(model);
  ui.scorerLine.textContent = status?.scorer || lastRecord?.decision?.scorer || "—";
  ui.executionLine.textContent = runtimeLabel(model);
}

function renderMetrics() {
  const state = displayState || status?.state;
  if (state) {
    ui.score.textContent = String(state.score ?? status?.score ?? 0);
    ui.length.textContent = String(state.snake?.length ?? status?.snake_length ?? 0);
  }
  ui.move.textContent = String(status?.steps ?? 0);

  const decision = decisionForView();
  const metrics = lastRecord?.runtime_metrics || {};
  ui.latency.textContent = lastRecord ? formatMs(lastRecord.decision_latency_seconds) : "—";
  ui.roundtrip.textContent = lastRecord?.client_roundtrip_ms == null
    ? "—"
    : `${Math.round(lastRecord.client_roundtrip_ms)} ms`;
  ui.tokens.textContent = String(decision?.generated_tokens ?? 0);
  ui.reuse.textContent = metrics.reuse_ratio == null ? "—" : formatPct(metrics.reuse_ratio);

  const mode = lastRecord?.constraints?.mode;
  ui.modeBadge.textContent = mode === "model" ? "MODEL" : mode ? "RULE" : "LOCAL";
  ui.modeBadge.classList.toggle("subtle", mode !== "model");
}

function renderVerdict() {
  const decision = decisionForView();

  ui.verdict.classList.remove("idle", "deciding", "selected", "rule");
  if (busy && phase === "decide") {
    ui.verdict.classList.add("deciding");
    ui.verdictArrow.textContent = "···";
    ui.verdictTitle.textContent = "DECIDING…";
    const elapsed = decidingStarted == null
      ? 0
      : (performance.now() - decidingStarted) / 1000;
    ui.verdictSub.textContent = `${modelLabel(status?.model)} · ${elapsed.toFixed(1)} s elapsed`;
    return;
  }

  if (!decision) {
    ui.verdict.classList.add("idle");
    ui.verdictArrow.textContent = "·";
    ui.verdictTitle.textContent = "Waiting";
    ui.verdictSub.textContent = "Start the game or request one move.";
    return;
  }

  const mode = lastRecord?.constraints?.mode;
  ui.verdict.classList.add(mode === "model" ? "selected" : "rule");
  ui.verdictArrow.textContent = ARROWS[decision.choice] || "·";
  ui.verdictTitle.textContent = String(decision.choice).toUpperCase();

  if (mode === "model") {
    const preference = decision.distribution?.[decision.choice];
    ui.verdictSub.textContent =
      `${formatPct(preference)} relative preference · ${formatMs(lastRecord.decision_latency_seconds)}`;
  } else {
    ui.verdictSub.textContent = "Resolved by deterministic constraints · model not called";
  }
}

function renderChoices() {
  ui.choices.replaceChildren();
  const decision = decisionForView();
  const constraints = constraintsForView();
  const safe = new Set(constraints.safe_actions || []);
  const filtered = constraints.filtered_actions || {};

  DIRECTIONS.forEach((direction) => {
    const row = document.createElement("div");
    row.className = "choice";
    const selected = decision?.choice === direction;
    const isFiltered = Object.hasOwn(filtered, direction);
    if (selected) row.classList.add("selected");
    if (isFiltered) row.classList.add("filtered");

    const name = document.createElement("div");
    name.className = "choice-name";
    name.append(document.createTextNode(`${ARROWS[direction]} ${direction.toUpperCase()}`));
    const reason = document.createElement("small");
    if (isFiltered) reason.textContent = String(filtered[direction]).replaceAll("_", " ");
    else if (safe.has(direction)) reason.textContent = "candidate";
    else reason.textContent = "not supplied";
    name.append(reason);

    const track = document.createElement("div");
    track.className = "track";
    const fill = document.createElement("i");
    const probability = decision?.distribution?.[direction];
    fill.style.width = probability == null
      ? (safe.has(direction) ? "8%" : "0")
      : `${probability * 100}%`;
    track.append(fill);

    const value = document.createElement("div");
    value.className = "choice-value";
    if (isFiltered) value.textContent = "filtered";
    else if (busy && safe.has(direction) && phase === "decide") value.textContent = "…";
    else value.textContent = probability == null ? "—" : formatPct(probability);

    row.append(name, track, value);
    ui.choices.append(row);
  });
}

function renderConstraints() {
  ui.constraints.replaceChildren();
  const constraints = constraintsForView();
  const filtered = Object.entries(constraints.filtered_actions || {});
  if (!filtered.length) {
    const empty = document.createElement("span");
    empty.className = "muted";
    empty.textContent = "None — all legal directions remain candidates.";
    ui.constraints.append(empty);
    return;
  }

  filtered.forEach(([direction, reason]) => {
    const pill = document.createElement("span");
    pill.className = "constraint";
    pill.textContent = `${direction.toUpperCase()} · ${String(reason).replaceAll("_", " ")}`;
    ui.constraints.append(pill);
  });
}

function renderLog() {
  ui.logCount.textContent =
    `${logRows.length} ${logRows.length === 1 ? "move" : "moves"}`;
  ui.log.replaceChildren();
  if (!logRows.length) {
    const empty = document.createElement("div");
    empty.className = "empty";
    empty.textContent = "No decisions yet.";
    ui.log.append(empty);
    return;
  }

  logRows.slice(0, 60).forEach((record) => {
    const row = document.createElement("div");
    row.className = "log-row";

    const n = document.createElement("span");
    n.className = "n";
    n.textContent = `#${record.step}`;

    const move = document.createElement("span");
    move.className = "move";
    move.textContent =
      `${ARROWS[record.decision.choice] || "·"} ${record.decision.choice.toUpperCase()}`;

    const mode = document.createElement("span");
    mode.className = "mode";
    mode.textContent = record.constraints.mode === "model" ? "MODEL" : "RULE";

    const ms = document.createElement("span");
    ms.className = "ms";
    ms.textContent = formatMs(record.decision_latency_seconds);

    row.append(n, move, mode, ms);
    ui.log.append(row);
  });
}

function renderOverlay() {
  const alive = status?.alive !== false;
  const limit = status?.limit_reached === true;
  ui.overlay.hidden = alive && !limit;
  if (limit) {
    ui.overlayTitle.textContent = "Demo limit reached";
    ui.overlayText.textContent = "Reset to start another episode.";
  } else if (!alive) {
    ui.overlayTitle.textContent = "Game over";
    ui.overlayText.textContent = lastRecord?.outcome?.reason
      ? String(lastRecord.outcome.reason).replaceAll("_", " ")
      : "The episode ended.";
  }
}

function drawBoard() {
  const state = displayState || status?.state;
  if (!state) return;

  const canvas = ui.board;
  const cssSize = Math.max(300, Math.floor(canvas.clientWidth || 600));
  const dpr = window.devicePixelRatio || 1;
  const pixelSize = Math.round(cssSize * dpr);
  if (canvas.width !== pixelSize || canvas.height !== pixelSize) {
    canvas.width = pixelSize;
    canvas.height = pixelSize;
  }

  const ctx = canvas.getContext("2d");
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  ctx.clearRect(0, 0, cssSize, cssSize);

  const board = state.board;
  const cols = Number(board.width);
  const rows = Number(board.height);
  const pad = Math.max(20, cssSize * .055);
  const cell = Math.min((cssSize - pad * 2) / cols, (cssSize - pad * 2) / rows);
  const boardW = cell * cols;
  const boardH = cell * rows;
  const ox = (cssSize - boardW) / 2;
  const oy = (cssSize - boardH) / 2;

  ctx.fillStyle = "#f7fafc";
  ctx.fillRect(0, 0, cssSize, cssSize);
  ctx.fillStyle = "#ffffff";
  ctx.fillRect(ox, oy, boardW, boardH);
  ctx.strokeStyle = "#e1e9ee";
  ctx.lineWidth = 1;

  for (let x = 0; x <= cols; x += 1) {
    ctx.beginPath();
    ctx.moveTo(ox + x * cell, oy);
    ctx.lineTo(ox + x * cell, oy + boardH);
    ctx.stroke();
  }
  for (let y = 0; y <= rows; y += 1) {
    ctx.beginPath();
    ctx.moveTo(ox, oy + y * cell);
    ctx.lineTo(ox + boardW, oy + y * cell);
    ctx.stroke();
  }

  const body = state.snake.body_head_first || [];
  const head = body[0];
  const constraints = constraintsForView();
  const decision = decisionForView();
  const showCandidates = phase === "decide" || phase === "act";

  if (showCandidates && head) {
    for (const direction of constraints.safe_actions || []) {
      const [dx, dy] = DELTAS[direction];
      const tx = Number(head.x) + dx;
      const ty = Number(head.y) + dy;
      if (tx < 0 || ty < 0 || tx >= cols || ty >= rows) continue;
      const selected = decision?.choice === direction;
      ctx.fillStyle = selected ? "rgba(3,194,126,.20)" : "rgba(2,201,193,.09)";
      ctx.strokeStyle = selected ? "#03c27e" : "#8bded7";
      ctx.lineWidth = selected ? 3 : 1.5;
      const inset = 4;
      ctx.fillRect(
        ox + tx * cell + inset,
        oy + ty * cell + inset,
        cell - inset * 2,
        cell - inset * 2,
      );
      ctx.strokeRect(
        ox + tx * cell + inset,
        oy + ty * cell + inset,
        cell - inset * 2,
        cell - inset * 2,
      );

      const probability = decision?.distribution?.[direction];
      if (probability != null) {
        ctx.fillStyle = selected ? "#087b59" : "#506579";
        ctx.font = `700 ${Math.max(10, cell * .18)}px ui-monospace, SFMono-Regular, monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(
          formatPct(probability),
          ox + (tx + .5) * cell,
          oy + (ty + .5) * cell,
        );
      }
    }
  }

  const food = state.food;
  if (food) {
    const cx = ox + (Number(food.x) + .5) * cell;
    const cy = oy + (Number(food.y) + .5) * cell;
    ctx.beginPath();
    ctx.fillStyle = "#ef6c5b";
    ctx.arc(cx, cy, cell * .20, 0, Math.PI * 2);
    ctx.fill();
  }

  for (let index = body.length - 1; index >= 0; index -= 1) {
    const part = body[index];
    const x = ox + Number(part.x) * cell;
    const y = oy + Number(part.y) * cell;
    const inset = Math.max(3, cell * .09);
    const radius = Math.max(4, cell * .18);
    ctx.beginPath();
    ctx.roundRect(
      x + inset,
      y + inset,
      cell - inset * 2,
      cell - inset * 2,
      radius,
    );
    ctx.fillStyle = index === 0 ? "#112543" : "#03c27e";
    ctx.fill();
  }

  if (head) {
    const direction = state.snake.current_direction;
    const [dx, dy] = DELTAS[direction] || [1, 0];
    const cx = ox + (Number(head.x) + .5) * cell;
    const cy = oy + (Number(head.y) + .5) * cell;
    const sx = -dy;
    const sy = dx;
    ctx.fillStyle = "#ffffff";
    for (const side of [-1, 1]) {
      ctx.beginPath();
      ctx.arc(
        cx + dx * cell * .18 + side * sx * cell * .16,
        cy + dy * cell * .18 + side * sy * cell * .16,
        Math.max(2, cell * .045),
        0,
        Math.PI * 2,
      );
      ctx.fill();
    }
  }
}

function render() {
  updateRuntime();
  renderMetrics();
  renderVerdict();
  renderChoices();
  renderConstraints();
  renderLog();
  renderOverlay();
  drawBoard();

  ui.toggle.textContent = running ? "Pause" : "Start";
  ui.step.disabled = busy || running || !status?.alive || status?.limit_reached;
  ui.reset.disabled = busy;
}

function startTicker() {
  stopTicker();
  decidingTicker = window.setInterval(() => {
    if (busy && phase === "decide") renderVerdict();
  }, 100);
}

function stopTicker() {
  if (decidingTicker != null) {
    window.clearInterval(decidingTicker);
    decidingTicker = null;
  }
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    method: options.method || "GET",
    headers: { "content-type": "application/json" },
  });
  const value = await response.json();
  if (!response.ok) throw new Error(value.error || `HTTP ${response.status}`);
  return value;
}

async function oneMove() {
  if (busy || !status?.alive || status?.limit_reached) return;
  busy = true;
  setPhase("decide");
  lastRecord = null;
  decidingStarted = performance.now();
  startTicker();
  render();

  const requestStarted = performance.now();
  try {
    const record = await api("/api/step", { method: "POST" });
    const roundtrip = performance.now() - requestStarted;
    stopTicker();
    record.client_roundtrip_ms = roundtrip;
    lastRecord = record;
    displayState = record.before_state;
    ui.requestJson.textContent = JSON.stringify(record.request, null, 2);
    ui.responseJson.textContent = JSON.stringify({
      decision: record.decision,
      runtime_metrics: record.runtime_metrics,
      outcome: record.outcome,
    }, null, 2);
    render();

    await sleep(Number(ui.hold.value));
    setPhase("act");
    render();
    await sleep(260);

    status = record.status;
    displayState = record.after_state;
    logRows.unshift(record);
    setPhase("observe");
    render();
  } catch (error) {
    running = false;
    stopTicker();
    setPhase("observe");
    ui.verdict.classList.remove("deciding");
    ui.verdict.classList.add("idle");
    ui.verdictArrow.textContent = "!";
    ui.verdictTitle.textContent = "Request failed";
    ui.verdictSub.textContent = error.message;
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
  status = await api("/api/reset", { method: "POST" });
  displayState = status.state;
  lastRecord = null;
  logRows = [];
  ui.requestJson.textContent = "{}";
  ui.responseJson.textContent = "{}";
  setPhase("observe");
  render();
}

ui.toggle.addEventListener("click", () => {
  if (!status?.alive || status?.limit_reached) return;
  running = !running;
  render();
  if (running && !busy) oneMove();
});

ui.step.addEventListener("click", () => oneMove());
ui.reset.addEventListener("click", () => reset());
ui.hold.addEventListener("input", () => {
  ui.holdLabel.textContent = `${ui.hold.value} ms`;
});
window.addEventListener("resize", () => drawBoard());

(async () => {
  try {
    status = await api("/api/status");
    displayState = status.state;
    render();
  } catch (error) {
    ui.verdictArrow.textContent = "!";
    ui.verdictTitle.textContent = "Server unavailable";
    ui.verdictSub.textContent = error.message;
  }
})();
