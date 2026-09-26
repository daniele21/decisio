from __future__ import annotations

import hashlib
from pathlib import Path

import pytest

import scripts.run_snake_demo as demo


def test_existing_custom_model_is_used_without_download(tmp_path: Path):
    model = tmp_path / "custom.gguf"
    model.write_bytes(b"custom")

    assert demo.ensure_demo_model(model) == model.resolve()


def test_missing_custom_model_is_rejected(tmp_path: Path):
    with pytest.raises(FileNotFoundError, match="model not found"):
        demo.ensure_demo_model(tmp_path / "missing.gguf")


def test_default_model_checksum_is_verified(monkeypatch, tmp_path: Path):
    model = tmp_path / demo.DEMO_MODEL_NAME
    model.write_bytes(b"bad")
    monkeypatch.setattr(demo, "DEFAULT_MODEL", model)

    with pytest.raises(RuntimeError, match="checksum mismatch"):
        demo.ensure_demo_model(model)


def test_download_stream_verifies_checksum(monkeypatch, tmp_path: Path):
    payload = b"demo-model"
    expected = hashlib.sha256(payload).hexdigest()

    class Response:
        def __init__(self):
            self._sent = False

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def read(self, size):
            del size
            if self._sent:
                return b""
            self._sent = True
            return payload

    monkeypatch.setattr(demo, "urlopen", lambda request: Response())
    monkeypatch.setattr(demo, "DEMO_MODEL_SHA256", expected)
    target = tmp_path / "model.gguf"

    demo._download("https://example.invalid/model.gguf", target)

    assert target.read_bytes() == payload
    assert not target.with_suffix(".gguf.part").exists()


def test_main_launches_snake_with_direct_scorer(monkeypatch, tmp_path: Path):
    model = tmp_path / "custom.gguf"
    model.write_bytes(b"custom")
    captured = {}

    def fake_call(command, cwd):
        captured["command"] = command
        captured["cwd"] = cwd
        return 0

    monkeypatch.setattr(demo.subprocess, "call", fake_call)

    assert demo.main(["--model", str(model), "--open", "--device", "cpu"]) == 0
    command = captured["command"]
    assert command[1:3] == ["-m", "examples.snake.web"]
    assert command[command.index("--model") + 1] == str(model.resolve())
    assert command[command.index("--scorer") + 1] == "direct"
    assert "--open" in command
    assert command[command.index("--device") + 1] == "cpu"
    assert captured["cwd"] == demo.REPO_ROOT
