from __future__ import annotations

import json
import mimetypes
from collections.abc import Callable
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import sys
from pathlib import Path
from threading import Event
from typing import Any
from urllib.parse import parse_qs, unquote, urlparse

from .chronicle import ChronicleStore, default_chronicle_path
from .event_store import EventStore
from .projections import event_projection, world_projection
from .world import replay


class QuietThreadingHTTPServer(ThreadingHTTPServer):
    """ThreadingHTTPServer that suppresses benign client disconnect tracebacks."""

    def handle_error(self, request: Any, client_address: Any) -> None:
        exctype, _, _ = sys.exc_info()
        if exctype is not None and issubclass(
            exctype, (ConnectionResetError, BrokenPipeError, ConnectionAbortedError)
        ):
            return
        super().handle_error(request, client_address)


class ObserverReadModel:
    """Privileged read-only projection for the local Architect Observer."""

    def __init__(
        self,
        database_path: str | Path,
        chronicle_database_path: str | Path | None = None,
    ) -> None:
        self.database_path = Path(database_path)
        self.chronicle_database_path = Path(
            chronicle_database_path or default_chronicle_path(database_path)
        )

    def snapshot(self, *, at_sequence: int | None = None) -> dict[str, Any]:
        if at_sequence is not None and at_sequence < 0:
            raise ValueError("at_sequence must be non-negative")
        with EventStore(self.database_path, read_only=True) as store:
            events, minds = store.read_snapshot()
        latest_sequence = events[-1].sequence if events else 0
        if at_sequence is not None and at_sequence > latest_sequence:
            raise ValueError("at_sequence cannot be beyond the live sequence")
        projected_events = (
            events
            if at_sequence is None
            else [event for event in events if (event.sequence or 0) <= at_sequence]
        )
        projected_sequence = projected_events[-1].sequence if projected_events else 0
        is_live = at_sequence is None or at_sequence == latest_sequence
        return {
            "schema_version": 1,
            "observer_scope": "architect-local-read-only",
            "last_sequence": projected_sequence,
            "latest_sequence": latest_sequence,
            "is_live": is_live,
            "world": world_projection(replay(projected_events)),
            "minds": (
                {agent_id: mind.to_dict() for agent_id, mind in minds.items()}
                if is_live
                else {}
            ),
        }

    def events(
        self, *, after_sequence: int = 0, limit: int = 500
    ) -> list[dict[str, Any]]:
        if after_sequence < 0:
            raise ValueError("after_sequence must be non-negative")
        if not 1 <= limit <= 5000:
            raise ValueError("limit must be between 1 and 5000")
        with EventStore(self.database_path, read_only=True) as store:
            events = store.events(after_sequence=after_sequence)[:limit]
        return [event_projection(event) for event in events]

    def chronicle_entries(
        self, *, after_sequence: int = 0, limit: int = 200
    ) -> list[dict[str, Any]]:
        if after_sequence < 0:
            raise ValueError("after_sequence must be non-negative")
        if not 1 <= limit <= 1000:
            raise ValueError("limit must be between 1 and 1000")
        if not self.chronicle_database_path.is_file():
            return []
        with ChronicleStore(self.chronicle_database_path, read_only=True) as store:
            entries = store.entries(after_sequence=after_sequence)[:limit]
        return [entry.to_dict() for entry in entries]


@dataclass(frozen=True, slots=True)
class ObserverAddress:
    host: str
    port: int


