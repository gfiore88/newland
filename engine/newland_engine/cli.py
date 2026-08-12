from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

from .chronicle import (
    ChronicleUnavailable,
    ChronicleWorker,
    GenerativeChroniclerPool,
    OllamaChronicler,
    default_chronicle_path,
)
from .cognition import GenerativeCognitionPool, OllamaCognition, RoutedCognition
from .event_store import EventStore
from .observer import ObserverServer
from .simulation import NewlandSimulation
from .world import replay


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="newland", description="Newland autonomous world runtime"
    )
    parser.add_argument("--db", type=Path, default=Path("data/newland.db"))
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser(
        "run", help="advance the event-driven vertical slice"
    )
    run_parser.add_argument("--activations", type=int, default=8)
    run_parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Ollama model; repeat for generative failover (default: qwen3:8b)",
    )
    run_parser.add_argument(
        "--reflective-model",
        action="append",
        dest="reflective_models",
        help=(
            "Ollama model for resonance and active disputes; repeat for "
            "generative failover (default: same pool as --model)"
        ),
    )

    subparsers.add_parser("events", help="print the canonical event log")
    subparsers.add_parser("state", help="print materialized world state")
    serve_parser = subparsers.add_parser(
        "serve", help="serve the local read-only Observer API"
    )
    serve_parser.add_argument("--host", default="127.0.0.1")
    serve_parser.add_argument("--port", type=int, default=8765)
    serve_parser.add_argument(
        "--chronicle-db",
        type=Path,
        help="derived chronicle database (default: next to the canonical database)",
    )
    chronicle_parser = subparsers.add_parser(
        "chronicle", help="generate the non-interfering Silent Chronicler diary"
    )
    chronicle_parser.add_argument(
        "--chronicle-db",
        type=Path,
        help="derived chronicle database (default: next to the canonical database)",
    )
    chronicle_parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Ollama model; repeat for generative failover (default: qwen3:8b)",
    )
    chronicle_parser.add_argument("--batch-size", type=int, default=20)
    chronicle_parser.add_argument("--poll-interval", type=float, default=2.0)
    chronicle_parser.add_argument(
        "--once",
        action="store_true",
        help="process at most one pending batch and exit",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        models = args.models or ["qwen3:8b"]
        ordinary = GenerativeCognitionPool(
            [OllamaCognition(model=model) for model in models]
        )
        reflective = (
            GenerativeCognitionPool(
                [OllamaCognition(model=model) for model in args.reflective_models]
            )
            if args.reflective_models
            else ordinary
        )
        cognition = RoutedCognition(ordinary, reflective)
        with NewlandSimulation(args.db, cognition=cognition) as simulation:
            events = simulation.run(max_activations=args.activations)
            _print_events(events)
        return 0

    if args.command == "serve":
        server = ObserverServer(
            args.db,
            chronicle_database_path=args.chronicle_db,
            host=args.host,
            port=args.port,
        )
        address = server.address
        print(f"Newland Observer API: http://{address.host}:{address.port}")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass
        finally:
            server.shutdown()
        return 0

    if args.command == "chronicle":
        if args.poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        models = args.models or ["qwen3:8b"]
        chronicler = GenerativeChroniclerPool(
            [OllamaChronicler(model=model) for model in models]
        )
        worker = ChronicleWorker(
            args.db,
            args.chronicle_db or default_chronicle_path(args.db),
            chronicler,
            batch_size=args.batch_size,
        )
        while True:
            try:
                entry = worker.run_once()
            except ChronicleUnavailable as error:
                print(
                    json.dumps(
                        {"status": "chronicle_deferred", "failures": error.failures},
                        ensure_ascii=False,
                    ),
                    file=sys.stderr,
                )
                if args.once:
                    return 2
                time.sleep(args.poll_interval)
                continue
            if entry is not None:
                print(json.dumps(entry.to_dict(), ensure_ascii=False))
            if args.once:
                return 0
            if entry is None:
                time.sleep(args.poll_interval)

    with EventStore(args.db) as store:
        events = store.events()
        if args.command == "events":
            _print_events(events)
        else:
            state = replay(events)
            print(
                json.dumps(
                    {
                        "tick": state.tick,
                        "world_time": state.world_time,
                        "locations": {
                            key: sorted(value) for key, value in state.locations.items()
                        },
                        "resources": {
                            key: {
                                "kind": value.kind,
                                "label": value.label,
                                "location": value.location,
                                "quantity": value.quantity,
                                "unit": value.unit,
                                "renewable": value.renewable,
                            }
                            for key, value in state.resources.items()
                        },
                        "activities": {
                            key: {
                                "label": value.label,
                                "location": value.location,
                                "energy_cost": value.energy_cost,
                                "practiced_skill": value.practiced_skill,
                                "minimum_proficiency": value.minimum_proficiency,
                                "skill_gain": value.skill_gain,
                            }
                            for key, value in state.activities.items()
                        },
                        "resonance_nodes": {
                            key: {
                                "label": value.label,
                                "location": value.location,
                                "intensity": value.intensity,
                            }
                            for key, value in state.resonance_nodes.items()
                        },
                        "agents": {
                            key: {
                                "name": value.name,
                                "location": value.location,
                                "energy": value.energy,
                                "hunger": value.hunger,
                                "thirst": value.thirst,
                                "inventory": value.inventory,
                                "inventory_capacity": value.inventory_capacity,
                                "native_language": value.native_language,
                                "language_proficiencies": value.language_proficiencies,
                                "skills": value.skills,
                                "family_group_id": value.family_group_id,
                            }
                            for key, value in state.agents.items()
                        },
                        "family_groups": {
                            key: sorted(value)
                            for key, value in state.family_groups.items()
                        },
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
    return 0


def _print_events(events: list[object]) -> None:
    for event in events:
        print(
            json.dumps(
                {
                    "sequence": event.sequence,
                    "tick": event.world_tick,
                    "type": event.event_type,
                    "actors": event.actor_ids,
                    "location": event.location,
                    "payload": event.payload,
                },
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    raise SystemExit(main())
