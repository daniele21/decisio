#!/usr/bin/env python3
"""Run the Snake demo with the pinned small GGUF, downloading it when needed."""

from __future__ import annotations

import argparse
import hashlib
import subprocess
import sys
from pathlib import Path
from urllib.request import Request, urlopen

DEMO_MODEL_NAME = "Qwen3.5-0.8B-Q4_K_M.gguf"
DEMO_MODEL_REVISION = "91840701981c3152e23662fa4416d7a93cab90e2"
DEMO_MODEL_SHA256 = "bd258782e35f7f458f8aced1adc053e6e92e89bc735ba3be89d38a06121dc517"
DEMO_MODEL_URL = (
    "https://huggingface.co/unsloth/Qwen3.5-0.8B-GGUF/resolve/"
    f"{DEMO_MODEL_REVISION}/{DEMO_MODEL_NAME}?download=true"
)
REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MODEL = REPO_ROOT / "models" / DEMO_MODEL_NAME


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _download(url: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_suffix(destination.suffix + ".part")
    partial.unlink(missing_ok=True)
    digest = hashlib.sha256()
    request = Request(url, headers={"User-Agent": "decisio-demo/0.1"})
    try:
        with urlopen(request) as response, partial.open("wb") as output:
            while chunk := response.read(1024 * 1024):
                output.write(chunk)
                digest.update(chunk)
    except Exception:
        partial.unlink(missing_ok=True)
        raise

    actual = digest.hexdigest()
    if actual != DEMO_MODEL_SHA256:
        partial.unlink(missing_ok=True)
        raise RuntimeError(
            "downloaded demo model checksum mismatch: "
            f"expected {DEMO_MODEL_SHA256}, got {actual}"
        )
    partial.replace(destination)


def ensure_demo_model(model: Path, *, force_download: bool = False) -> Path:
    model = model.expanduser().resolve()
    if model.exists() and not force_download:
        if model == DEFAULT_MODEL.resolve():
            actual = _sha256(model)
            if actual != DEMO_MODEL_SHA256:
                raise RuntimeError(
                    f"existing demo model checksum mismatch at {model}; "
                    "remove it or rerun with --force-download"
                )
        return model

    if model != DEFAULT_MODEL.resolve():
        raise FileNotFoundError(f"model not found: {model}")

    print(f"Downloading pinned demo model to {model}")
    _download(DEMO_MODEL_URL, model)
    return model


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Download the pinned small GGUF when needed and launch the local Snake UI."
    )
    parser.add_argument(
        "--model",
        type=Path,
        default=DEFAULT_MODEL,
        help="custom GGUF path; the pinned smoke model is downloaded only for the default path",
    )
    parser.add_argument(
        "--force-download",
        action="store_true",
        help="redownload the pinned default model after verifying the new artifact",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args, snake_args = parser.parse_known_args(argv)
    model = ensure_demo_model(args.model, force_download=args.force_download)
    command = [
        sys.executable,
        "-m",
        "examples.snake.web",
        "--model",
        str(model),
        "--scorer",
        "direct",
        *snake_args,
    ]
    return subprocess.call(command, cwd=REPO_ROOT)


if __name__ == "__main__":
    raise SystemExit(main())
