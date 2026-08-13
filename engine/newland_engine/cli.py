from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import Protocol

from .arrival_factory import ArrivalGenerationUnavailable, GenerativeArrivalFactory
from .arrivals import ArrivalProfile
from .chronicle import (
    ChronicleUnavailable,
    ChronicleWorker,
    GenerativeChroniclerPool,
    OllamaChronicler,
    default_chronicle_path,
)
from .cognition import OllamaCognition
from .cognition.runtime import (
    build_configured_cognition,
    default_cloud_ledger_path,
    default_prompt_ledger_path,
)
from .cognition.prompt_learning import LocalPromptAnnealer, PromptFailureLedger
from .cognition.prompt_registry import PromptRegistry
from .cognition.schema import DEFAULT_PROMPT_REGISTRY
from .event_store import EventStore
from .live import LiveSupervisor
from .models import AgentMind
from .observer import ObserverServer
from .simulation import NewlandSimulation
from .world import replay


class ContinuousSimulation(Protocol):
    def run(self, *, max_activations: int = 8) -> list[object]: ...


def _add_live_cloud_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--allow-cloud-live",
        action="store_true",
        help="explicitly authorize agent-scoped context transfer to DashScope",
    )
    parser.add_argument(
        "--cloud-token-cap",
        type=int,
        help="persistent cumulative token cap shared by selected cloud models",
    )
    parser.add_argument(
        "--cloud-ledger",
        type=Path,
        help="non-canonical cloud usage database",
    )
    parser.add_argument(
        "--env-file",
        type=Path,
        default=Path(".env"),
        help="local ignored file containing DashScope credentials",
    )


def _add_prompt_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--prompt-registry", type=Path, default=DEFAULT_PROMPT_REGISTRY
    )
    parser.add_argument("--prompt-ledger", type=Path)


