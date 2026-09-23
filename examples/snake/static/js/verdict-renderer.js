/**
 * Verdict and Candidate Choices Renderer for Decisio Snake
 * Displays verdict status, relative logodds preference bars, and pre-model constraints.
 */

import { formatMs, formatPct, modelLabel } from "./metrics-renderer.js";

const DIRECTIONS = ["up", "right", "down", "left"];
const ARROWS = { up: "↑", right: "→", down: "↓", left: "←" };

function make(tag, className = "", text = null) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = String(text);
  return node;
}

function skipReason(mode) {
  if (mode === "deterministic_adjacent_food_policy") {
    return "Adjacent-food policy: eat now with a safe next move available. Long-term safety is not guaranteed.";
  }
  if (mode === "deterministic_no_safe_action") return "No safe action remains.";
  return "Only one safe action remained, so the deterministic controller resolved the move.";
}

function featureSummary(features) {
  if (!features) return "candidate";
  const distance =
    features.food_distance_after == null
      ? "food ?"
      : `food ${features.food_progress} → d=${features.food_distance_after}`;
  return `${distance} · ${features.safe_moves_after} next · loop ${features.loop_risk}`;
}

export function renderVerdict(ui, busy, phase, decidingStarted, status, lastRecord) {
  const decision = lastRecord?.decision || null;
  ui.verdict.classList.remove("idle", "deciding", "selected", "rule");

  if (busy && phase === "decide") {
    ui.verdict.classList.add("deciding");
    ui.verdictArrow.textContent = "···";
    ui.verdictTitle.textContent = "DECIDING…";
    const elapsed = decidingStarted == null ? 0 : (performance.now() - decidingStarted) / 1000;
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
    ui.verdictSub.textContent = `${formatPct(preference)} relative preference · ${formatMs(
      lastRecord.decision_latency_seconds
    )}`;
  } else {
    ui.verdictSub.textContent = skipReason(mode);
  }
}

export function renderChoices(ui, constraints, decision, busy, phase) {
  ui.choices.replaceChildren();
  const safe = new Set(constraints?.safe_actions || []);
  const filtered = constraints?.filtered_actions || {};
  const features = constraints?.candidate_features || {};

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
    fill.style.width =
      probability == null
        ? safe.has(direction)
          ? "8%"
          : "0"
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

export function renderConstraints(ui, constraints) {
  ui.constraints.replaceChildren();
  const filtered = Object.entries(constraints?.filtered_actions || {});
  if (!filtered.length) {
    ui.constraints.append(make("span", "muted", "None — all legal directions remain candidates."));
    return;
  }
  filtered.forEach(([direction, reason]) => {
    ui.constraints.append(
      make("span", "constraint", `${direction.toUpperCase()} · ${String(reason).replaceAll("_", " ")}`)
    );
  });
}
