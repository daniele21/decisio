"use strict";

const DIRECTIONS = ["up", "right", "down", "left"];
const ARROWS = { up: "↑", right: "→", down: "↓", left: "←" };
const DELTAS = { up: [0, -1], right: [1, 0], down: [0, 1], left: [-1, 0] };
const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

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
  ioMoveLabel: $("#ioMoveLabel"),
  modelInput: $("#modelInput"),
  modelOutput: $("#modelOutput"),
  overlay: $("#gameOverlay"),
  overlayTitle: $("#overlayTitle"),
  overlayText: $("#overlayText"),
};

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
const formatMs = (seconds) => seconds == null ? "—" : `${Math.round(seconds * 1000)} ms`;
const formatPct = (value) => value == null ? "—" : `${(Number(value) * 100).toFixed(1)}%`;

function make(tag, className = "", text = null) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = String(text);
  return node;
}

function modelLabel(model) {
  if (!model) return "model";
  const name = model.artifact_filename || model.model || model.backend || "model";
  const quant = model.quantization ? ` · ${model.quantization}` : "";
  return `${name}${quant}`;
}

function scorerLabel(name) {
  if (name === "letter_question_prefix_v1") return "DIRECT CHOICE · reusable question prefix";
  if (name === "snake_adjacent_food_policy_v1") return "FOOD POLICY · model skipped";
  if (name === "letter_token_baseline_v1") return "DIRECT CHOICE · A/B/C logits · 1 forward";
  if (name === "semantic_comparative_logodds_v2") return "SEMANTIC v2 · YES/NO per candidate";
  if (name === "semantic_binary_logodds_v1") return "SEMANTIC v1 · YES/NO per candidate";
  if (name?.startsWith("deterministic_")) return "DETERMINISTIC · model skipped";
  return name || "—";
}