class ObserverServer:
    def __init__(
        self,
        database_path: str | Path,
        *,
        chronicle_database_path: str | Path | None = None,
        host: str = "127.0.0.1",
        port: int = 8765,
        poll_interval: float = 0.5,
        static_directory: str | Path | None = None,
        operational_health: Callable[[], dict[str, Any]] | None = None,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        self.read_model = ObserverReadModel(database_path, chronicle_database_path)
        self.stop_event = Event()
        self.poll_interval = poll_interval
        self.static_directory = (
            None if static_directory is None else Path(static_directory).resolve()
        )
        if self.static_directory is not None and not (
            self.static_directory / "index.html"
        ).is_file():
            raise ValueError("static_directory must contain index.html")
        self.operational_health = operational_health
        handler = self._handler_type()
        self.httpd = QuietThreadingHTTPServer((host, port), handler)
        self.httpd.daemon_threads = True

    @property
    def address(self) -> ObserverAddress:
        host, port = self.httpd.server_address[:2]
        return ObserverAddress(str(host), int(port))

    def serve_forever(self) -> None:
        self.httpd.serve_forever(poll_interval=0.2)

    def shutdown(self) -> None:
        self.stop_event.set()
        self.httpd.shutdown()
        self.httpd.server_close()

    def _handler_type(self) -> type[BaseHTTPRequestHandler]:
        read_model = self.read_model
        stop_event = self.stop_event
        poll_interval = self.poll_interval
        static_directory = self.static_directory
        operational_health = self.operational_health

        class ObserverRequestHandler(BaseHTTPRequestHandler):
            server_version = "NewlandObserver/0.1"

            def do_OPTIONS(self) -> None:
                self.send_response(HTTPStatus.NO_CONTENT)
                self._cors_headers()
                self.end_headers()

            def do_GET(self) -> None:
                parsed = urlparse(self.path)
                try:
                    if parsed.path == "/api/health":
                        snapshot = read_model.snapshot()
                        chronicle = read_model.chronicle_entries()
                        health = {
                            "status": "ok",
                            "last_sequence": snapshot["last_sequence"],
                            "last_chronicle_sequence": (
                                chronicle[-1]["sequence"] if chronicle else 0
                            ),
                        }
                        if operational_health is not None:
                            health["runtime"] = operational_health()
                        self._json(health)
                        return
                    if parsed.path == "/api/snapshot":
                        query = parse_qs(parsed.query)
                        values = query.get("at_sequence")
                        at_sequence = None if not values else int(values[-1])
                        self._json(read_model.snapshot(at_sequence=at_sequence))
                        return
                    if parsed.path == "/api/events":
                        query = parse_qs(parsed.query)
                        after_sequence = self._query_int(
                            query, "after_sequence", default=0
                        )
                        limit = self._query_int(query, "limit", default=500)
                        self._json(
                            {
                                "events": read_model.events(
                                    after_sequence=after_sequence,
                                    limit=limit,
                                )
                            }
                        )
                        return
                    if static_directory is not None and not parsed.path.startswith(
                        "/api/"
                    ):
                        self._static(parsed.path, static_directory)
                        return
                    if parsed.path == "/api/stream":
                        query = parse_qs(parsed.query)
                        query_cursor = self._query_int(
                            query, "after_sequence", default=0
                        )
                        header_cursor = self._header_int("Last-Event-ID", default=0)
                        self._stream(
                            max(query_cursor, header_cursor),
                            read_model.events,
                            "newland-event",
                        )
                        return
                    if parsed.path == "/api/chronicle":
                        query = parse_qs(parsed.query)
                        after_sequence = self._query_int(
                            query, "after_sequence", default=0
                        )
                        limit = self._query_int(query, "limit", default=200)
                        self._json(
                            {
                                "entries": read_model.chronicle_entries(
                                    after_sequence=after_sequence,
                                    limit=limit,
                                )
                            }
                        )
                        return
                    if parsed.path == "/api/chronicle-stream":
                        query = parse_qs(parsed.query)
                        query_cursor = self._query_int(
                            query, "after_sequence", default=0
                        )
                        header_cursor = self._header_int("Last-Event-ID", default=0)
                        self._stream(
                            max(query_cursor, header_cursor),
                            read_model.chronicle_entries,
                            "chronicle-entry",
                        )
                        return
                except (TypeError, ValueError) as error:
                    self._json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
                    return
                self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

            def _static(self, request_path: str, root: Path) -> None:
                relative = "index.html" if request_path == "/" else unquote(
                    request_path.lstrip("/")
                )
                candidate = (root / relative).resolve()
                if root not in candidate.parents and candidate != root:
                    self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                    return
                if not candidate.is_file():
                    self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)
                    return
                encoded = candidate.read_bytes()
                content_type = mimetypes.guess_type(candidate.name)[0]
                self.send_response(HTTPStatus.OK)
                self.send_header(
                    "Content-Type", content_type or "application/octet-stream"
                )
                self.send_header("Content-Length", str(len(encoded)))
                self.send_header(
                    "Cache-Control",
                    "no-cache" if candidate.name == "index.html" else "public, max-age=31536000, immutable",
                )
                self.end_headers()
                self.wfile.write(encoded)

            def _stream(
                self,
                after_sequence: int,
                loader: Callable[..., list[dict[str, Any]]],
                event_name: str,
            ) -> None:
                if after_sequence < 0:
                    raise ValueError("after_sequence must be non-negative")
                self.send_response(HTTPStatus.OK)
                self.send_header("Content-Type", "text/event-stream; charset=utf-8")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("X-Accel-Buffering", "no")
                self._cors_headers()
                self.end_headers()
                cursor = after_sequence
                try:
                    while not stop_event.is_set():
                        records = loader(after_sequence=cursor)
                        if records:
                            for record in records:
                                sequence = int(record["sequence"] or cursor)
                                payload = json.dumps(
                                    record,
                                    ensure_ascii=False,
                                    separators=(",", ":"),
                                )
                                block = (
                                    f"id: {sequence}\n"
                                    f"event: {event_name}\n"
                                    f"data: {payload}\n\n"
                                )
                                self.wfile.write(block.encode("utf-8"))
                                cursor = sequence
                        else:
                            self.wfile.write(b": heartbeat\n\n")
                        self.wfile.flush()
                        stop_event.wait(poll_interval)
                except (BrokenPipeError, ConnectionAbortedError, ConnectionResetError):
                    return

            def _json(
                self,
                payload: dict[str, Any],
                *,
                status: HTTPStatus = HTTPStatus.OK,
            ) -> None:
                encoded = json.dumps(
                    payload,
                    ensure_ascii=False,
                    sort_keys=True,
                ).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Content-Length", str(len(encoded)))
                self.send_header("Cache-Control", "no-store")
                self._cors_headers()
                self.end_headers()
                self.wfile.write(encoded)

            def _cors_headers(self) -> None:
                origin = self.headers.get("Origin")
                if origin is None:
                    return
                parsed_origin = urlparse(origin)
                if parsed_origin.scheme not in {
                    "http",
                    "https",
                } or parsed_origin.hostname not in {"127.0.0.1", "localhost", "::1"}:
                    return
                self.send_header("Access-Control-Allow-Origin", origin)
                self.send_header("Vary", "Origin")
                self.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
                self.send_header("Access-Control-Allow-Headers", "Last-Event-ID")

            @staticmethod
            def _query_int(
                query: dict[str, list[str]], key: str, *, default: int
            ) -> int:
                values = query.get(key)
                return default if not values else int(values[-1])

            def _header_int(self, key: str, *, default: int) -> int:
                value = self.headers.get(key)
                return default if value is None else int(value)

            def log_message(self, format: str, *args: object) -> None:
                return

        return ObserverRequestHandler
