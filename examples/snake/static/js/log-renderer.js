/**
 * Interactive Decision Log Renderer for Decisio Snake
 */

import { formatMs } from "./metrics-renderer.js";

const ARROWS = { up: "↑", right: "→", down: "↓", left: "←" };

function make(tag, className = "", text = null) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text != null) node.textContent = String(text);
  return node;
}

function recordKey(record) {
  return record ? String(record.step) : "";
}

export function renderLog(ui, logRows, selectedRecord, onSelectRecord, maxEntries = 60) {
  if (ui.logCount) {
    ui.logCount.textContent = `${logRows.length} ${logRows.length === 1 ? "move" : "moves"}`;
  }
  if (ui.tabLogCount) {
    ui.tabLogCount.textContent = String(logRows.length);
  }
  if (!ui.log) return;
  ui.log.replaceChildren();

  if (!logRows.length) {
    ui.log.append(make("div", "empty", "No decisions yet."));
    return;
  }

  logRows.slice(0, maxEntries).forEach((record) => {
    const row = make("button", "log-row");
    row.type = "button";
    if (recordKey(selectedRecord) === recordKey(record)) {
      row.classList.add("selected-log");
    }

    const choice = record?.decision?.choice;
    const arrow = ARROWS[choice] || "·";
    const moveText = choice ? `${arrow} ${choice.toUpperCase()}` : "—";
    const mode = record?.constraints?.mode === "model" ? "MODEL" : "RULE";

    row.append(
      make("span", "n", `#${record.step}`),
      make("span", "move", moveText),
      make("span", "mode", mode),
      make("span", "ms", formatMs(record.decision_latency_seconds))
    );

    row.addEventListener("click", () => {
      if (typeof onSelectRecord === "function") {
        onSelectRecord(record);
      }
    });

    ui.log.append(row);
  });
}
