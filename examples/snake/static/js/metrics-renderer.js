/**
 * Metrics and Telemetry Renderer for Decisio Snake
 * Updates score, moves, latency, tokens, cache reuse, and phase progression.
 */

export const formatMs = (seconds) =>
  seconds == null ? "—" : `${Math.round(seconds * 1000)} ms`;

export const formatPct = (value) =>
  value == null ? "—" : `${(Number(value) * 100).toFixed(1)}%`;

export function modelLabel(model) {
  if (!model) return "model";
  const name = model.artifact_filename || model.model || model.backend || "model";
  const quant = model.quantization ? ` · ${model.quantization}` : "";
  return `${name}${quant}`;
}

export function scorerLabel(name) {
  if (name === "letter_question_prefix_v1") return "DIRECT CHOICE · reusable question prefix";
  if (name === "snake_adjacent_food_policy_v1") return "FOOD POLICY · model skipped";
  if (name === "letter_token_baseline_v1") return "DIRECT CHOICE · A/B/C logits · 1 forward";
  if (name === "semantic_comparative_logodds_v2") return "SEMANTIC v2 · YES/NO per candidate";
  if (name === "semantic_binary_logodds_v1") return "SEMANTIC v1 · YES/NO per candidate";
  if (name?.startsWith("deterministic_")) return "DETERMINISTIC · model skipped";
  return name || "—";
}

export function runtimeLabel(model) {
  if (!model) return "—";
  const device = model.device || "local";
  const threads = model.n_threads
    ? `${model.n_threads}/${model.n_threads_batch || model.n_threads} threads`
    : "";
  return [device, threads].filter(Boolean).join(" · ");
}

export function setPhase(ui, next) {
  document.querySelectorAll(".phase").forEach((node) => {
    node.classList.toggle("active", node.dataset.phase === next);
  });
  if (ui.phase) ui.phase.textContent = next;
}

export function updateRuntimeBadges(ui, status, lastRecord) {
  const model = status?.model || lastRecord?.decision?.model || {};
  if (ui.modelBadge) ui.modelBadge.textContent = modelLabel(model);
  if (ui.modelLine) ui.modelLine.textContent = modelLabel(model);
  if (ui.scorerLine) ui.scorerLine.textContent = scorerLabel(status?.scorer || lastRecord?.decision?.scorer);
  if (ui.executionLine) ui.executionLine.textContent = runtimeLabel(model);
}

export function renderMetrics(ui, displayState, status, lastRecord) {
  const state = displayState || status?.state;
  if (state) {
    if (ui.score) ui.score.textContent = String(state.score ?? status?.score ?? 0);
    if (ui.length) ui.length.textContent = String(state.snake?.length ?? status?.snake_length ?? 0);
  }
  if (ui.move) ui.move.textContent = String(status?.steps ?? 0);

  const decision = lastRecord?.decision || null;
  const metrics = lastRecord?.runtime_metrics || {};

  if (ui.latency) ui.latency.textContent = lastRecord ? formatMs(lastRecord.decision_latency_seconds) : "—";
  if (ui.roundtrip) {
    ui.roundtrip.textContent =
      lastRecord?.client_roundtrip_ms == null
        ? "—"
        : `${Math.round(lastRecord.client_roundtrip_ms)} ms`;
  }
  if (ui.tokens) ui.tokens.textContent = String(decision?.generated_tokens ?? 0);
  if (ui.reuse) ui.reuse.textContent = metrics.reuse_ratio == null ? "—" : formatPct(metrics.reuse_ratio);

  const mode = lastRecord?.constraints?.mode;
  const scorer = status?.scorer || lastRecord?.decision?.scorer;
  if (ui.modeBadge) {
    ui.modeBadge.textContent =
      mode === "model"
        ? scorer === "letter_token_baseline_v1"
          ? "DIRECT"
          : "MODEL"
        : mode
        ? "RULE"
        : "LOCAL";
    ui.modeBadge.classList.toggle("subtle", mode !== "model");
  }
}

export function renderSystemTelemetry(ui, status, config) {
  const sys = status?.system;
  const model = status?.model || {};

  if (ui.systemSection && config?.panels?.show_system_telemetry === false) {
    ui.systemSection.hidden = true;
  } else if (ui.systemSection) {
    ui.systemSection.hidden = false;
  }

  if (!sys) return;

  const showHost = Boolean(config?.telemetry?.show_hostname);
  const customHost = (config?.telemetry?.host_display_name || "").trim();

  // Header Host Badge: display hardware & memory, omitting private machine hostname by default
  if (ui.topbarHostText) {
    const chipShort = sys.chip ? sys.chip.replace("Apple ", "") : (sys.arch || "local");
    const memStr = sys.total_memory && sys.total_memory !== "N/A" ? ` · ${sys.total_memory}` : "";
    const hwInfo = `${chipShort}${memStr}`;

    if (showHost && sys.hostname) {
      ui.topbarHostText.textContent = `${sys.hostname} · ${hwInfo}`;
    } else if (customHost) {
      ui.topbarHostText.textContent = `${customHost} · ${hwInfo}`;
    } else {
      ui.topbarHostText.textContent = hwInfo;
    }
  }

  // System HUD items: display OS & architecture instead of raw machine hostname
  if (ui.sysHost) {
    if (showHost && sys.hostname) {
      ui.sysHost.textContent = sys.hostname;
    } else if (customHost) {
      ui.sysHost.textContent = customHost;
    } else {
      ui.sysHost.textContent = sys.os || "Local System";
    }
  }
  if (ui.sysOs) {
    if (showHost && sys.hostname) {
      ui.sysOs.textContent = `${sys.os || "OS"} · ${sys.arch || ""}`;
    } else {
      ui.sysOs.textContent = sys.arch ? `arch: ${sys.arch} · local` : "local runtime";
    }
  }
  if (ui.sysChip) ui.sysChip.textContent = sys.chip || sys.arch || "CPU";
  if (ui.sysCores) ui.sysCores.textContent = `${sys.cpu_count || 1} CPU cores`;
  if (ui.sysRam) {
    ui.sysRam.textContent =
      sys.total_memory && sys.total_memory !== "N/A"
        ? `${sys.total_memory} Total`
        : "Memory N/A";
  }
  if (ui.sysRss) ui.sysRss.textContent = `process RSS: ${sys.process_rss || "—"}`;

  const threads = model.n_threads
    ? `${model.n_threads}/${model.n_threads_batch || model.n_threads} threads`
    : "default threads";
  if (ui.sysThreads) ui.sysThreads.textContent = threads;
  if (ui.sysPid) ui.sysPid.textContent = `PID: ${sys.pid || "—"}`;

  if (ui.sysModelChip) ui.sysModelChip.textContent = modelLabel(model);
  if (ui.sysScorerChip) ui.sysScorerChip.textContent = status.scorer || "—";
  if (ui.sysBoardChip) {
    const w = status.width || 8;
    const h = status.height || 8;
    const seed = status.seed ?? 1;
    const fmt = status.input_format || "verbose";
    ui.sysBoardChip.textContent = `${w}×${h} · seed ${seed} · ${fmt}`;
  }
  if (ui.sysPyChip) ui.sysPyChip.textContent = `Python ${sys.python_version || ""}`;
}