def _cloud_settings(args: argparse.Namespace) -> dict[str, str]:
    values: dict[str, str] = {}
    if args.env_file.is_file():
        for raw_line in args.env_file.read_text().splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return {
        "api_key": os.environ.get("DASHSCOPE_API_KEY")
        or values.get("DASHSCOPE_API_KEY", ""),
        "base_url": os.environ.get("DASHSCOPE_BASE_URL")
        or values.get("DASHSCOPE_BASE_URL", ""),
    }


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
        "--continuous",
        action="store_true",
        help="keep activating autonomous minds until interrupted",
    )
    _add_live_cloud_options(run_parser)
    _add_prompt_options(run_parser)
    run_parser.add_argument("--selective-attention", action="store_true")
    run_parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Ollama model; repeat for generative failover (default: qwen2.5:3b)",
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
        help="Ollama model; repeat for generative failover (default: qwen2.5:3b)",
    )
    chronicle_parser.add_argument("--batch-size", type=int, default=20)
    chronicle_parser.add_argument("--poll-interval", type=float, default=2.0)
    chronicle_parser.add_argument(
        "--once",
        action="store_true",
        help="process at most one pending batch and exit",
    )
    live_parser = subparsers.add_parser(
        "live", help="run autonomous minds, Chronicle, Observer, and WebGL UI"
    )
    live_parser.add_argument("--host", default="127.0.0.1")
    live_parser.add_argument("--port", type=int, default=8765)
    live_parser.add_argument(
        "--ui-dist", type=Path, default=Path("ui/dist"), help="built WebGL UI"
    )
    live_parser.add_argument("--chronicle-db", type=Path)
    live_parser.add_argument("--model", action="append", dest="models")
    live_parser.add_argument(
        "--reflective-model", action="append", dest="reflective_models"
    )
    live_parser.add_argument(
        "--chronicle-model", action="append", dest="chronicle_models"
    )
    live_parser.add_argument("--agent-weight", type=int, default=8)
    live_parser.add_argument("--batch-size", type=int, default=20)
    live_parser.add_argument("--poll-interval", type=float, default=2.0)
    live_parser.add_argument(
        "--max-activations",
        type=int,
        help="stop after this many complete activation transactions",
    )
    _add_live_cloud_options(live_parser)
    _add_prompt_options(live_parser)
    live_parser.add_argument("--selective-attention", action="store_true")
    live_parser.add_argument("--allow-prompt-annealing", action="store_true")
    live_parser.add_argument(
        "--prompt-annealer-model", default="qwen2.5:3b"
    )

    prompts_parser = subparsers.add_parser(
        "prompts", help="inspect and operate the cognition prompt registry"
    )
    _add_prompt_options(prompts_parser)
    prompt_commands = prompts_parser.add_subparsers(
        dest="prompt_command", required=True
    )
    prompt_commands.add_parser("status")
    prompt_run = prompt_commands.add_parser("run")
    prompt_run.add_argument("--model", default="qwen2.5:3b")
    prompt_commands.add_parser("rollback")

    arrive_parser = subparsers.add_parser(
        "arrive", help="admit a new inhabitant into Newland (identity generated by LLM)"
    )
    arrive_parser.add_argument(
        "--name", required=True, help="full name of the inhabitant"
    )
    arrive_parser.add_argument(
        "--location", default="cittadina_iniziale", help="location of arrival"
    )
    arrive_parser.add_argument(
        "--language", default="it", help="native language of the inhabitant"
    )
    arrive_parser.add_argument(
        "--model",
        default="qwen2.5:3b",
        help="Ollama model for identity generation (default: qwen2.5:3b)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "run":
        models = args.models or ["qwen2.5:3b"]
        cloud = _cloud_settings(args)
        configured = build_configured_cognition(
            ordinary_models=tuple(models),
            reflective_models=tuple(args.reflective_models or ()),
            allow_cloud_live=args.allow_cloud_live,
            api_key=cloud["api_key"],
            base_url=cloud["base_url"],
            cloud_token_cap=args.cloud_token_cap,
            ledger_path=(
                args.cloud_ledger or default_cloud_ledger_path(args.db)
            ),
            prompt_registry_path=args.prompt_registry,
            prompt_ledger_path=(
                args.prompt_ledger or default_prompt_ledger_path(args.db)
            ),
            selective_attention=args.selective_attention,
        )
        try:
            with NewlandSimulation(
                args.db, cognition=configured.cognition
            ) as simulation:
                if args.continuous:
                    try:
                        run_continuously(simulation, emit=_print_events)
                    except KeyboardInterrupt:
                        pass
                else:
                    events = simulation.run(max_activations=args.activations)
                    _print_events(events)
        finally:
            configured.close()
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
        models = args.models or ["qwen2.5:3b"]
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

    if args.command == "live":
        cloud = _cloud_settings(args)
        supervisor = LiveSupervisor(
            args.db,
            chronicle_database_path=args.chronicle_db,
            static_directory=args.ui_dist,
            host=args.host,
            port=args.port,
            models=tuple(args.models or ["qwen2.5:3b"]),
            reflective_models=tuple(args.reflective_models or ()),
            chronicle_models=tuple(args.chronicle_models or ()),
            agent_weight=args.agent_weight,
            batch_size=args.batch_size,
            poll_interval=args.poll_interval,
            allow_cloud_live=args.allow_cloud_live,
            dashscope_api_key=cloud["api_key"],
            dashscope_base_url=cloud["base_url"],
            cloud_token_cap=args.cloud_token_cap,
            cloud_ledger_path=args.cloud_ledger,
            max_activations=args.max_activations,
            prompt_registry_path=args.prompt_registry,
            prompt_ledger_path=args.prompt_ledger,
            allow_prompt_annealing=args.allow_prompt_annealing,
            prompt_annealer_model=args.prompt_annealer_model,
            selective_attention=args.selective_attention,
            emit=_print_events,
        )
        try:
            supervisor.start()
            address = supervisor.address
            if address is not None:
                print(f"Newland live: http://{address[0]}:{address[1]}")
            supervisor.wait()
        except KeyboardInterrupt:
            pass
        finally:
            supervisor.shutdown()
        return 0

    if args.command == "prompts":
        registry = PromptRegistry(args.prompt_registry)
        ledger_path = args.prompt_ledger or default_prompt_ledger_path(args.db)
        with PromptFailureLedger(ledger_path) as ledger:
            if args.prompt_command == "status":
                print(
                    json.dumps(
                        {
                            "registry": registry.health(),
                            "learning": ledger.summary(),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            if args.prompt_command == "run":
                candidate = LocalPromptAnnealer(
                    registry=registry, ledger=ledger, model=args.model
                ).run_once()
                print(
                    json.dumps(
                        {
                            "candidate_version": (
                                candidate.version if candidate is not None else None
                            )
                        },
                        ensure_ascii=False,
                    )
                )
                return 0
            restored = registry.rollback()
            print(json.dumps({"active_version": restored.version}))
            return 0

    if args.command == "arrive":
        print(f"🧬 Generazione identità per '{args.name}' via {args.model}...")
        factory = GenerativeArrivalFactory(model=args.model)
        try:
            profile, provenance = factory.generate(
                name=args.name,
                native_language=args.language,
                location=args.location,
            )
        except ArrivalGenerationUnavailable as error:
            print(
                f"❌ Impossibile generare l'identità dopo {len(error.failures)} tentativi:",
                file=sys.stderr,
            )
            for failure in error.failures:
                print(f"  - {failure['model']}: {failure['error']}", file=sys.stderr)
            return 2
        with NewlandSimulation(args.db, cognition=OllamaCognition(args.model)) as simulation:
            simulation.admit_arrivals((profile,))
        print(f"✨ {args.name} è entrato a Newland ({args.location}) con id {profile.mind.agent_id}!")
        print(f"   Valori: {', '.join(profile.mind.values)}")
        print(f"   Temperamento: {', '.join(profile.mind.temperament)}")
        print(f"   Obiettivi: {', '.join(profile.mind.goals)}")
        print(f"   Skills: {profile.skills}")
        print(f"   Memoria: {profile.arrival_memory[:120]}...")
        print(f"   [Provenance: {provenance.model} · {provenance.inference_id[:8]} · {provenance.attempts} attempt(s)]")
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


def run_continuously(
    simulation: ContinuousSimulation,
    *,
    emit: Callable[[list[object]], None],
    stop_requested: Callable[[], bool] = lambda: False,
) -> int:
    """Run scheduled cognition continuously without choosing agent behavior."""
    activations = 0
    while not stop_requested():
        events = simulation.run(max_activations=1)
        emit(events)
        activations += 1
    return activations


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
            ),
            flush=True,
        )


if __name__ == "__main__":
    raise SystemExit(main())
