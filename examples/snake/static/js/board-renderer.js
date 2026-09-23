/**
 * Canvas Board Renderer for Decisio Snake
 * Features: High-DPI scaling, brand gradient snake interpolation, glowing food, candidate move indicators.
 */

const DELTAS = { up: [0, -1], right: [1, 0], down: [0, 1], left: [-1, 0] };

// Color interpolation for Decisio Brand Gradient: Emerald (#03c27e) -> Teal (#02c9c1) -> Azure (#01c8f6)
function getSnakeSegmentColor(progress) {
  // progress from 0 (head) to 1 (tail)
  const clamped = Math.max(0, Math.min(1, progress));
  let r, g, b;

  if (clamped <= 0.52) {
    const t = clamped / 0.52;
    // #03c27e (3, 194, 126) -> #02c9c1 (2, 201, 193)
    r = Math.round(3 + (2 - 3) * t);
    g = Math.round(194 + (201 - 194) * t);
    b = Math.round(126 + (193 - 126) * t);
  } else {
    const t = (clamped - 0.52) / 0.48;
    // #02c9c1 (2, 201, 193) -> #01c8f6 (1, 200, 246)
    r = Math.round(2 + (1 - 2) * t);
    g = Math.round(201 + (200 - 201) * t);
    b = Math.round(193 + (246 - 193) * t);
  }

  return `rgb(${r}, ${g}, ${b})`;
}

