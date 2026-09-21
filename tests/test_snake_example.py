from examples.snake.game import SnakeGame
from examples.snake.play import build_request


def test_snake_request_excludes_immediate_reverse():
    game = SnakeGame(seed=1)
    request = build_request(game)
    ids = {candidate.id for candidate in request.candidates}
    assert ids == {"up", "right", "down"}
    assert "left" not in ids


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
