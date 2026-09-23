"""Local branded Snake demo for visualizing the Decisio decision loop."""

from __future__ import annotations

import argparse
import json
import threading
import webbrowser
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from examples.snake.game import SnakeGame
from examples.snake.play import (
    SCORER_CHOICES,
    append_trace,
    build_request,
    build_scorer,
    choose_move,
)

STATIC_ROOT = Path(__file__).with_name("static")
REPO_ROOT = Path(__file__).resolve().parents[2]
BRAND_MARK = REPO_ROOT / "assets" / "brand" / "decisio-mark.svg"


class SnakeSession:
    """One in-memory Snake episode backed by one already-loaded Decisio scorer."""

    def __init__(
        self,
        *,
        scorer: Any,
        seed: int,
        width: int,
        height: int,
        max_steps: int,
        trace: Path | None = None,
    ) -> None:
        self.scorer = scorer
        self.seed = seed
        self.width = width
        self.height = height
        self.max_steps = max_steps
        self.trace = trace
        self._lock = threading.Lock()
        self.game = SnakeGame(width=width, height=height, seed=seed)
        if self.trace is not None:
            self.trace.unlink(missing_ok=True)

    @property
    def backend(self) -> Any:
        return getattr(self.scorer, "backend", None)

    def _runtime_identity(self) -> dict[str, Any]:
        identity = getattr(self.backend, "identity", {})
        return dict(identity) if isinstance(identity, dict) else {}

    def _constraints_unlocked(self) -> dict[str, Any]:
        raw = self.game.action_constraints()
        safe = self.game.safe_directions()
        return {
            "legal_actions": list(self.game.candidate_directions()),
            "safe_actions": list(safe),
            "candidate_features": self.game.candidate_features(safe),
            "filtered_actions": {
                direction: reason
                for direction, reason in raw.items()
                if reason is not None
            },
        }

    def _next_request_unlocked(self) -> dict[str, Any] | None:
        if not self.game.alive or self.game.steps >= self.max_steps:
            return None
        safe = self.game.safe_directions()
        if not safe:
            return None
        return build_request(self.game, safe).to_dict()

    def status(self) -> dict[str, Any]:
        with self._lock:
            return self._status_unlocked()

    def _status_unlocked(self) -> dict[str, Any]:
        return {
            "state": self.game.state(),
            "constraints": self._constraints_unlocked(),
            "next_request": self._next_request_unlocked(),
            "alive": self.game.alive,
            "steps": self.game.steps,
            "score": self.game.score,
            "snake_length": len(self.game.snake),
            "seed": self.seed,
            "max_steps": self.max_steps,
            "limit_reached": self.game.steps >= self.max_steps,
            "scorer": getattr(self.scorer, "name", type(self.scorer).__name__),
            "model": self._runtime_identity(),
        }

    def reset(self) -> dict[str, Any]:
        with self._lock:
            self.game = SnakeGame(
                width=self.width,
                height=self.height,
                seed=self.seed,
            )
            if self.trace is not None:
                self.trace.unlink(missing_ok=True)
            return self._status_unlocked()

    def step(self) -> dict[str, Any]:
        with self._lock:
            if not self.game.alive:
                raise RuntimeError("game is over; reset before requesting another move")
            if self.game.steps >= self.max_steps:
                raise RuntimeError("maximum demo steps reached; reset to continue")

            backend = self.backend
            reset_metrics = getattr(backend, "reset_runtime_metrics", None)
            if callable(reset_metrics):
                reset_metrics()

            request, decision, latency, constraints = choose_move(
                self.game,
                self.scorer,
            )
            before_state = request["state"]
            outcome = self.game.step(decision.choice)

            runtime_metrics: dict[str, Any] = {}
            metrics = getattr(backend, "runtime_metrics", None)
            if callable(metrics):
                value = metrics()
                if isinstance(value, dict):
                    runtime_metrics = dict(value)

            record = {
                "step": self.game.steps,
                "request": request,
                "constraints": constraints,
                "decision_latency_seconds": latency,
                "decision": decision.to_dict(),
                "runtime_metrics": runtime_metrics,
                "outcome": {
                    "alive": outcome.alive,
                    "ate_food": outcome.ate_food,
                    "reason": outcome.reason,
                    "game_score": self.game.score,
                },
            }
            if self.trace is not None:
                append_trace(self.trace, record)

            return {
                **record,
                "before_state": before_state,
                "after_state": self.game.state(),
                "limit_reached": self.game.steps >= self.max_steps,
                "status": self._status_unlocked(),
            }

    def close(self) -> None:
        close = getattr(self.backend, "close", None)
        if callable(close):
            close()