export function drawBoard(canvas, state, constraints, decision, phase, config = {}) {
  if (!state || !canvas) return;

  const isDark = document.documentElement.dataset.theme !== "light";
  const cssSize = Math.max(300, Math.floor(canvas.clientWidth || 640));
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
  const pad = Math.max(18, cssSize * 0.05);
  const cell = Math.min((cssSize - pad * 2) / cols, (cssSize - pad * 2) / rows);
  const boardW = cell * cols;
  const boardH = cell * rows;
  const ox = (cssSize - boardW) / 2;
  const oy = (cssSize - boardH) / 2;

  // Board Background
  ctx.fillStyle = isDark ? "#070e1a" : "#f7fafc";
  ctx.fillRect(0, 0, cssSize, cssSize);

  // Playing Field Surface
  ctx.fillStyle = isDark ? "#0c182c" : "#ffffff";
  ctx.fillRect(ox, oy, boardW, boardH);

  // Subtle Grid Lines
  if (config.show_grid !== false) {
    ctx.strokeStyle = isDark ? "rgba(101, 223, 213, 0.08)" : "#e6eff4";
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
  }

  const body = state.snake?.body_head_first || [];
  const head = body[0];
  const showCandidates = phase === "decide" || phase === "act";

  // Candidate Safe Moves Overlays with Probabilities
  if (showCandidates && head && config.show_candidate_overlays !== false) {
    for (const direction of constraints?.safe_actions || []) {
      const [dx, dy] = DELTAS[direction] || [0, 0];
      const tx = Number(head.x) + dx;
      const ty = Number(head.y) + dy;
      if (tx < 0 || ty < 0 || tx >= cols || ty >= rows) continue;

      const selected = decision?.choice === direction;
      const inset = 3.5;
      const rx = ox + tx * cell + inset;
      const ry = oy + ty * cell + inset;
      const rw = cell - inset * 2;
      const rh = cell - inset * 2;

      ctx.fillStyle = selected
        ? (isDark ? "rgba(3, 194, 126, 0.28)" : "rgba(3, 194, 126, 0.18)")
        : (isDark ? "rgba(2, 201, 193, 0.12)" : "rgba(2, 201, 193, 0.08)");
      ctx.strokeStyle = selected ? "#03c27e" : (isDark ? "rgba(101, 223, 213, 0.5)" : "#8bded7");
      ctx.lineWidth = selected ? 2.5 : 1.5;

      ctx.beginPath();
      if (typeof ctx.roundRect === "function") {
        ctx.roundRect(rx, ry, rw, rh, Math.max(4, cell * 0.16));
      } else {
        ctx.rect(rx, ry, rw, rh);
      }
      ctx.fill();
      ctx.stroke();

      // Probability percentage label in candidate cell
      const probability = decision?.distribution?.[direction];
      if (probability != null) {
        ctx.fillStyle = selected
          ? (isDark ? "#48e3a8" : "#067c59")
          : (isDark ? "#8fa3b8" : "#506579");
        ctx.font = `700 ${Math.max(10, cell * 0.18)}px "JetBrains Mono", monospace`;
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        const pctText = `${(Number(probability) * 100).toFixed(1)}%`;
        ctx.fillText(pctText, ox + (tx + 0.5) * cell, oy + (ty + 0.5) * cell);
      }
    }
  }

  // Food Orb Rendering (Jewel Glow)
  const food = state.food;
  if (food) {
    const cx = ox + (Number(food.x) + 0.5) * cell;
    const cy = oy + (Number(food.y) + 0.5) * cell;
    const radius = cell * 0.22;

    // Outer Glow Halo
    const glowGradient = ctx.createRadialGradient(cx, cy, radius * 0.3, cx, cy, radius * 2.2);
    glowGradient.addColorStop(0, "rgba(255, 99, 132, 0.45)");
    glowGradient.addColorStop(1, "rgba(255, 99, 132, 0)");
    ctx.fillStyle = glowGradient;
    ctx.beginPath();
    ctx.arc(cx, cy, radius * 2.2, 0, Math.PI * 2);
    ctx.fill();

    // Food Core Orb
    const coreGradient = ctx.createRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 0.1, cx, cy, radius);
    coreGradient.addColorStop(0, "#ff8a9e");
    coreGradient.addColorStop(1, "#f43f5e");
    ctx.fillStyle = coreGradient;
    ctx.beginPath();
    ctx.arc(cx, cy, radius, 0, Math.PI * 2);
    ctx.fill();
  }

  // Snake Body Segments (Interpolated Brand Gradient)
  const totalParts = body.length;
  for (let index = totalParts - 1; index >= 0; index -= 1) {
    const part = body[index];
    const x = ox + Number(part.x) * cell;
    const y = oy + Number(part.y) * cell;
    const inset = Math.max(2.5, cell * 0.08);
    const radius = Math.max(4, cell * 0.20);

    const segmentProgress = totalParts > 1 ? index / (totalParts - 1) : 0;
    const segmentColor = getSnakeSegmentColor(segmentProgress);

    ctx.beginPath();
    if (typeof ctx.roundRect === "function") {
      ctx.roundRect(x + inset, y + inset, cell - inset * 2, cell - inset * 2, radius);
    } else {
      ctx.rect(x + inset, y + inset, cell - inset * 2, cell - inset * 2);
    }

    ctx.fillStyle = segmentColor;
    ctx.fill();

    // Subtle inner highlight on head
    if (index === 0) {
      ctx.strokeStyle = isDark ? "#65dfd5" : "#02c9c1";
      ctx.lineWidth = 1.5;
      ctx.stroke();
    }
  }

  // Snake Head Eyes (Tracking Direction)
  if (head) {
    const direction = state.snake?.current_direction || "right";
    const [dx, dy] = DELTAS[direction] || [1, 0];
    const cx = ox + (Number(head.x) + 0.5) * cell;
    const cy = oy + (Number(head.y) + 0.5) * cell;
    const sx = -dy;
    const sy = dx;

    const eyeRadius = Math.max(2.5, cell * 0.065);
    const pupilRadius = Math.max(1.2, cell * 0.035);

    for (const side of [-1, 1]) {
      const eyeX = cx + dx * cell * 0.18 + side * sx * cell * 0.17;
      const eyeY = cy + dy * cell * 0.18 + side * sy * cell * 0.17;

      // White Sclera
      ctx.fillStyle = "#ffffff";
      ctx.beginPath();
      ctx.arc(eyeX, eyeY, eyeRadius, 0, Math.PI * 2);
      ctx.fill();

      // Pupil Looking Forward
      ctx.fillStyle = "#112543";
      ctx.beginPath();
      ctx.arc(eyeX + dx * eyeRadius * 0.35, eyeY + dy * eyeRadius * 0.35, pupilRadius, 0, Math.PI * 2);
      ctx.fill();
    }
  }
}
