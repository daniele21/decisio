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
        (x0 - 7, y0 - 7, x0 + board_w + 7, y0 + board_h + 7),
        radius=14,
        fill="#f6f5f1",
        outline="#dedcd5",
        width=2,
    )

    for gy in range(height):
        for gx in range(width):
            left = x0 + gx * cell
            top = y0 + gy * cell
            draw.rectangle(
                (left, top, left + cell, top + cell),
                fill="#fbfaf7",
                outline="#e8e5dd",
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
            fill="#b3261e",
        )

    body = state["snake"]["body_head_first"]
    for index, part in enumerate(reversed(body)):
        px = int(part["x"])
        py = int(part["y"])
        is_head = index == len(body) - 1
        pad = max(3, cell // 10)
        left = x0 + px * cell + pad
        top = y0 + py * cell + pad
        fill = "#0b8f6c" if is_head else "#5bb59b"
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
    filtered_actions: dict[str, str],
    x0: int,
    y0: int,
    width: int,
    font: Any,
    small_font: Any,
) -> int:
    directions = ("up", "right", "down", "left")
    y = y0
    for direction in directions:
        filtered_reason = filtered_actions.get(direction)
        probability = distribution.get(direction)
        selected = direction == choice
        label = direction.upper()

        draw.text(
            (x0, y),
            label,
            font=small_font,
            fill="#1b1d1f" if filtered_reason is None else "#94918a",
        )

        if filtered_reason is not None:
            reason = filtered_reason.replace("_", " ")
            draw.rounded_rectangle(
                (x0 + 92, y - 1, x0 + width - 2, y + 23),
                radius=11,
                fill="#fbead8",
            )
            draw.text(
                (x0 + 104, y + 2),
                f"filtered · {reason}",
                font=small_font,
                fill="#b4540a",
            )
        else:
            track_left = x0 + 92
            track_right = x0 + width - 66
            track_top = y + 5
            track_bottom = y + 17
            draw.rounded_rectangle(
                (track_left, track_top, track_right, track_bottom),
                radius=6,
                fill="#ebe9e2",
            )
            bar_probability = float(probability or 0.0)
            fill_right = track_left + max(2, int((track_right - track_left) * bar_probability))
            draw.rounded_rectangle(
                (track_left, track_top, fill_right, track_bottom),
                radius=6,
                fill="#0b8f6c" if selected else "#8b918f",
            )
            draw.text(
                (x0 + width - 55, y),
                f"{bar_probability:5.1%}",
                font=small_font,
                fill="#0b8f6c" if selected else "#6a6f76",
            )
        y += 39
    return y
def render_frame(record: dict[str, Any], output: Path) -> None:
    Image, ImageDraw, ImageFont = _load_pillow()
    width, height = 1280, 720
    image = Image.new("RGB", (width, height), "#f6f5f1")
    draw = ImageDraw.Draw(image)

    title_font = _font(ImageFont, 28, bold=True)
    heading_font = _font(ImageFont, 20, bold=True)
    metric_font = _font(ImageFont, 17, bold=True)
    body_font = _font(ImageFont, 16)
    small_font = _font(ImageFont, 14)

    request = record["request"]
    state = request["state"]
    decision = record["decision"]
    outcome = record["outcome"]
    constraints = record.get("constraints", {})
    latency = float(record.get("decision_latency_seconds", 0.0))
    mode = str(constraints.get("mode", "model"))
    filtered = {
        str(direction): str(reason)
        for direction, reason in constraints.get("filtered_actions", {}).items()
    }

    draw.text((28, 23), "Decisio", font=title_font, fill="#1b1d1f")
    draw.text((130, 31), "snake", font=body_font, fill="#6a6f76")
    draw.rounded_rectangle((1058, 23, 1248, 52), radius=14, fill="#dff3ec")
    draw.text((1073, 30), "constraint-first decisions", font=small_font, fill="#0b8f6c")

    left = (28, 75, 620, 692)
    right = (640, 75, 1252, 692)
    for panel in (left, right):
        draw.rounded_rectangle(panel, radius=12, fill="#ffffff", outline="#dedcd5", width=2)

    draw.text((48, 96), "GAME", font=small_font, fill="#6a6f76")
    draw.text((660, 96), "MODEL DECISION", font=small_font, fill="#6a6f76")

    _draw_board(draw, state, x0=72, y0=132, size=500)

    score = int(outcome.get("game_score", state.get("score", 0)))
    metrics = [
        ("SCORE", str(score)),
        ("LENGTH", str(state["snake"]["length"])),
        ("STEP", str(record["step"])),
    ]
    metric_x = 48
    for label, value in metrics:
        draw.rounded_rectangle(
            (metric_x, 622, metric_x + 168, 673),
            radius=9,
            fill="#f6f5f1",
            outline="#e3e0d8",
        )
        draw.text((metric_x + 12, 632), value, font=metric_font, fill="#1b1d1f")
        draw.text((metric_x + 12, 654), label.lower(), font=small_font, fill="#6a6f76")
        metric_x += 181

    choice = str(decision["choice"]).upper()
    verdict_fill = "#dff3ec" if mode == "model" else "#ebe9e2"
    verdict_ink = "#0b8f6c" if mode == "model" else "#4d5358"
    draw.rounded_rectangle((660, 128, 1232, 210), radius=10, fill=verdict_fill)
    draw.text((680, 144), "→", font=_font(ImageFont, 42, bold=True), fill=verdict_ink)
    draw.text((738, 143), choice, font=title_font, fill="#1b1d1f")
    verdict_sub = (
        f"{decision['distribution'].get(decision['choice'], 1.0):.1%} relative preference"
        if mode == "model"
        else "resolved by deterministic constraints"
    )
    draw.text((738, 177), verdict_sub, font=small_font, fill="#6a6f76")

    bars_bottom = _draw_probability_panel(
        draw,
        distribution=decision["distribution"],
        choice=decision["choice"],
        filtered_actions=filtered,
        x0=680,
        y0=235,
        width=532,
        font=heading_font,
        small_font=small_font,
    )

    draw.text((680, bars_bottom + 7), "LAST DECISION", font=small_font, fill="#6a6f76")
    metric_cards = [
        ("latency", f"{latency * 1000:.0f} ms"),
        ("generated", str(decision.get("generated_tokens", 0))),
        ("mode", "model" if mode == "model" else "rule"),
    ]
    card_x = 680
    for label, value in metric_cards:
        draw.rounded_rectangle(
            (card_x, bars_bottom + 31, card_x + 164, bars_bottom + 84),
            radius=9,
            fill="#f6f5f1",
            outline="#e3e0d8",
        )
        draw.text((card_x + 11, bars_bottom + 41), value, font=metric_font, fill="#1b1d1f")
        draw.text((card_x + 11, bars_bottom + 64), label, font=small_font, fill="#6a6f76")
        card_x += 176

    status = "alive" if outcome["alive"] else f"game over · {outcome['reason']}"
    status_fill = "#dff3ec" if outcome["alive"] else "#fbe3e1"
    status_ink = "#0b8f6c" if outcome["alive"] else "#b3261e"
    draw.rounded_rectangle((680, 602, 1212, 641), radius=9, fill=status_fill)
    draw.text((694, 612), status, font=body_font, fill=status_ink)

    scorer = str(decision.get("scorer", "unknown"))
    draw.text(
        (680, 655),
        f"{scorer} · zero answer generation · probabilities are uncalibrated",
        font=small_font,
        fill="#6a6f76",
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