def _json_bytes(value: Any) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True) + "\n").encode("utf-8")


class SnakeDemoHandler(BaseHTTPRequestHandler):
    server: SnakeDemoServer

    def log_message(self, format: str, *args: Any) -> None:
        del format, args

    def _send(
        self,
        status: HTTPStatus,
        body: bytes,
        *,
        content_type: str,
    ) -> None:
        self.send_response(status.value)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def _send_json(self, status: HTTPStatus, value: Any) -> None:
        self._send(
            status,
            _json_bytes(value),
            content_type="application/json; charset=utf-8",
        )

    def _send_file(self, path: Path, content_type: str) -> None:
        if not path.is_file():
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
            return
        self._send(HTTPStatus.OK, path.read_bytes(), content_type=content_type)

    def do_GET(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        if path == "/":
            self._send_file(STATIC_ROOT / "index.html", "text/html; charset=utf-8")
        elif path == "/style.css":
            self._send_file(STATIC_ROOT / "style.css", "text/css; charset=utf-8")
        elif path == "/app.js":
            self._send_file(STATIC_ROOT / "app.js", "text/javascript; charset=utf-8")
        elif path == "/decisio-mark.svg":
            self._send_file(BRAND_MARK, "image/svg+xml")
        elif path == "/api/status":
            self._send_json(HTTPStatus.OK, self.server.session.status())
        else:
            self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})

    def do_POST(self) -> None:  # noqa: N802
        path = urlparse(self.path).path
        try:
            if path == "/api/reset":
                self._send_json(HTTPStatus.OK, self.server.session.reset())
            elif path == "/api/step":
                self._send_json(HTTPStatus.OK, self.server.session.step())
            else:
                self._send_json(HTTPStatus.NOT_FOUND, {"error": "not found"})
        except RuntimeError as exc:
            self._send_json(HTTPStatus.CONFLICT, {"error": str(exc)})
        except Exception as exc:  # pragma: no cover - integration error surface
            self._send_json(
                HTTPStatus.INTERNAL_SERVER_ERROR,
                {"error": f"{type(exc).__name__}: {exc}"},
            )


class SnakeDemoServer(ThreadingHTTPServer):
    daemon_threads = True

    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        session: SnakeSession,
    ) -> None:
        super().__init__(server_address, SnakeDemoHandler)
        self.session = session


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run the local branded Decisio Snake decision-loop demo"
    )
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--open", action="store_true", dest="open_browser")
    parser.add_argument("--n-ctx", type=int, default=8192)
    parser.add_argument("--n-batch", type=int, default=512)
    parser.add_argument("--n-ubatch", type=int, default=512)
    parser.add_argument("--threads", type=int)
    parser.add_argument("--threads-batch", type=int)
    parser.add_argument("--max-sequences", type=int, default=8)
    parser.add_argument("--mlock", action="store_true")
    parser.add_argument("--no-mmap", action="store_true")
    parser.add_argument(
        "--scorer",
        choices=SCORER_CHOICES,
        default="direct",
        help=(
            "direct performs one A/B/C/... choice-logit forward pass; "
            "semantic modes remain available for comparison"
        ),
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--width", type=int, default=8)
    parser.add_argument("--height", type=int, default=8)
    parser.add_argument("--max-steps", type=int, default=200)
    parser.add_argument("--trace", type=Path)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if not (1 <= args.port <= 65535):
        raise ValueError("--port must be between 1 and 65535")
    if args.max_steps < 1:
        raise ValueError("--max-steps must be positive")

    scorer = build_scorer(args)
    session = SnakeSession(
        scorer=scorer,
        seed=args.seed,
        width=args.width,
        height=args.height,
        max_steps=args.max_steps,
        trace=args.trace,
    )
    server = SnakeDemoServer((args.host, args.port), session=session)
    url = f"http://{args.host}:{args.port}/"

    print(f"Decisio Snake UI: {url}")
    print(
        "The browser is a local demo surface; model inference stays in this Python process."
    )
    if args.open_browser:
        webbrowser.open(url)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
        session.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
