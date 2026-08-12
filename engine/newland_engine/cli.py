from __future__ import annotations

import argparse
import json
from pathlib import Path

from .cognition import GenerativeCognitionPool, OllamaCognition
from .event_store import EventStore
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
        help="Ollama model; repeat for generative failover (default: qwen3:4b)",
    )

    subparsers.add_parser("events", help="print the canonical event log")
    subparsers.add_parser("state", help="print materialized world state")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        models = args.models or ["qwen3:4b"]
        cognition = GenerativeCognitionPool(
            [OllamaCognition(model=model) for model in models]
        )
        with NewlandSimulation(args.db, cognition=cognition) as simulation:
            events = simulation.run(max_activations=args.activations)
            _print_events(events)
        return 0

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
                        "agents": {
                            key: {
                                "name": value.name,
                                "location": value.location,
                                "energy": value.energy,
                                "hunger": value.hunger,
                                "thirst": value.thirst,
                            }
                            for key, value in state.agents.items()
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
