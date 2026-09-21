from pathlib import Path

import pytest

from examples.snake.video import load_trace


def test_snake_video_trace_loader_rejects_empty_file(tmp_path: Path):
    path = tmp_path / "empty.jsonl"
    path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        load_trace(path)


def test_snake_video_trace_loader_reads_records(tmp_path: Path):
    path = tmp_path / "trace.jsonl"
    path.write_text('{"step": 1}\n{"step": 2}\n', encoding="utf-8")
    rows = load_trace(path)
    assert [row["step"] for row in rows] == [1, 2]
