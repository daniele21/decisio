import pytest

from decisio.schema import DecisionResult


def test_decision_result_rejects_fake_generation():
    with pytest.raises(ValueError, match="generated"):
        DecisionResult(
            choice="a",
            distribution={"a": 0.5, "b": 0.5},
            scores={"a": 1.0, "b": 1.0},
            scorer="test",
            generated_tokens=1,
        )


def test_decision_result_rejects_non_normalized_distribution():
    with pytest.raises(ValueError, match="sum to one"):
        DecisionResult(
            choice="a",
            distribution={"a": 0.9, "b": 0.9},
            scores={"a": 1.0, "b": 1.0},
            scorer="test",
        )
