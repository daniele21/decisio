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

Before Decisio is called, the game deterministically removes reverse moves and moves that would immediately hit a wall or body segment. Decisio chooses only among the remaining safe alternatives. If exactly one safe move remains, the controller takes it without running the model.

## Why the controller filters first

The prior smoke test exposed a useful failure: the 0.8B model kept choosing RIGHT even when RIGHT meant an immediate wall collision. That is not a judgment an LLM should own. Geometry is deterministic, so the game now filters impossible/deadly immediate actions before scoring.

This is the intended Decisio integration pattern: **hard constraints define the valid action space; Decisio ranks the remaining semantic alternatives.**

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

Install the llama.cpp runtime and point Snake at any compatible local Qwen GGUF:

```bash
uv sync --extra llama --extra dev

uv run python -m examples.snake.play \
  --model /path/to/Qwen3.5-0.8B-Q4_K_M.gguf \
  --threads 4 \
  --max-steps 10 \
  --render
```

## Run with the Decisio reference artifact class

The reference path is CPU-only Qwen3.5-4B Q4_K_M GGUF:

```bash
uv run python -m examples.snake.play \
  --model /path/to/Qwen3.5-4B-Q4_K_M.gguf \
  --threads 8 \
  --max-steps 100 \
  --render
```

The exact 4B artifact SHA and runtime identity are frozen by scorer-gate v2, not by this example.

## Compare scoring strategies

Run the same deterministic episode with the same model and seed:

```bash
uv run python -m examples.snake.play --model /path/model.gguf --seed 42 --scorer semantic --max-steps 50
uv run python -m examples.snake.play --model /path/model.gguf --seed 42 --scorer semantic-independent --max-steps 50
uv run python -m examples.snake.play --model /path/model.gguf --seed 42 --scorer letters --max-steps 50
```

This is not yet a rigorous benchmark because both runs may diverge after the first differing action. A future Snake evaluation harness should compare fixed board states as well as full rollouts.

## Record every decision

```bash
uv run python -m examples.snake.play \
  --model /path/model.gguf \
  --seed 42 \
  --max-steps 50 \
  --trace .artifacts/snake-semantic.jsonl
```

Each JSONL row stores the exact state, candidates, Decisio distribution, model provenance and game outcome. This makes interesting failures easy to inspect and later promote into frozen regression fixtures.

## Objective used by the controller

The model is asked to prioritize:

1. progress toward food;
2. preserving future mobility and avoiding obvious traps.

Immediate wall/body validity is no longer delegated to the LLM. Candidate descriptions still contain only the direction and movement delta; the model is not given a handcrafted distance-to-food score.


## Visual and UX reference

The Snake evidence view intentionally takes **Rizzo Flow Snake** as its visual/interaction reference:
<https://github.com/Rizzo-AI-Academy/rizzo-flow/blob/main/src/rizzo_flow/snake.html>.

Decisio does not copy that implementation. It adopts the useful information hierarchy for this
kind of demo:

- game state and model decision are visible side by side;
- the chosen move is the primary visual event;
- candidate probabilities stay close to the board and also remain readable as bars;
- deterministic filtering is visible but secondary to the model decision;
- latency, generated-token count and outcome are compact evidence, not decorative dashboard chrome;
- diagnostics must not imply that uncalibrated relative scores are correctness probabilities.

The current artifact is deliberately a rendered evidence video, not a new browser application.
An interactive Snake surface should wait until Decisio's scorer semantics and public runtime surface
are stable enough to justify owning UI lifecycle and interaction code.

## Visual and UX direction

For Snake presentation, use the information hierarchy of [Rizzo Flow Snake](https://github.com/Rizzo-AI-Academy/rizzo-flow/blob/main/src/rizzo_flow/snake.html) as a reference, not as an implementation to copy.

The useful pattern is:

```text
game board                         decision
large, immediately readable       chosen move first
score / length / step              probability bars
                                  deterministic filters
                                  latency / generated tokens
                                  status + diagnostics
```

Decisio-specific differences are deliberate:

- deterministic wall/body/reversal constraints are filtered **before** model scoring, rather than exposed as choices the model may override;
- filtered actions stay visible in the presentation so the constraint boundary is obvious;
- zero generated answer tokens and uncalibrated score semantics stay visible;
- diagnostics are secondary to the board and current decision;
- the current deliverable is the trace-backed MP4 artifact, not a new web product surface.

An interactive Snake page can reuse this hierarchy after the scorer semantics gate is settled. The repository currently defers new UI surfaces until Milestone 0–1 establishes the scorer.

## CI video artifact

The real-model GitHub Actions smoke runs a short Snake rollout with the official Qwen3.5-0.8B checkpoint, renders the actual decision trace to MP4, and uploads both:

- `decisio-snake.mp4` — board state plus chosen move and per-action Decisio distribution;
- `decisio-snake-smoke.jsonl` — the exact machine-readable trace behind the video.

The video is generated from the same states and model decisions used by the test; it is not a scripted animation.

To render a recorded trace locally:

```bash
uv sync --extra video
# ffmpeg must also be available on PATH

uv run python -m examples.snake.video \
  --trace .artifacts/snake-semantic.jsonl \
  --output .artifacts/snake-semantic.mp4 \
  --frames-dir .artifacts/snake-frames
```
