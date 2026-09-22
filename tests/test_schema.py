import math

import pytest

from decisio.schema import Candidate, ChoiceRequest, DecisionResult


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


@pytest.mark.parametrize(
    "distribution",
    [
        {"a": 1.2, "b": -0.2},
        {"a": math.nan, "b": math.nan},
        {"a": math.inf, "b": 0.0},
    ],
)
def test_decision_result_rejects_invalid_distribution_values(distribution):
    with pytest.raises(ValueError, match="distribution values"):
        DecisionResult(
            choice="a",
            distribution=distribution,
            scores={"a": 1.0, "b": 0.0},
            scorer="test",
        )


def test_decision_result_rejects_non_finite_scores():
    with pytest.raises(ValueError, match="scores must be finite"):
        DecisionResult(
            choice="a",
            distribution={"a": 0.5, "b": 0.5},
            scores={"a": math.inf, "b": 0.0},
            scorer="test",
        )


def test_candidate_from_dict_does_not_coerce_none_to_text():
    with pytest.raises(ValueError, match="candidate id must be a string"):
        Candidate.from_dict({"id": None, "description": "valid"})


def test_choice_request_rejects_non_string_question():
    with pytest.raises(ValueError, match="question must be a string"):
        ChoiceRequest.from_dict(
            {
                "state": "x",
                "question": None,
                "candidates": [
                    {"id": "a", "description": "one"},
                    {"id": "b", "description": "two"},
                ],
            }
        )


def test_choice_request_rejects_non_json_state():
    with pytest.raises(ValueError, match="JSON-serializable"):
        ChoiceRequest(
            state={"bad": {1, 2}},
            question="choose",
            candidates=(Candidate("a", "one"), Candidate("b", "two")),
        )


def test_choice_request_rejects_duplicate_candidate_descriptions():
    with pytest.raises(ValueError, match="descriptions must be unique"):
        ChoiceRequest(
            state="x",
            question="choose",
            candidates=(Candidate("a", "same"), Candidate("b", "same")),
        )
