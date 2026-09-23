from __future__ import annotations

import math

from scripts.diagnose_repeated_state import (
    _format_duration,
    _progress_line,
    _requests,
    _summary,
)


def test_repeated_state_diagnostic_uses_one_shared_state_and_four_candidates():
    rows = _requests()
    assert len(rows) == 8
    states = [request.state for request, _ in rows]
    assert all(state == states[0] for state in states)
    assert len({request.id for request, _ in rows}) == 8
    assert all(len(request.candidates) == 4 for request, _ in rows)
    assert all(
        "Which queue best matches this situation:" in request.question
        for request, _ in rows
    )
    assert all(
        request.id not in request.question
        for request, _ in rows
        if request.id is not None
    )
    assert {expected for _, expected in rows} == {
        "billing",
        "technical",
        "security",
        "sales",
    }


def test_latency_summary_is_deterministic():
    result = _summary([1.0, 2.0, 3.0, 4.0])
    assert result["mean"] == 2.5
    assert result["p50"] == 2.5
    assert math.isclose(result["p95"], 3.85)
    assert result["min"] == 1.0
    assert result["max"] == 4.0


def test_progress_line_reports_elapsed_and_eta():
    assert _format_duration(65.4) == "00:01:05"
    assert _progress_line(
        round_index=1,
        rounds=2,
        arm="semantic",
        completed=2,
        total=7,
        label="completed case-c in 00:00:18",
        elapsed_seconds=40.0,
    ) == (
        "[round 1/2] [semantic 2/7 |  28.6%] "
        "completed case-c in 00:00:18 | elapsed 00:00:40 | ETA 00:01:40"
    )


def test_progress_line_has_unknown_eta_before_first_measured_request():
    line = _progress_line(
        round_index=2,
        rounds=2,
        arm="generated",
        completed=0,
        total=7,
        label="warmup case-a",
        elapsed_seconds=3.0,
    )
    assert line.endswith("elapsed 00:00:03 | ETA --:--:--")
