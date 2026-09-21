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


def _draw_board(draw: Any, state: dict[str, Any], *, x0: int, y0: int, size: int) -> None:
    board = state["board"]
    width = int(board["width"])
    height = int(board["height"])
    cell = min(size // width, size // height)
    board_w = cell * width
    board_h = cell * height

    draw.rounded_rectangle(
        (x0 - 8, y0 - 8, x0 + board_w + 8, y0 + board_h + 8),
        radius=16,
        fill="#111827",
        outline="#374151",
        width=2,
    )

    for gy in range(height):
        for gx in range(width):
            left = x0 + gx * cell
            top = y0 + gy * cell
            draw.rectangle(
                (left, top, left + cell, top + cell),
                fill="#0b1220",
                outline="#1f2937",
                width=1,
            )

    food = state.get("food")
    if food is not None:
        fx = int(food["x"])
        fy = int(food["y"])
        pad = max(4, cell // 5)
        left = x0 + fx * cell + pad
        top = y0 + fy * cell + pad
        draw.ellipse(
            (left, top, left + cell - 2 * pad, top + cell - 2 * pad),
            fill="#ef4444",
        )

    body = state["snake"]["body_head_first"]
    for index, part in enumerate(reversed(body)):
        px = int(part["x"])
        py = int(part["y"])
        is_head = index == len(body) - 1
        pad = max(3, cell // 10)
        left = x0 + px * cell + pad
        top = y0 + py * cell + pad
        fill = "#22c55e" if is_head else "#15803d"
        draw.rounded_rectangle(
            (left, top, left + cell - 2 * pad, top + cell - 2 * pad),
            radius=max(4, cell // 7),
            fill=fill,
        )


def _draw_probability_panel(
    draw: Any,
    *,
    distribution: dict[str, float],
    choice: str,
    x0: int,
    y0: int,
    width: int,
    font: Any,
    small_font: Any,
) -> None:
    draw.text((x0, y0), "Decision", font=font, fill="#f9fafb")
    y = y0 + 52
    ordered = sorted(distribution.items(), key=lambda item: item[1], reverse=True)
    for direction, probability in ordered:
        selected = direction == choice
        label = f"{direction.upper():<5} {probability:6.1%}"
        draw.text(
            (x0, y),
            label,
            font=small_font,
            fill="#f9fafb" if selected else "#d1d5db",
        )
        bar_y = y + 28
        bar_w = max(2, int((width - 20) * probability))
        draw.rounded_rectangle(
            (x0, bar_y, x0 + width - 20, bar_y + 16),
            radius=8,
            fill="#1f2937",
        )
        draw.rounded_rectangle(
            (x0, bar_y, x0 + bar_w, bar_y + 16),
            radius=8,
            fill="#60a5fa" if selected else "#4b5563",
        )
        y += 72


def render_frame(record: dict[str, Any], output: Path) -> None:
    Image, ImageDraw, ImageFont = _load_pillow()
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), "#030712")
    draw = ImageDraw.Draw(image)

    title_font = _font(ImageFont, 34, bold=True)
    heading_font = _font(ImageFont, 26, bold=True)
    body_font = _font(ImageFont, 20)
    small_font = _font(ImageFont, 18)

    request = record["request"]
    state = request["state"]
    decision = record["decision"]
    outcome = record["outcome"]
    constraints = record.get("constraints", {})
    latency = float(record.get("decision_latency_seconds", 0.0))

    draw.text((40, 28), "Decisio · Snake", font=title_font, fill="#f9fafb")
    draw.text(
        (40, 76),
        "Qwen scores semantic actions directly · zero generated answer tokens",
        font=body_font,
        fill="#9ca3af",
    )

    _draw_board(draw, state, x0=55, y0=135, size=520)

    panel_x = 650
    draw.text(
        (panel_x, 140),
        f"Step {record['step']}",
        font=heading_font,
        fill="#f9fafb",
    )
    draw.text(
        (panel_x, 184),
        f"Current direction: {state['snake']['current_direction'].upper()}",
        font=body_font,
        fill="#d1d5db",
    )
    food = state.get("food")
    food_text = "none" if food is None else f"({food['x']}, {food['y']})"
    draw.text(
        (panel_x, 218),
        f"Food: {food_text}   Score: {state['score']}",
        font=body_font,
        fill="#d1d5db",
    )

    filtered = constraints.get("filtered_actions", {})
    filtered_text = ", ".join(
        f"{direction.upper()}:{reason}" for direction, reason in filtered.items()
    ) or "none"
    draw.text(
        (panel_x, 252),
        f"Filtered before model: {filtered_text}",
        font=small_font,
        fill="#f59e0b",
    )

    _draw_probability_panel(
        draw,
        distribution=decision["distribution"],
        choice=decision["choice"],
        x0=panel_x,
        y0=292,
        width=520,
        font=heading_font,
        small_font=small_font,
    )

    status = "ALIVE" if outcome["alive"] else f"GAME OVER · {outcome['reason']}"
    status_fill = "#22c55e" if outcome["alive"] else "#ef4444"
    draw.text(
        (panel_x, 595),
        f"Applied move: {decision['choice'].upper()}",
        font=heading_font,
        fill="#60a5fa",
    )
    draw.text((panel_x, 635), status, font=body_font, fill=status_fill)
    draw.text(
        (panel_x, 666),
        f"decision latency: {latency:.3f}s · mode={constraints.get('mode', 'model')}",
        font=small_font,
        fill="#9ca3af",
    )
    draw.text(
        (40, 682),
        f"scorer={decision['scorer']} · generated_tokens={decision['generated_tokens']}",
        font=small_font,
        fill="#6b7280",
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
