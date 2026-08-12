from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Event
from typing import Any
from urllib.parse import parse_qs, urlparse

from .event_store import EventStore
from .models import EventEnvelope, WorldState
from .world import replay


def event_projection(event: EventEnvelope) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "sequence": event.sequence,
        "schema_version": event.schema_version,
        "world_tick": event.world_tick,
        "world_time": event.world_time,
        "event_type": event.event_type,
        "actor_ids": event.actor_ids,
        "location": event.location,
        "payload": event.payload,
        "visibility": event.visibility,
        "recipient_ids": event.recipient_ids,
        "causation_id": event.causation_id,
    }


def world_projection(state: WorldState) -> dict[str, Any]:
    return {
        "tick": state.tick,
        "world_time": state.world_time,
        "locations": {
            location: sorted(neighbors)
            for location, neighbors in state.locations.items()
        },
        "agents": {
            agent_id: {
                "agent_id": agent.agent_id,
                "name": agent.name,
                "location": agent.location,
                "energy": agent.energy,
                "hunger": agent.hunger,
                "thirst": agent.thirst,
                "native_language": agent.native_language,
                "language_proficiencies": agent.language_proficiencies,
                "skills": agent.skills,
                "family_group_id": agent.family_group_id,
                "inventory": agent.inventory,
                "inventory_capacity": agent.inventory_capacity,
                "active": agent.active,
            }
            for agent_id, agent in state.agents.items()
        },
        "resources": {
            resource_id: {
                "resource_id": resource.resource_id,
                "kind": resource.kind,
                "label": resource.label,
                "location": resource.location,
                "quantity": resource.quantity,
                "unit": resource.unit,
                "renewable": resource.renewable,
            }
            for resource_id, resource in state.resources.items()
        },
        "activities": {
            activity_id: {
                "activity_id": activity.activity_id,
                "label": activity.label,
                "location": activity.location,
                "energy_cost": activity.energy_cost,
                "practiced_skill": activity.practiced_skill,
                "minimum_proficiency": activity.minimum_proficiency,
                "skill_gain": activity.skill_gain,
            }
            for activity_id, activity in state.activities.items()
        },
        "resonance_nodes": {
            node_id: {
                "node_id": node.node_id,
                "label": node.label,
                "location": node.location,
                "intensity": node.intensity,
            }
            for node_id, node in state.resonance_nodes.items()
        },
        "family_groups": {
            group_id: sorted(members)
            for group_id, members in state.family_groups.items()
        },
        "cooperations": {
            proposal_id: {
                "proposal_id": cooperation.proposal_id,
                "proposer_id": cooperation.proposer_id,
                "target_id": cooperation.target_id,
                "activity_id": cooperation.activity_id,
                "status": cooperation.status,
                "created_tick": cooperation.created_tick,
                "response_tick": cooperation.response_tick,
            }
            for proposal_id, cooperation in state.cooperations.items()
        },
        "disputes": {
            dispute_id: {
                "dispute_id": dispute.dispute_id,
                "opener_id": dispute.opener_id,
                "target_id": dispute.target_id,
                "subject_event_id": dispute.subject_event_id,
                "status": dispute.status,
                "created_tick": dispute.created_tick,
                "resolution_offered_by": dispute.resolution_offered_by,
            }
            for dispute_id, dispute in state.disputes.items()
        },
    }


class ObserverReadModel:
    """Privileged read-only projection for the local Architect Observer."""

    def __init__(self, database_path: str | Path) -> None:
        self.database_path = Path(database_path)

    def snapshot(self) -> dict[str, Any]:
        with EventStore(self.database_path, read_only=True) as store:
            events, minds = store.read_snapshot()
        return {
            "schema_version": 1,
            "observer_scope": "architect-local-read-only",
            "last_sequence": events[-1].sequence if events else 0,
            "world": world_projection(replay(events)),
            "minds": {agent_id: mind.to_dict() for agent_id, mind in minds.items()},
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


@dataclass(frozen=True, slots=True)
class ObserverAddress:
    host: str
    port: int


class ObserverServer:
    def __init__(
        self,
        database_path: str | Path,
        *,
        host: str = "127.0.0.1",
        port: int = 8765,
        poll_interval: float = 0.5,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        self.read_model = ObserverReadModel(database_path)
        self.stop_event = Event()
        self.poll_interval = poll_interval
        handler = self._handler_type()
        self.httpd = ThreadingHTTPServer((host, port), handler)
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
                        self._json(
                            {
                                "status": "ok",
                                "last_sequence": snapshot["last_sequence"],
                            }
                        )
                        return
                    if parsed.path == "/api/snapshot":
                        self._json(read_model.snapshot())
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
                    if parsed.path == "/api/stream":
                        query = parse_qs(parsed.query)
                        query_cursor = self._query_int(
                            query, "after_sequence", default=0
                        )
                        header_cursor = self._header_int("Last-Event-ID", default=0)
                        self._stream(max(query_cursor, header_cursor))
                        return
                except (TypeError, ValueError) as error:
                    self._json({"error": str(error)}, status=HTTPStatus.BAD_REQUEST)
                    return
                self._json({"error": "not found"}, status=HTTPStatus.NOT_FOUND)

            def _stream(self, after_sequence: int) -> None:
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
                        events = read_model.events(after_sequence=cursor)
                        if events:
                            for event in events:
                                sequence = int(event["sequence"] or cursor)
                                payload = json.dumps(
                                    event,
                                    ensure_ascii=False,
                                    separators=(",", ":"),
                                )
                                block = (
                                    f"id: {sequence}\n"
                                    f"event: {event['event_type']}\n"
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
