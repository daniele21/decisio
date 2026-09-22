from __future__ import annotations

import pytest

from benchmarks.verify_llama_runtime_gate import _format_duration, _progress_line


def test_format_duration_is_stable_for_progress_output():
    assert _format_duration(0) == "00:00:00"
    assert _format_duration(65.4) == "00:01:05"
    assert _format_duration(3661.2) == "01:01:01"


def test_progress_line_reports_percent_elapsed_and_eta():
    assert _progress_line(
        stage="fixture",
        completed=16,
        total=64,
        label="running compare-privacy-delete",
        elapsed_seconds=160.0,
    ) == (
        "[fixture 16/64 |  25.0%] running compare-privacy-delete | "
        "elapsed 00:02:40 | ETA 00:08:00"
    )


def test_progress_line_handles_start_and_completion():
    assert _progress_line(
        stage="cache",
        completed=0,
        total=3,
        label="priming repeated-state cache",
        elapsed_seconds=0.0,
    ).endswith("elapsed 00:00:00 | ETA --:--:--")
    assert _progress_line(
        stage="cache",
        completed=3,
        total=3,
        label="complete",
        elapsed_seconds=12.0,
    ).endswith("elapsed 00:00:12 | ETA 00:00:00")


@pytest.mark.parametrize(
    ("completed", "total"),
    [(-1, 64), (65, 64), (0, 0)],
)
def test_progress_line_rejects_invalid_counts(completed: int, total: int):
    with pytest.raises(ValueError):
        _progress_line(
            stage="fixture",
            completed=completed,
            total=total,
            label="invalid",
            elapsed_seconds=0.0,
        )