function skipReason(mode) {
  if (mode === "deterministic_adjacent_food_policy") {
    return "Adjacent-food policy: eat now with a safe next move available. Long-term safety is not guaranteed.";
  }
  if (mode === "deterministic_no_safe_action") return "No safe action remains.";
  return "Only one safe action remained, so the deterministic controller resolved the move.";
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

function currentConstraints() {
  if (lastRecord && (phase === "act" || selectedRecord === lastRecord)) {
    return lastRecord.constraints;
  }
  if (busy && status?.constraints) return status.constraints;
  return lastRecord?.constraints || status?.constraints || {
    safe_actions: [],
    candidate_features: {},
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
  ui.scorerLine.textContent = scorerLabel(status?.scorer || lastRecord?.decision?.scorer);
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
  const scorer = status?.scorer || lastRecord?.decision?.scorer;
  ui.modeBadge.textContent = mode === "model"
    ? (scorer === "letter_token_baseline_v1" ? "DIRECT" : "MODEL")
    : mode ? "RULE" : "LOCAL";
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
    ui.verdictSub.textContent = skipReason(mode);
  }
}

function featureSummary(features) {
  if (!features) return "candidate";
  const distance = features.food_distance_after == null
    ? "food ?"
    : `food ${features.food_progress} → d=${features.food_distance_after}`;
  return `${distance} · ${features.safe_moves_after} next · loop ${features.loop_risk}`;
}

function renderChoices() {
  ui.choices.replaceChildren();
  const decision = decisionForView();
  const constraints = currentConstraints();
  const safe = new Set(constraints.safe_actions || []);
  const filtered = constraints.filtered_actions || {};
  const features = constraints.candidate_features || {};

  DIRECTIONS.forEach((direction) => {
    const row = make("div", "choice");
    const selected = decision?.choice === direction;
    const isFiltered = Object.hasOwn(filtered, direction);
    if (selected) row.classList.add("selected");
    if (isFiltered) row.classList.add("filtered");

    const name = make("div", "choice-name");
    name.append(document.createTextNode(`${ARROWS[direction]} ${direction.toUpperCase()}`));
    const reason = make("small");
    if (isFiltered) reason.textContent = String(filtered[direction]).replaceAll("_", " ");
    else if (safe.has(direction)) reason.textContent = featureSummary(features[direction]);
    else reason.textContent = "not supplied";
    name.append(reason);

    const track = make("div", "track");
    const fill = make("i");
    const probability = decision?.distribution?.[direction];
    fill.style.width = probability == null
      ? (safe.has(direction) ? "8%" : "0")
      : `${probability * 100}%`;
    track.append(fill);

    const value = make("div", "choice-value");
    if (isFiltered) value.textContent = "filtered";
    else if (busy && safe.has(direction) && phase === "decide") value.textContent = "…";
    else value.textContent = probability == null ? "—" : formatPct(probability);

    row.append(name, track, value);
    ui.choices.append(row);
  });
}

function renderConstraints() {
  ui.constraints.replaceChildren();
  const filtered = Object.entries(currentConstraints().filtered_actions || {});
  if (!filtered.length) {
    ui.constraints.append(make("span", "muted", "None — all legal directions remain candidates."));
    return;
  }
  filtered.forEach(([direction, reason]) => {
    ui.constraints.append(
      make("span", "constraint", `${direction.toUpperCase()} · ${String(reason).replaceAll("_", " ")}`),
    );
  });
}

function recordKey(record) {
  return record ? String(record.step) : "";
}

function renderLog() {
  ui.logCount.textContent = `${logRows.length} ${logRows.length === 1 ? "move" : "moves"}`;
  ui.log.replaceChildren();
  if (!logRows.length) {
    ui.log.append(make("div", "empty", "No decisions yet."));
    return;
  }

  logRows.slice(0, 60).forEach((record) => {
    const row = make("button", "log-row");
    row.type = "button";
    if (recordKey(selectedRecord) === recordKey(record)) row.classList.add("selected-log");

    row.append(
      make("span", "n", `#${record.step}`),
      make("span", "move", `${ARROWS[record.decision.choice] || "·"} ${record.decision.choice.toUpperCase()}`),
      make("span", "mode", record.constraints.mode === "model" ? "MODEL" : "RULE"),
      make("span", "ms", formatMs(record.decision_latency_seconds)),
    );
    row.addEventListener("click", () => {
      selectedRecord = record;
      renderLog();
      renderInspector();
    });
    ui.log.append(row);
  });
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

function appendField(container, label, value, className = "") {
  const field = make("div", `io-field ${className}`.trim());
  field.append(make("span", "io-label", label), make("b", "io-value", value));
  container.append(field);
}

function positionText(value) {
  if (!value) return "—";
  return `(${value.x}, ${value.y})`;
}

function renderInputOption(candidate, index, features) {
  const card = make("div", "input-option");
  const heading = make("div", "input-option-head");
  heading.append(
    make("span", "option-slot", LETTERS[index] || "?"),
    make("b", "", String(candidate.id).toUpperCase()),
  );
  card.append(heading);
  card.append(make("p", "option-description", candidate.description));

  if (features) {
    const chips = make("div", "sensor-chips");
    const distance = features.food_distance_after == null
      ? "food distance ?"
      : `food ${features.food_progress}: ${features.food_distance_before} → ${features.food_distance_after}`;
    [
      distance,
      `${features.safe_moves_after} safe next`,
      `${features.reachable_free_cells_after} reachable`,
      `recent visits ${features.recent_visit_count}`,
      `loop ${features.loop_risk}`,
    ].forEach((value) => chips.append(make("span", `sensor ${features.loop_risk === "high" && value.startsWith("loop") ? "risk" : ""}`, value)));
    card.append(chips);
  }
  return card;
}

function renderModelInput(request, record) {
  ui.modelInput.replaceChildren();
  if (!request) {
    ui.modelInput.append(make("div", "empty", "No decision request available."));
    return;
  }

  const state = request.state || {};
  const snake = state.snake || {};
  const body = snake.body_head_first || [];
  const memory = state.decision_memory || {};
  const features = record?.constraints?.candidate_features
    || status?.constraints?.candidate_features
    || {};

  const question = make("div", "io-block");
  question.append(make("span", "io-label", "QUESTION"));
  question.append(make("p", "io-question", request.question || "—"));
  ui.modelInput.append(question);

  const stateGrid = make("div", "io-state-grid");
  appendField(stateGrid, "head", positionText(body[0]));
  appendField(stateGrid, "food", positionText(state.food));
  appendField(stateGrid, "direction", snake.current_direction || "—");
  appendField(stateGrid, "length", snake.length ?? body.length ?? "—");
  appendField(stateGrid, "score", state.score ?? "—");
  appendField(stateGrid, "steps since food", memory.steps_since_food ?? "—");
  ui.modelInput.append(stateGrid);

  if (Array.isArray(state.board_grid) && state.board_grid.length) {
    const gridBlock = make("div", "io-block");
    gridBlock.append(make("span", "io-label", "BOARD GRID · MODEL INPUT"));
    const pre = make("pre", "board-grid-text", state.board_grid.join("\n"));
    gridBlock.append(pre);
    ui.modelInput.append(gridBlock);
  }

  if (body.length) {
    const bodyBlock = make("div", "io-block");
    bodyBlock.append(make("span", "io-label", "BODY · HEAD FIRST"));
    bodyBlock.append(
      make("p", "body-path", body.map((point) => positionText(point)).join(" → ")),
    );
    ui.modelInput.append(bodyBlock);
  }

  const options = make("div", "io-block");
  options.append(make("span", "io-label", "OPTIONS SENT TO MODEL"));
  const optionList = make("div", "input-options");
  (request.candidates || []).forEach((candidate, index) => {
    optionList.append(renderInputOption(candidate, index, features[candidate.id]));
  });
  options.append(optionList);
  ui.modelInput.append(options);
}

function renderPreferenceRow(candidate, index, decision) {
  const row = make("div", "readout-row");
  const choice = candidate.id;
  const probability = decision.distribution?.[choice];
  const raw = decision.scores?.[choice];
  if (decision.choice === choice) row.classList.add("selected-readout");

  row.append(
    make("span", "option-slot", LETTERS[index] || "?"),
    make("b", "readout-name", String(choice).toUpperCase()),
  );
  const track = make("div", "mini-track");
  const fill = make("i");
  fill.style.width = probability == null ? "0" : `${probability * 100}%`;
  track.append(fill);
  row.append(track);
  row.append(make("span", "readout-prob", formatPct(probability)));
  row.append(make("span", "readout-logit", raw == null ? "logit —" : `logit ${Number(raw).toFixed(3)}`));
  return row;
}

function renderModelOutput(request, record) {
  ui.modelOutput.replaceChildren();
  if (!record) {
    const message = busy
      ? "Inference in progress. The input on the left is what the model is evaluating now."
      : "No model readout yet.";
    ui.modelOutput.append(make("div", "empty", message));
    return;
  }

  const decision = record.decision || {};
  const mode = record.constraints?.mode;
  if (mode !== "model") {
    const hero = make("div", "readout-hero");
    hero.append(make("span", "readout-kicker", "MODEL SKIPPED"));
    hero.append(make("strong", "", `${ARROWS[decision.choice] || "·"} ${String(decision.choice).toUpperCase()}`));
    hero.append(make("p", "", skipReason(mode)));
    ui.modelOutput.append(hero);
    return;
  }

  const candidates = request?.candidates || [];
  const selectedIndex = candidates.findIndex((candidate) => candidate.id === decision.choice);
  const selectedSlot = selectedIndex >= 0 ? LETTERS[selectedIndex] : "?";
  const hero = make("div", "readout-hero selected-output");
  hero.append(make("span", "readout-kicker", "SELECTED OPTION"));
  hero.append(
    make("strong", "", `${selectedSlot} · ${ARROWS[decision.choice] || "·"} ${String(decision.choice).toUpperCase()}`),
  );
  hero.append(
    make("p", "", `${formatPct(decision.distribution?.[decision.choice])} relative preference · no answer text generated`),
  );
  ui.modelOutput.append(hero);

  const rows = make("div", "readout-list");
  candidates.forEach((candidate, index) => rows.append(renderPreferenceRow(candidate, index, decision)));
  ui.modelOutput.append(rows);

  const metadata = make("div", "io-state-grid output-meta");
  appendField(metadata, "scorer", scorerLabel(decision.scorer));
  appendField(metadata, "latency", formatMs(record.decision_latency_seconds));
  appendField(metadata, "generated tokens", decision.generated_tokens ?? 0);
  appendField(metadata, "text output", "none");
  ui.modelOutput.append(metadata);
}

function renderInspector() {
  const request = inspectorRequest();
  const record = inspectorRecord();
  if (selectedRecord) ui.ioMoveLabel.textContent = `move #${selectedRecord.step}`;
  else if (busy) ui.ioMoveLabel.textContent = "deciding now";
  else if (lastRecord) ui.ioMoveLabel.textContent = `move #${lastRecord.step}`;
  else ui.ioMoveLabel.textContent = "next move";

  renderModelInput(request, record);
  renderModelOutput(request, record);
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
  const constraints = currentConstraints();
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
      ctx.fillRect(ox + tx * cell + inset, oy + ty * cell + inset, cell - inset * 2, cell - inset * 2);
      ctx.strokeRect(ox + tx * cell + inset, oy + ty * cell + inset, cell - inset * 2, cell - inset * 2);

      const probability = decision?.distribution?.[direction];
      if (probability != null) {
        ctx.fillStyle = selected ? "#087b59" : "#506579";
        ctx.font = `700 ${Math.max(10, cell * .18)}px ui-monospace, SFMono-Regular, monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.fillText(formatPct(probability), ox + (tx + .5) * cell, oy + (ty + .5) * cell);
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
    ctx.roundRect(x + inset, y + inset, cell - inset * 2, cell - inset * 2, radius);
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
  renderInspector();
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
  selectedRecord = null;
  activeRequest = status?.next_request || null;
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
    selectedRecord = record;
    displayState = record.before_state;
    render();

    await sleep(Number(ui.hold.value));
    setPhase("act");
    render();
    await sleep(260);

    status = record.status;
    activeRequest = status.next_request;
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
  activeRequest = status.next_request;
  lastRecord = null;
  selectedRecord = null;
  logRows = [];
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
    activeRequest = status.next_request;
    render();
  } catch (error) {
    ui.verdictArrow.textContent = "!";
    ui.verdictTitle.textContent = "Server unavailable";
    ui.verdictSub.textContent = error.message;
  }
})();
