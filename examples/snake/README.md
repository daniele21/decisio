# Snake

Snake turns Decisio into a repeated action selector rather than a one-shot classifier.

At every game step:

```text
board + snake body + food + current direction
                      |
                      v
             candidate moves
            UP / RIGHT / DOWN / LEFT
                      |
                      v
                   Decisio
                      |
                      v
               one next move
                      |
                      v
                 game.step()
                      |
                   repeat
```

The immediate reverse direction is excluded because standard Snake does not allow a 180-degree reversal. Wall/body collisions remain possible candidates: avoiding them is part of the model's decision problem.

## Why this is useful

Snake stresses properties that a static classification fixture does not:

- sequential decisions where an early mistake changes all future states;
- dynamic candidate sets;
- spatial reasoning over structured state;
- repeated inference latency;
- error accumulation;
- reproducible episodes through a fixed random seed;
- comparison between semantic scoring and the A/B/C-style baseline.

It is an **example and behavioral probe**, not evidence that Decisio is a good game-playing agent.

## Run a cheap smoke

The GitHub CI uses the official Qwen3.5-0.8B checkpoint for functional integration. You can use the same model:

```bash
uv sync --extra qwen --extra dev

uv run python examples/snake/play.py \
  --model Qwen/Qwen3.5-0.8B \
  --revision 2fc06364 \
  --device cpu \
  --dtype bfloat16 \
  --max-steps 10 \
  --render
```

## Run with the Decisio reference model

On a CUDA machine:

```bash
uv run python examples/snake/play.py \
  --model Qwen/Qwen3.5-4B \
  --revision 1eef1f4e0bc57dec8f814d1e4c714c8e0065d261 \
  --device cuda \
  --dtype bfloat16 \
  --max-steps 100 \
  --render
```

## Compare scoring strategies

Run the same deterministic episode with the same model and seed:

```bash
uv run python examples/snake/play.py --seed 42 --scorer semantic --max-steps 50
uv run python examples/snake/play.py --seed 42 --scorer letters  --max-steps 50
```

This is not yet a rigorous benchmark because both runs may diverge after the first differing action. A future Snake evaluation harness should compare fixed board states as well as full rollouts.

## Record every decision

```bash
uv run python examples/snake/play.py \
  --seed 42 \
  --max-steps 50 \
  --trace .artifacts/snake-semantic.jsonl
```

Each JSONL row stores the exact state, candidates, Decisio distribution, model provenance and game outcome. This makes interesting failures easy to inspect and later promote into frozen regression fixtures.

## Objective used by the controller

The model is asked to prioritize:

1. avoiding immediate wall/body death;
2. progress toward food;
3. preserving future mobility and avoiding obvious traps.

Candidate descriptions contain only the direction and movement delta. Decisio is not given a precomputed "safe" flag or distance-to-food score.
