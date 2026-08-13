#!/usr/bin/env python3
"""Finite, non-canonical DashScope protocol benchmark for ADR-0018."""

from __future__ import annotations

import argparse
import json
import os
from dataclasses import asdict
from pathlib import Path
from urllib.request import urlopen

from newland_engine.cloud_evaluation import (
    MODEL_POLICIES,
    CloudEvaluationConfigurationError,
    CloudQuotaExhausted,
    DashScopeEvaluationCognition,
)
from newland_engine.cognition import CognitionContext
from newland_engine.evaluation import live_runtime_active
from newland_engine.models import (
    AgentMind,
    EventEnvelope,
    MaterialAgentState,
    world_time_for_tick,
)
from newland_engine.perception import Observation


FIXTURE_VERSION = "cloud-protocol-v1"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Benchmark cloud offline e non canonico; non modifica Newland."
        )
    )
    parser.add_argument(
        "--allow-cloud",
        action="store_true",
        help="autorizza esplicitamente l'invio del fixture sanitizzato",
    )
    parser.add_argument(
        "--model",
        choices=tuple(MODEL_POLICIES),
        default="qwen-flash-character",
    )
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--max-output-tokens", type=int, default=2_048)
    parser.add_argument("--token-cap", type=int)
    parser.add_argument("--disagreement-case", action="store_true")
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--output", type=Path)
    parser.add_argument(
        "--live-health-url", default="http://127.0.0.1:8765/api/health"
    )
    return parser.parse_args()


def load_local_env(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def refuse_concurrent_live_runtime(health_url: str) -> None:
    try:
        with urlopen(health_url, timeout=1) as response:
            health = json.loads(response.read().decode("utf-8"))
    except Exception:
        return
    if live_runtime_active(health):
        raise SystemExit(
            "Benchmark rifiutato: agent_loop o chronicle è attivo. "
            "Ferma `newland live` prima della valutazione cloud."
        )


def sanitized_protocol_context() -> CognitionContext:
    """Small fictional fixture used only to establish API compatibility."""
    observed_body_change = EventEnvelope(
        event_type="NeedsChanged",
        world_tick=12,
        world_time=world_time_for_tick(12),
        actor_ids=("fixture-newlander-001",),
        location="luogo_fixture",
        payload={
            "previous": {"energy": 0.71, "hunger": 0.39, "thirst": 0.33},
            "current": {"energy": 0.68, "hunger": 0.42, "thirst": 0.35},
        },
        visibility="private",
        recipient_ids=("fixture-newlander-001",),
        event_id="fixture-body-event-001",
    )
    return CognitionContext(
        mind=AgentMind(
            agent_id="fixture-newlander-001",
            name="Abitante Fixture",
            values=["autonomia", "prudenza"],
            temperament=["riflessivo", "concreto"],
            goals=["comprendere il proprio stato senza forzare conclusioni"],
        ),
        material_state=MaterialAgentState(
            agent_id="fixture-newlander-001",
            name="Abitante Fixture",
            location="luogo_fixture",
            energy=0.68,
            hunger=0.42,
            thirst=0.35,
            inventory={},
            inventory_capacity=14.0,
            native_language="it",
            language_proficiencies={"it": 1.0},
            skills={"osservazione": 0.5},
        ),
        observations=(Observation(observed_body_change),),
        nearby_agents=(),
        activation_reason="controllo periodico del proprio stato",
        world_tick=12,
        adjacent_locations=("luogo_fixture_adiacente",),
        action_contracts={
            "tick_minutes": 10,
            "duration_semantics": "le azioni richiedono tempo materiale",
            "consume": {"carried": {}},
        },
    )


def main() -> int:
    args = parse_args()
    if args.samples < 1:
        raise SystemExit("--samples deve essere positivo")
    refuse_concurrent_live_runtime(args.live_health_url)
    local_env = load_local_env(args.env_file)
    api_key = os.environ.get("DASHSCOPE_API_KEY") or local_env.get(
        "DASHSCOPE_API_KEY", ""
    )
    base_url = os.environ.get("DASHSCOPE_BASE_URL") or local_env.get(
        "DASHSCOPE_BASE_URL", ""
    )
    try:
        client = DashScopeEvaluationCognition(
            model=args.model,
            api_key=api_key,
            base_url=base_url,
            allow_cloud=args.allow_cloud,
            disagreement_case=args.disagreement_case,
            token_cap=args.token_cap,
            max_output_tokens=args.max_output_tokens,
        )
    except CloudEvaluationConfigurationError as error:
        raise SystemExit(str(error)) from error

    context = sanitized_protocol_context()
    runs = []
    for sample in range(1, args.samples + 1):
        try:
            result = client.decide(context)
        except (CloudQuotaExhausted, RuntimeError) as error:
            runs.append({"sample": sample, "ok": False, "error": str(error)})
            break
        runs.append(
            {
                "sample": sample,
                "ok": True,
                "result": asdict(result),
            }
        )
    report = {
        "fixture_version": FIXTURE_VERSION,
        "canonical_writes": 0,
        "samples_requested": args.samples,
        "configuration": {
            "model": args.model,
            "max_output_tokens": args.max_output_tokens,
            "disagreement_case": args.disagreement_case,
            "stateless": True,
        },
        "metrics": client.report_metrics(),
        "runs": runs,
        "limitations": [
            "Questo fixture misura compatibilità del protocollo, non qualità cognitiva.",
            "Nessun risultato viene promosso nel mondo canonico.",
        ],
    }
    rendered = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered)
    else:
        print(rendered, end="")
    return 0 if runs and runs[-1]["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
