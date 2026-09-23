from pathlib import Path

from decisio.schema import DecisionResult
from examples.snake.web import SnakeSession


class FakeBackend:
    def __init__(self):
        self.identity = {
            "backend": "fake",
            "artifact_filename": "Qwen3.5-2B-Q4_K_M.gguf",
            "quantization": "Q4_K_M",
            "device": "cpu",
            "n_threads": 5,
            "n_threads_batch": 11,
        }
        self.closed = False
        self.resets = 0

    def reset_runtime_metrics(self):
        self.resets += 1

    def runtime_metrics(self):
        return {
            "reuse_ratio": 0.75,
            "repeated_state_cache_hits": 1,
            "repeated_state_cache_misses": 0,
        }

    def close(self):
        self.closed = True


class FakeScorer:
    name = "semantic_comparative_logodds_v2"

    def __init__(self):
        self.backend = FakeBackend()

    def score(self, request):
        count = len(request.candidates)
        choice = request.candidates[0].id
        probability = 1.0 / count
        distribution = {candidate.id: probability for candidate in request.candidates}
        scores = {candidate.id: float(count - index) for index, candidate in enumerate(request.candidates)}
        return DecisionResult(
            choice=choice,
            distribution=distribution,
            scores=scores,
            scorer=self.name,
            model=self.backend.identity,
        )


def test_snake_web_status_exposes_candidates_before_model():
    session = SnakeSession(
        scorer=FakeScorer(),
        seed=1,
        width=8,
        height=8,
        max_steps=10,
    )

    status = session.status()

    assert status["constraints"]["safe_actions"] == ["up", "right", "down"]
    assert status["constraints"]["filtered_actions"] == {"left": "reverse_direction"}
    assert status["model"]["n_threads"] == 5
    assert status["model"]["n_threads_batch"] == 11


def test_snake_web_step_returns_before_decision_after_and_runtime_metrics():
    scorer = FakeScorer()
    session = SnakeSession(
        scorer=scorer,
        seed=1,
        width=8,
        height=8,
        max_steps=10,
    )

    record = session.step()

    assert record["step"] == 1
    assert record["request"]["state"] == record["before_state"]
    assert record["decision"]["scorer"] == "semantic_comparative_logodds_v2"
    assert record["decision"]["generated_tokens"] == 0
    assert record["constraints"]["mode"] == "model"
    assert record["runtime_metrics"]["reuse_ratio"] == 0.75
    assert record["status"]["steps"] == 1
    assert record["after_state"] == record["status"]["state"]
    assert scorer.backend.resets == 1


def test_snake_web_trace_and_reset(tmp_path: Path):
    trace = tmp_path / "snake.jsonl"
    session = SnakeSession(
        scorer=FakeScorer(),
        seed=1,
        width=8,
        height=8,
        max_steps=10,
        trace=trace,
    )

    session.step()
    assert trace.read_text(encoding="utf-8").count("\n") == 1

    status = session.reset()

    assert status["steps"] == 0
    assert not trace.exists()


def test_snake_web_close_closes_backend():
    scorer = FakeScorer()
    session = SnakeSession(
        scorer=scorer,
        seed=1,
        width=8,
        height=8,
        max_steps=10,
    )

    session.close()

    assert scorer.backend.closed is True
