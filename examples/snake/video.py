"""Render a Snake decision trace to an MP4 video artifact."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path
from typing import Any


def _load_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except ImportError as exc:  # pragma: no cover - CI/example environment dependent
        raise RuntimeError(
            "Snake video rendering requires Pillow: python -m pip install pillow"
        ) from exc
    return Image, ImageDraw, ImageFont


def load_trace(path: Path) -> list[dict[str, Any]]:
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    if not rows:
        raise ValueError("Snake trace is empty")
    return rows


def _font(ImageFont: Any, size: int, *, bold: bool = False):
    name = "DejaVuSans-Bold.ttf" if bold else "DejaVuSans.ttf"
    try:
        return ImageFont.truetype(name, size)
    except OSError:
        return ImageFont.load_default()


PALETTE = {
    "bg": "#f6f5f1",
    "panel": "#ffffff",
    "ink": "#1b1d1f",
    "muted": "#6a6f76",
    "line": "#dedcd5",
    "accent": "#0b8f6c",
    "accent_soft": "#dff3ec",
    "track": "#ebe9e2",
    "warn": "#b4540a",
    "warn_soft": "#fbead8",
    "bad": "#b3261e",
    "bad_soft": "#fbe3e1",
}

_DIRECTION_DELTAS = {
    "up": (0, -1),
    "right": (1, 0),
    "down": (0, 1),
    "left": (-1, 0),
}

_DIRECTION_ARROWS = {
    "up": "↑",
    "right": "→",
    "down": "↓",
    "left": "←",
}


def _text_size(draw: Any, text: str, font: Any) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _draw_card(
    draw: Any,
    box: tuple[int, int, int, int],
    *,
    fill: str = PALETTE["panel"],
    outline: str = PALETTE["line"],
    radius: int = 14,
) -> None:
    draw.rounded_rectangle(box, radius=radius, fill=fill, outline=outline, width=1)


def _draw_pill(
    draw: Any,
    text: str,
    *,
    x: int,
    y: int,
    font: Any,
    fill: str,
    ink: str,
    pad_x: int = 10,
    pad_y: int = 5,
) -> int:
    text_w, text_h = _text_size(draw, text, font)
    width = text_w + 2 * pad_x
    height = text_h + 2 * pad_y
    draw.rounded_rectangle(
        (x, y, x + width, y + height),
        radius=height // 2,
        fill=fill,
    )
    draw.text((x + pad_x, y + pad_y - 1), text, font=font, fill=ink)
    return width


def _draw_metric(
    draw: Any,
    *,
    x: int,
    y: int,
    width: int,
    value: str,
    label: str,
    value_font: Any,
    label_font: Any,
) -> None:
    _draw_card(
        draw,
        (x, y, x + width, y + 56),
        fill=PALETTE["bg"],
        radius=9,
    )
    draw.text((x + 10, y + 7), value, font=value_font, fill=PALETTE["ink"])
    draw.text((x + 10, y + 34), label, font=label_font, fill=PALETTE["muted"])


def _draw_board(
    draw: Any,
    state: dict[str, Any],
    *,
    distribution: dict[str, float],
    choice: str,
    x0: int,
    y0: int,
    size: int,
) -> None:
    board = state["board"]
    width = int(board["width"])
    height = int(board["height"])
    cell = min(size // (width + 2), size // (height + 2))
    board_w = cell * (width + 2)
    board_h = cell * (height + 2)

    draw.rectangle((x0, y0, x0 + board_w, y0 + board_h), fill=PALETTE["track"])
    inner_x = x0 + cell
    inner_y = y0 + cell
    draw.rectangle(
        (inner_x, inner_y, inner_x + cell * width, inner_y + cell * height),
        fill=PALETTE["panel"],
    )

    for gy in range(height + 1):
        y = inner_y + gy * cell
        draw.line(
            (inner_x, y, inner_x + cell * width, y),
            fill=PALETTE["line"],
            width=1,
        )
    for gx in range(width + 1):
        x = inner_x + gx * cell
        draw.line(
            (x, inner_y, x, inner_y + cell * height),
            fill=PALETTE["line"],
            width=1,
        )

    food = state.get("food")
    if food is not None:
        fx = int(food["x"])
        fy = int(food["y"])
        pad = max(4, cell // 5)
        left = inner_x + fx * cell + pad
        top = inner_y + fy * cell + pad
        draw.ellipse(
            (left, top, left + cell - 2 * pad, top + cell - 2 * pad),
            fill=PALETTE["bad"],
        )

    body = state["snake"]["body_head_first"]
    body_cells = [(int(part["x"]), int(part["y"])) for part in body]
    pad = max(3, cell // 10)
    for index in range(len(body_cells) - 1, -1, -1):
        px, py = body_cells[index]
        left = inner_x + px * cell + pad
        top = inner_y + py * cell + pad
        draw.rounded_rectangle(
            (left, top, left + cell - 2 * pad, top + cell - 2 * pad),
            radius=max(4, cell // 5),
            fill=PALETTE["accent"],
        )

    if body_cells:
        hx, hy = body_cells[0]
        direction = state["snake"]["current_direction"]
        dx, dy = _DIRECTION_DELTAS[direction]
        eye_r = max(2, cell // 14)
        cx = inner_x + hx * cell + cell // 2
        cy = inner_y + hy * cell + cell // 2
        side_x, side_y = -dy, dx
        for side in (-1, 1):
            ex = cx + int(dx * cell * 0.18 + side * side_x * cell * 0.17)
            ey = cy + int(dy * cell * 0.18 + side * side_y * cell * 0.17)
            draw.ellipse(
                (ex - eye_r, ey - eye_r, ex + eye_r, ey + eye_r),
                fill=PALETTE["panel"],
            )

        candidate_font = _font(_load_pillow()[2], max(11, cell // 4), bold=True)
        for direction, probability in distribution.items():
            dx, dy = _DIRECTION_DELTAS[direction]
            tx = hx + dx
            ty = hy + dy
            left = inner_x + tx * cell + 2
            top = inner_y + ty * cell + 2
            right = left + cell - 4
            bottom = top + cell - 4
            selected = direction == choice
            fill = PALETTE["accent_soft"] if selected else PALETTE["track"]
            outline = PALETTE["accent"] if selected else PALETTE["line"]
            draw.rounded_rectangle(
                (left, top, right, bottom),
                radius=max(4, cell // 6),
                fill=fill,
                outline=outline,
                width=2 if selected else 1,
            )
            label = f"{probability:.0%}"
            tw, th = _text_size(draw, label, candidate_font)
            draw.text(
                (left + (cell - 4 - tw) / 2, top + (cell - 4 - th) / 2 - 1),
                label,
                font=candidate_font,
                fill=PALETTE["accent"] if selected else PALETTE["ink"],
            )


def _draw_probability_panel(
    draw: Any,
    *,
    distribution: dict[str, float],
    choice: str,
    x0: int,
    y0: int,
    width: int,
    label_font: Any,
    value_font: Any,
) -> int:
    y = y0
    order = ("up", "left", "right", "down")
    for direction in order:
        if direction not in distribution:
            continue
        probability = float(distribution[direction])
        selected = direction == choice
        label = f"{_DIRECTION_ARROWS[direction]}  {direction.upper()}"
        draw.text(
            (x0, y),
            label,
            font=label_font,
            fill=PALETTE["ink"],
        )
        pct = f"{probability:.1%}"
        pct_w, _ = _text_size(draw, pct, value_font)
        draw.text(
            (x0 + width - pct_w, y + 1),
            pct,
            font=value_font,
            fill=PALETTE["accent"] if selected else PALETTE["muted"],
        )
        track_y = y + 28
        draw.rounded_rectangle(
            (x0, track_y, x0 + width, track_y + 11),
            radius=6,
            fill=PALETTE["track"],
        )
        bar_w = max(3, int(width * probability))
        draw.rounded_rectangle(
            (x0, track_y, x0 + bar_w, track_y + 11),
            radius=6,
            fill=PALETTE["accent"] if selected else PALETTE["muted"],
        )
        if selected:
            draw.rounded_rectangle(
                (x0 - 8, y - 6, x0 + width + 8, y + 47),
                radius=9,
                outline=PALETTE["accent_soft"],
                width=3,
            )
        y += 58
    return y


def _model_label(decision: dict[str, Any]) -> str:
    model = decision.get("model") or {}
    if not isinstance(model, dict):
        return "model"
    name = model.get("model") or model.get("backend") or "model"
    dtype = model.get("dtype")
    device = model.get("device")
    details = [str(name)]
    if dtype:
        details.append(str(dtype))
    if device:
        details.append(str(device))
    return " · ".join(details)


def render_frame(record: dict[str, Any], output: Path) -> None:
    Image, ImageDraw, ImageFont = _load_pillow()
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), PALETTE["bg"])
    draw = ImageDraw.Draw(image)

    title_font = _font(ImageFont, 24, bold=True)
    section_font = _font(ImageFont, 12, bold=True)
    verdict_font = _font(ImageFont, 24, bold=True)
    value_font = _font(ImageFont, 16, bold=True)
    body_font = _font(ImageFont, 15)
    small_font = _font(ImageFont, 12)

    request = record["request"]
    state = request["state"]
    decision = record["decision"]
    outcome = record["outcome"]
    constraints = record.get("constraints", {})
    latency = float(record.get("decision_latency_seconds", 0.0))
    distribution = {
        str(key): float(value) for key, value in decision["distribution"].items()
    }
    choice = str(decision["choice"])

    # Header: restrained product identity + runtime status, inspired by the Rizzo Flow
    # Snake information hierarchy without copying its page implementation.
    draw.rectangle((0, 0, width, 70), fill=PALETTE["panel"])
    draw.line((0, 69, width, 69), fill=PALETTE["line"], width=1)
    draw.text((28, 21), "Decisio", font=title_font, fill=PALETTE["ink"])
    title_w, _ = _text_size(draw, "Decisio", title_font)
    draw.text(
        (34 + title_w, 24),
        "snake",
        font=body_font,
        fill=PALETTE["muted"],
    )
    badge_text = _model_label(decision)
    badge_w = _draw_pill(
        draw,
        badge_text,
        x=800,
        y=19,
        font=small_font,
        fill=PALETTE["accent_soft"],
        ink=PALETTE["accent"],
    )
    mode_text = "MODEL" if constraints.get("mode") == "model" else "DETERMINISTIC"
    _draw_pill(
        draw,
        mode_text,
        x=min(width - 130, 814 + badge_w),
        y=19,
        font=small_font,
        fill=PALETTE["track"],
        ink=PALETTE["muted"],
    )

    left = (24, 88, 626, 696)
    right = (642, 88, 1256, 696)
    _draw_card(draw, left)
    _draw_card(draw, right)

    draw.text((42, 106), "GAME", font=section_font, fill=PALETTE["muted"])
    draw.text((660, 106), "MODEL DECISION", font=section_font, fill=PALETTE["muted"])

    _draw_board(
        draw,
        state,
        distribution=distribution,
        choice=choice,
        x0=78,
        y0=137,
        size=500,
    )

    metric_y = 624
    metric_w = 126
    metrics = [
        (str(outcome.get("game_score", state.get("score", 0))), "score"),
        (str(len(state["snake"]["body_head_first"])), "length"),
        (str(record["step"]), "move"),
        (f"{latency * 1000:.0f} ms" if latency else "0 ms", "decision"),
    ]
    for index, (value, label) in enumerate(metrics):
        _draw_metric(
            draw,
            x=42 + index * (metric_w + 10),
            y=metric_y,
            width=metric_w,
            value=value,
            label=label,
            value_font=value_font,
            label_font=small_font,
        )

    # Verdict first. Diagnostics sit below it.
    verdict_box = (660, 134, 1238, 218)
    verdict_fill = PALETTE["accent_soft"] if outcome["alive"] else PALETTE["bad_soft"]
    _draw_card(draw, verdict_box, fill=verdict_fill, outline=verdict_fill, radius=10)
    arrow = _DIRECTION_ARROWS.get(choice, "·")
    draw.text(
        (680, 148),
        arrow,
        font=_font(ImageFont, 42, bold=True),
        fill=PALETTE["accent"] if outcome["alive"] else PALETTE["bad"],
    )
    draw.text(
        (742, 149),
        choice.upper(),
        font=verdict_font,
        fill=PALETTE["ink"],
    )
    selected_p = distribution.get(choice, 1.0)
    draw.text(
        (742, 184),
        f"selected · {selected_p:.1%} relative score",
        font=small_font,
        fill=PALETTE["muted"],
    )

    bars_end = _draw_probability_panel(
        draw,
        distribution=distribution,
        choice=choice,
        x0=672,
        y0=244,
        width=540,
        label_font=body_font,
        value_font=small_font,
    )

    # Keep hard constraints visible, but secondary to the actual semantic decision.
    filtered = constraints.get("filtered_actions", {})
    y = min(475, bars_end + 8)
    draw.text((672, y), "CONSTRAINTS BEFORE MODEL", font=section_font, fill=PALETTE["muted"])
    y += 24
    if filtered:
        x = 672
        for direction, reason in filtered.items():
            pill = f"{str(direction).upper()} · {reason}"
            pill_w = _draw_pill(
                draw,
                pill,
                x=x,
                y=y,
                font=small_font,
                fill=PALETTE["warn_soft"],
                ink=PALETTE["warn"],
            )
            x += pill_w + 8
            if x > 1160:
                x = 672
                y += 30
    else:
        draw.text((672, y), "none", font=body_font, fill=PALETTE["muted"])

    info_y = 554
    draw.text((672, info_y), "EVIDENCE", font=section_font, fill=PALETTE["muted"])
    _draw_metric(
        draw,
        x=672,
        y=info_y + 22,
        width=164,
        value=f"{latency * 1000:.0f} ms" if latency else "0 ms",
        label="decision latency",
        value_font=value_font,
        label_font=small_font,
    )
    _draw_metric(
        draw,
        x=846,
        y=info_y + 22,
        width=164,
        value=str(decision.get("generated_tokens", 0)),
        label="generated tokens",
        value_font=value_font,
        label_font=small_font,
    )
    _draw_metric(
        draw,
        x=1020,
        y=info_y + 22,
        width=192,
        value="ALIVE" if outcome["alive"] else "GAME OVER",
        label=str(outcome.get("reason") or "after move"),
        value_font=value_font,
        label_font=small_font,
    )

    draw.text(
        (672, 650),
        f"scorer: {decision['scorer']}",
        font=small_font,
        fill=PALETTE["muted"],
    )
    draw.text(
        (672, 672),
        "Relative scores are uncalibrated; deterministic invalid moves are filtered first.",
        font=small_font,
        fill=PALETTE["muted"],
    )

    output.parent.mkdir(parents=True, exist_ok=True)
    image.save(output)

def render_video(
    trace_path: Path,
    output_path: Path,
    *,
    frames_dir: Path,
    fps: int = 1,
    hold_frames: int = 2,
) -> None:
    if fps < 1:
        raise ValueError("fps must be positive")
    if hold_frames < 1:
        raise ValueError("hold_frames must be positive")
    rows = load_trace(trace_path)
    frames_dir.mkdir(parents=True, exist_ok=True)

    frame_index = 0
    for record in rows:
        still = frames_dir / f"source-{record['step']:04d}.png"
        render_frame(record, still)
        for _ in range(hold_frames):
            target = frames_dir / f"frame-{frame_index:05d}.png"
            shutil.copyfile(still, target)
            frame_index += 1

    ffmpeg = shutil.which("ffmpeg")
    if ffmpeg is None:
        raise RuntimeError("ffmpeg is required to encode the Snake MP4")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [
            ffmpeg,
            "-y",
            "-framerate",
            str(fps),
            "-i",
            str(frames_dir / "frame-%05d.png"),
            "-c:v",
            "libx264",
            "-pix_fmt",
            "yuv420p",
            "-movflags",
            "+faststart",
            str(output_path),
        ],
        check=True,
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render a Decisio Snake trace to MP4")
    parser.add_argument("--trace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--frames-dir", type=Path, required=True)
    parser.add_argument("--fps", type=int, default=1)
    parser.add_argument("--hold-frames", type=int, default=2)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    render_video(
        args.trace,
        args.output,
        frames_dir=args.frames_dir,
        fps=args.fps,
        hold_frames=args.hold_frames,
    )
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
