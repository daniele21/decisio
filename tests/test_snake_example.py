from examples.snake.game import SnakeGame
from examples.snake.play import build_parser, build_request, choose_move


class NeverCalledScorer:
    def score(self, request):
        raise AssertionError(f"model should not be called for request {request}")


def test_snake_request_contains_only_immediately_safe_actions():
    game = SnakeGame(seed=1)
    game.food = (4, 2)
    request = build_request(game)
    ids = {candidate.id for candidate in request.candidates}
    assert ids == {"up", "right", "down"}
    assert "left" not in ids
    descriptions = {candidate.id: candidate.description for candidate in request.candidates}
    assert descriptions["up"].startswith("Move UP to (x=4, y=3).")
    assert descriptions["right"].startswith("Move RIGHT to (x=5, y=4).")
    assert descriptions["down"].startswith("Move DOWN to (x=4, y=5).")
    assert "Food progress: closer; Manhattan distance 2 -> 1" in descriptions["up"]
    assert "Food progress: farther; Manhattan distance 2 -> 3" in descriptions["down"]
    assert "Future mobility:" in descriptions["up"]
    assert "board_grid" in request.state
    assert len(request.state["board_grid"]) > 0


def test_snake_filters_wall_collision_before_model():
    game = SnakeGame(width=5, height=5, seed=1)
    game.snake = [(4, 2), (3, 2), (2, 2)]
    game.direction = "right"
    assert game.immediate_failure_reason("right") == "wall_collision"
    assert "right" not in game.safe_directions()


def test_snake_filters_body_collision_before_model():
    game = SnakeGame(width=6, height=6, seed=1)
    game.snake = [(3, 3), (3, 2), (2, 2), (2, 3), (2, 4)]
    game.direction = "right"
    assert game.immediate_failure_reason("up") == "body_collision"
    assert "up" not in game.safe_directions()


def test_snake_single_safe_action_is_resolved_without_model():
    game = SnakeGame(width=5, height=5, seed=1)
    game.snake = [(4, 1), (3, 1), (3, 2), (4, 2)]
    game.direction = "up"
    game.food = (0, 0)
    safe = game.safe_directions()
    assert safe == ("up",)
    request, decision, latency, constraints = choose_move(game, NeverCalledScorer())
    assert request["candidates"][0]["id"] == "up"
    assert decision.choice == "up"
    assert latency == 0.0
    assert constraints["mode"] == "deterministic_single_safe_action"


def test_snake_wall_collision_ends_game():
    game = SnakeGame(width=5, height=5, seed=1)
    game.snake = [(4, 2), (3, 2), (2, 2)]
    game.direction = "right"
    outcome = game.step("right")
    assert outcome.alive is False
    assert outcome.reason == "wall_collision"


def test_snake_eating_food_grows_and_scores():
    game = SnakeGame(width=6, height=6, seed=1)
    hx, hy = game.head
    game.food = (hx + 1, hy)
    before = len(game.snake)
    outcome = game.step("right")
    assert outcome.ate_food is True
    assert game.score == 1
    assert len(game.snake) == before + 1


def test_snake_defaults_to_single_forward_direct_choice():
    args = build_parser().parse_args(["--model", "model.gguf"])
    assert args.scorer == "direct"


def test_snake_action_features_expose_progress_and_future_mobility():
    game = SnakeGame(width=8, height=8, seed=1)
    game.food = (4, 1)

    features = game.action_features("up")

    assert features["next_position"] == {"x": 4, "y": 3}
    assert features["food_progress"] == "closer"
    assert features["food_distance_after"] < features["food_distance_before"]
    assert features["safe_moves_after"] >= 1
    assert features["reachable_free_cells_after"] > 0
    assert features["loop_risk"] == "low"


def test_snake_bounded_memory_marks_revisited_cells_as_loop_risk():
    game = SnakeGame(width=8, height=8, seed=1)
    game.food = (0, 0)

    for direction in ("up", "left", "down", "right"):
        outcome = game.step(direction)
        assert outcome.alive is True

    assert game.steps_since_food == 4
    features = game.action_features("up")
    assert features["recent_visit_count"] >= 1
    assert features["loop_risk"] in {"medium", "high"}
    candidate = next(c for c in build_request(game).candidates if c.id == "up")
    assert "next cell visited 1 times" in candidate.description
    assert "loop risk medium" in candidate.description
    assert game.state()["decision_memory"]["recent_window_size"] <= 12


def test_snake_bounded_memory_resets_when_food_is_eaten():
    game = SnakeGame(width=8, height=8, seed=1)
    hx, hy = game.head
    game.food = (hx + 1, hy)

    game.step("right")

    memory = game.state()["decision_memory"]
    assert game.steps_since_food == 0
    assert memory["recent_window_size"] == 1
    assert memory["recent_unique_head_cells"] == 1


def test_compact_request_keeps_geometry_and_sensors_without_duplicate_grid():
    game = SnakeGame(seed=7)
    game.food = (4, 3)
    request = build_request(game, input_format="compact")
    assert request.state["snake"] == game.state()["snake"]
    assert request.state["food"] == {"x": 4, "y": 3}
    assert "board_grid" not in request.state
    assert "board_grid" in game.state()
    assert "food=1>0; eat=true" in request.candidates[0].description


def test_adjacent_food_policy_is_explicit_and_skips_model():
    game = SnakeGame(seed=7)
    game.food = (5, 4)
    request, decision, latency, constraints = choose_move(
        game, NeverCalledScorer(), controller="adjacent-food", input_format="compact",
    )
    assert len(request["candidates"]) == 3
    assert decision.choice == "right"
    assert latency == 0
    assert constraints["mode"] == "deterministic_adjacent_food_policy"
    assert decision.probability_status == "deterministic_application_policy"


def test_adjacent_food_policy_rejects_immediate_dead_end():
    class RecordingScorer:
        called = False

        def score(self, request):
            self.called = True
            from decisio.schema import DecisionResult
            return DecisionResult(choice="left", distribution={"left": 1.0},
                                  scores={"left": 0.0}, scorer="test")

    game = SnakeGame(width=5, height=5)
    game.snake = [(3, 0), (3, 1), (4, 1), (4, 2)]
    game.direction = "up"
    game.food = (4, 0)
    assert game.action_features("right")["safe_moves_after"] == 0
    scorer = RecordingScorer()
    _, _, _, constraints = choose_move(game, scorer, controller="adjacent-food")
    assert scorer.called
    assert constraints["mode"] == "model"
