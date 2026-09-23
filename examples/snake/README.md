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

Before Decisio is called, the game deterministically removes reverse moves and moves that would
immediately hit a wall or body segment. Decisio chooses only among the remaining safe alternatives.
If exactly one safe move remains, the controller takes it without running the model.

Snake is an **example and behavioral probe**, not evidence that Decisio is a good game-playing agent.

## Live decision-loop UI

The branded local UI makes the complete decision loop visible:

```text
OBSERVE                     DECIDE                         ACT
board/state       ->        candidate preferences    ->   selected move
safe + filtered moves       model + scorer                updated board
                             live elapsed time
                             decision latency
                             generated tokens
                             cache/reuse evidence
```

The browser is only a local example surface. The GGUF model stays in the Python process and no HTTP
server is added to the Decisio core package.

Install the llama.cpp runtime, then launch:

```bash
uv sync --extra llama --extra dev

uv run python -m examples.snake.web \
  --model /path/to/Qwen3.5-2B-Q4_K_M.gguf \
  --threads 5 \
  --threads-batch 11 \
  --trace .artifacts/snake-live.jsonl \
  --open
```

The UI opens at `http://127.0.0.1:8765/` by default.

Controls:

- **Start / Pause** — continuously ask Decisio for the next move;
- **1 move** — execute one complete observe → decide → act cycle;
- **Reset** — restart the deterministic episode;
- **Reveal hold** — keep each decision visible before Snake moves.

The default visual hierarchy is intentionally narrow: the board and selected move are primary;
candidate preferences and deterministic filters are contextual; model/runtime details, request JSON
and response JSON are diagnostics.

The UI labels candidate values as **relative preference**, not probability of correctness. Filtered
wall/body/reversal actions remain visible so the deterministic/application boundary is explicit.

Design source of truth for this example is code-first:
`examples/snake/static/index.html`, `style.css`, `app.js`, with the existing Decisio brand
tokens/assets as the visual owner.

## Reference artifact

The Decisio v1 reference path is CPU-only Qwen3.5-2B Q4_K_M GGUF through llama.cpp. The exact
artifact/runtime identity belongs to the scorer gate, not to this example.

For a headless rollout:

```bash
uv run python -m examples.snake.play \
  --model /path/to/Qwen3.5-2B-Q4_K_M.gguf \
  --threads 5 \
  --threads-batch 11 \
  --max-steps 100 \
  --render
```

Thread values are local execution tuning, not the frozen CPU scorer-gate identity.

## Why the controller filters first

A prior smoke exposed an immediate-wall failure. That is not a judgment an LLM should own. Geometry
is deterministic, so the game removes impossible/deadly immediate actions before scoring.

This is the intended Decisio integration pattern:

> **Hard constraints define the valid action space; Decisio ranks the remaining semantic alternatives.**

## What Snake exercises

Snake stresses properties that a static classification fixture does not:

- sequential decisions where an early mistake changes all future states;
- dynamic candidate sets;
- spatial reasoning over structured state;
- repeated inference latency;
- deterministic constraints before probabilistic scoring;
- error accumulation;
- reproducible episodes through a fixed random seed.

## Objective used by the controller

The model is asked to prioritize:

1. progress toward food;
2. preserving future mobility and avoiding obvious traps.

Immediate wall/body validity is not delegated to the LLM. Candidate descriptions contain the
direction and movement delta; the model is not given a handcrafted distance-to-food score.

## Compare scoring strategies

Run the same deterministic episode with the same model and seed:

```bash
uv run python -m examples.snake.play --model /path/model.gguf --seed 42 --scorer semantic --max-steps 50
uv run python -m examples.snake.play --model /path/model.gguf --seed 42 --scorer semantic-independent --max-steps 50
uv run python -m examples.snake.play --model /path/model.gguf --seed 42 --scorer letters --max-steps 50
```

Full rollouts can diverge after the first differing action, so Snake remains a behavioral probe rather
than the scorer promotion benchmark.

## Record every decision

Both the headless and live UI paths can write the same trace shape.

```bash
uv run python -m examples.snake.play \
  --model /path/model.gguf \
  --seed 42 \
  --max-steps 50 \
  --trace .artifacts/snake-semantic.jsonl
```

Each JSONL row stores the exact state, candidates, Decisio distribution, model provenance, runtime
evidence and game outcome.

## Visual reference

The information hierarchy takes
[Rizzo Flow Snake](https://github.com/Rizzo-AI-Academy/rizzo-flow/blob/main/src/rizzo_flow/snake.html)
as a useful reference without copying its implementation.

Decisio-specific choices are deliberate:

- the decision cycle is explicitly shown as **OBSERVE → DECIDE → ACT**;
- deterministic invalid actions are filtered before model scoring and stay visible as filtered;
- the selected move is the primary visual event;
- candidate relative preferences remain close to the board and readable as bars;
- model, scorer and per-decision latency are always visible;
- zero generated answer tokens and cache/reuse evidence are visible;
- raw request/response JSON is progressively disclosed instead of dominating the common path;
- reduced-motion settings disable non-essential animation.

## CI video artifact

The real-model smoke can still render a trace-backed MP4. The video is generated from the actual
states and decisions used by the test; it is not a scripted animation.

To render a recorded trace locally:

```bash
uv sync --extra video
# ffmpeg must also be available on PATH

uv run python -m examples.snake.video \
  --trace .artifacts/snake-semantic.jsonl \
  --output .artifacts/snake-semantic.mp4 \
  --frames-dir .artifacts/snake-frames
```
