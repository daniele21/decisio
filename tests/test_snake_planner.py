from examples.snake.game import SnakeGame
from examples.snake.planner import SnakePlanner


def test_planner_prefers_short_safe_path_to_food():
    game = SnakeGame(seed=1)
    game.food = (4, 1)

    result = SnakePlanner(max_nodes=10_000).evaluate(game)

    assert result.best_actions == ("up",)
    assert result.actions["up"].status == "proven_safe_food"
    assert result.actions["up"].safe_food_steps == 3
    assert result.ranks["up"] == 1


def test_planner_rejects_locally_tempting_body_pocket():
    game = SnakeGame(width=6, height=6, seed=1)
    game.snake = [
        (2, 2), (2, 3), (1, 3), (1, 4), (2, 4), (3, 4),
        (4, 4), (4, 3), (4, 2), (4, 1), (3, 1), (2, 1), (1, 1),
    ]
    game.direction = "up"
    game.food = (5, 2)

    result = SnakePlanner(max_nodes=50_000).evaluate(game)

    assert set(game.safe_directions()) == {"left", "right"}
    assert result.best_actions == ("left",)
    assert result.actions["left"].status == "proven_safe_food"
    assert result.actions["right"].status in {"trapping_food", "proven_no_safe_food"}
    assert result.ranks["left"] < result.ranks["right"]


def test_planner_post_food_horizon_exposes_adjacent_trap():
    game = SnakeGame(width=6, height=6, seed=1)
    game.snake = [
        (2, 2), (2, 3), (1, 3), (1, 4), (2, 4), (3, 4),
        (4, 4), (4, 3), (4, 2), (4, 1), (3, 1), (2, 1), (1, 1),
    ]
    game.direction = "up"
    game.food = (3, 2)

    result = SnakePlanner(post_food_escape_horizon=4).evaluate(game)

    assert game.action_features("right")["eats_food"] is True
    assert game.action_features("right")["safe_moves_after"] > 0
    assert result.actions["right"].status == "trapping_food"
    assert "right" not in result.best_actions


def test_planner_reports_bounded_unknown_instead_of_false_optimality():
    game = SnakeGame(seed=1)
    game.food = (4, 0)

    result = SnakePlanner(max_nodes=1, max_depth=20).evaluate(game)

    assert any(action.status == "bounded_unknown" for action in result.actions.values())
    assert result.complete is False
