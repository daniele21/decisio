/**
 * Model I/O Inspector and Game Overlay Renderer for Decisio Snake
 */

import { formatMs, formatPct, scorerLabel } from "./metrics-renderer.js";

const ARROWS = { up: "↑", right: "→", down: "↓", left: "←" };
const LETTERS = "ABCDEFGHIJKLMNOPQRSTUVWXYZ";

function make(tag, className = "", text = null) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = String(text);
  return node;
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

function skipReason(mode) {
  if (mode === "deterministic_adjacent_food_policy") {
    return "Adjacent-food policy: eat now with a safe next move available. Long-term safety is not guaranteed.";
  }
  if (mode === "deterministic_no_safe_action") return "No safe action remains.";
  return "Only one safe action remained, so the deterministic controller resolved the move.";
}

function renderInputOption(candidate, index, features) {
  const card = make("div", "input-option");
  const heading = make("div", "input-option-head");
  heading.append(
    make("span", "option-slot", LETTERS[index] || "?"),
    make("b", "", String(candidate.id).toUpperCase())
  );
  card.append(heading);
  card.append(make("p", "option-description", candidate.description));

  if (features) {
    const chips = make("div", "sensor-chips");
    const distance =
      features.food_distance_after == null
        ? "food distance ?"
        : `food ${features.food_progress}: ${features.food_distance_before} → ${features.food_distance_after}`;
    [
      distance,
      `${features.safe_moves_after} safe next`,
      `${features.reachable_free_cells_after} reachable`,
      `recent visits ${features.recent_visit_count}`,
      `loop ${features.loop_risk}`,
    ].forEach((value) =>
      chips.append(
        make(
          "span",
          `sensor ${features.loop_risk === "high" && value.startsWith("loop") ? "risk" : ""}`,
          value
        )
      )
    );
    card.append(chips);
  }
  return card;
}

function renderModelInput(ui, request, record, status) {
  if (!ui.modelInput) return;
  ui.modelInput.replaceChildren();

  if (!request) {
    ui.modelInput.append(make("div", "empty", "No decision request available."));
    return;
  }

  const state = request.state || {};
  const snake = state.snake || {};
  const body = snake.body_head_first || [];
  const memory = state.decision_memory || {};
  const features =
    record?.constraints?.candidate_features ||
    status?.constraints?.candidate_features ||
    {};

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
      make("p", "body-path", body.map((point) => positionText(point)).join(" → "))
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
    make("b", "readout-name", String(choice).toUpperCase())
  );
  const track = make("div", "mini-track");
  const fill = make("i");
  fill.style.width = probability == null ? "0" : `${probability * 100}%`;
  track.append(fill);
  row.append(track);
  row.append(make("span", "readout-prob", formatPct(probability)));
  row.append(
    make("span", "readout-logit", raw == null ? "logit —" : `logit ${Number(raw).toFixed(3)}`)
  );
  return row;
}

function renderModelOutput(ui, request, record, busy) {
  if (!ui.modelOutput) return;
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
    hero.append(
      make("strong", "", `${ARROWS[decision.choice] || "·"} ${String(decision.choice).toUpperCase()}`)
    );
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
    make(
      "strong",
      "",
      `${selectedSlot} · ${ARROWS[decision.choice] || "·"} ${String(decision.choice).toUpperCase()}`
    )
  );
  hero.append(
    make(
      "p",
      "",
      `${formatPct(decision.distribution?.[decision.choice])} relative preference · no answer text generated`
    )
  );
  ui.modelOutput.append(hero);

  const rows = make("div", "readout-list");
  candidates.forEach((candidate, index) =>
    rows.append(renderPreferenceRow(candidate, index, decision))
  );
  ui.modelOutput.append(rows);

  const metadata = make("div", "io-state-grid output-meta");
  appendField(metadata, "scorer", scorerLabel(decision.scorer));
  appendField(metadata, "latency", formatMs(record.decision_latency_seconds));
  appendField(metadata, "generated tokens", decision.generated_tokens ?? 0);
  appendField(metadata, "text output", "none");
  ui.modelOutput.append(metadata);
}

export function renderInspector(ui, request, record, busy, status, selectedRecord, lastRecord) {
  if (ui.ioMoveLabel) {
    if (selectedRecord) ui.ioMoveLabel.textContent = `move #${selectedRecord.step}`;
    else if (busy) ui.ioMoveLabel.textContent = "deciding now";
    else if (lastRecord) ui.ioMoveLabel.textContent = `move #${lastRecord.step}`;
    else ui.ioMoveLabel.textContent = "next move";
  }

  renderModelInput(ui, request, record, status);
  renderModelOutput(ui, request, record, busy);
}

export function renderOverlay(ui, status, lastRecord) {
  if (!ui.overlay) return;
  const alive = status?.alive !== false;
  const limit = status?.limit_reached === true;
  ui.overlay.hidden = alive && !limit;

  if (limit) {
    if (ui.overlayTitle) ui.overlayTitle.textContent = "Demo limit reached";
    if (ui.overlayText) ui.overlayText.textContent = "Reset to start another episode.";
  } else if (!alive) {
    if (ui.overlayTitle) ui.overlayTitle.textContent = "Game over";
    if (ui.overlayText) {
      ui.overlayText.textContent = lastRecord?.outcome?.reason
        ? String(lastRecord.outcome.reason).replaceAll("_", " ")
        : "The episode ended.";
    }
  }
}
