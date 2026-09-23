from examples.snake.game import SnakeGame
from examples.snake.play import build_parser, build_request, choose_move


class NeverCalledScorer:
    def score(self, request):
        raise AssertionError(f"model should not be called for request {request}")


def test_snake_request_contains_only_immediately_safe_actions():
    game = SnakeGame(seed=1)
    request = build_request(game)
    ids = {candidate.id for candidate in request.candidates}
    assert ids == {"up", "right", "down"}
    assert "left" not in ids


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
