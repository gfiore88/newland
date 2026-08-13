#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sqlite3
import time
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

from newland_engine.cognition.prompting import build_system_prompt
from newland_engine.cognition.schema import get_cognition_schema
from newland_engine.evaluation import (
    live_runtime_active,
    score_cognition_response,
    summarize_model_runs,
)
from newland_engine.models import MaterialAgentState
from newland_engine.physiology import project_somatic_state, somatic_condition_for


CHECKPOINTS = (7, 34, 44, 75, 85)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replay non canonico di snapshot cognitivi dell'incidente John."
    )
    parser.add_argument("--db", type=Path, default=Path("data/newland.db"))
    parser.add_argument(
        "--model",
        action="append",
        dest="models",
        help="Modello Ollama; ripetibile.",
    )
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--think-phi", action="store_true")
    parser.add_argument(
        "--live-health-url", default="http://127.0.0.1:8765/api/health"
    )
    return parser.parse_args()


def refuse_concurrent_live_runtime(health_url: str) -> None:
    try:
        with urlopen(health_url, timeout=1) as response:
            health = json.loads(response.read().decode())
    except Exception:
        return
    if live_runtime_active(health):
        raise SystemExit(
            "Refusing to bypass Newland's agent-first inference queue while "
            "agent_loop or chronicle is running. Stop `newland live` before evaluation."
        )


def read_events(database: Path) -> list[dict[str, Any]]:
    uri = f"file:{database.resolve()}?mode=ro"
    with sqlite3.connect(uri, uri=True) as connection:
        connection.row_factory = sqlite3.Row
        rows = connection.execute(
            "SELECT * FROM events ORDER BY sequence"
        ).fetchall()
    return [
        {
            **dict(row),
            "actor_ids": json.loads(row["actor_ids"]),
            "recipient_ids": json.loads(row["recipient_ids"]),
            "payload": json.loads(row["payload"]),
        }
        for row in rows
    ]


def build_scenarios(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    registered = next(
        event
        for event in events
        if event["event_type"] == "AgentRegistered"
        and event["payload"].get("name") == "John Flower"
    )
    agent_id = registered["actor_ids"][0]
    world = next(event for event in events if event["event_type"] == "WorldInitialized")
    territory = world["payload"]
    scenarios = []
    for checkpoint in CHECKPOINTS:
        history = [event for event in events if event["sequence"] < checkpoint]
        agent_history = [event for event in history if agent_id in event["actor_ids"]]
        needs_events = [
            event for event in agent_history if event["event_type"] == "NeedsChanged"
        ]
        latest_needs = needs_events[-1]["payload"]["current"]
        tick = max(event["world_tick"] for event in history)
        location = registered["location"]
        inventory: dict[str, float] = dict(registered["payload"].get("inventory", {}))
        for event in agent_history:
            if event["event_type"] == "AgentMoved":
                location = event["payload"]["destination"]
            elif event["event_type"] == "ResourceGathered":
                kind = event["payload"]["resource_kind"]
                inventory[kind] = inventory.get(kind, 0.0) + float(
                    event["payload"]["quantity"]
                )
            elif event["event_type"] == "ResourceConsumed":
                kind = event["payload"]["resource_kind"]
                inventory[kind] = max(
                    0.0,
                    inventory.get(kind, 0.0) - float(event["payload"]["quantity"]),
                )

        state = MaterialAgentState(
            agent_id=agent_id,
            name="John Flower",
            location=location,
            energy=float(latest_needs["energy"]),
            hunger=float(latest_needs["hunger"]),
            thirst=float(latest_needs["thirst"]),
            inventory=inventory,
            inventory_capacity=float(registered["payload"].get("inventory_capacity", 20)),
            native_language=str(registered["payload"].get("native_language", "it")),
            language_proficiencies=registered["payload"].get(
                "language_proficiencies", {"it": 1.0}
            ),
            skills=registered["payload"].get("skills", {}),
        )
        _derive_somatic_history(state, needs_events, tick)
        memories = _consolidated_memories(agent_history)
        resources = [
            {"resource_id": resource_id, **definition}
            for resource_id, definition in territory["resources"].items()
            if definition["location"] == location
        ]
        activities = [
            {"activity_id": activity_id, **definition}
            for activity_id, definition in territory["activities"].items()
            if definition["location"] == location
        ]
        attention = next(
            (
                event
                for event in reversed(agent_history)
                if event["event_type"] == "AttentionScheduled"
            ),
            None,
        )
        context = {
            "self": {
                "agent_id": agent_id,
                "name": state.name,
                "values": [],
                "temperament": [],
                "needs": latest_needs,
                "somatic_state": project_somatic_state(state),
                "goals": _latest_active_goals(agent_history),
                "plans": [],
                "commitments": [],
                "inventory": inventory,
                "inventory_capacity": state.inventory_capacity,
                "native_language": state.native_language,
                "language_proficiencies": state.language_proficiencies,
                "skills": state.skills,
                "family_group_id": None,
                "location": location,
            },
            "local_affordances": {
                "adjacent_locations": sorted(territory["locations"][location]),
                "resources": resources,
                "activities": activities,
                "resonance_nodes": [],
            },
            "action_contracts": {
                "tick_minutes": 10,
                "duration_semantics": (
                    "accepted actions complete only after their duration has elapsed"
                ),
                "rest": {"energy_recovered_per_minute": 0.03},
                "consume": {
                    "carried": {
                        kind: {
                            "available_quantity": quantity,
                            "effects_per_unit": territory["resource_effects"][kind],
                        }
                        for kind, quantity in inventory.items()
                        if quantity > 0.0 and kind in territory["resource_effects"]
                    }
                },
            },
            "social_affordances": {"cooperations": [], "disputes": []},
            "world_tick": tick,
            "activation_reason": (
                attention["payload"]["reason"] if attention else "prima percezione"
            ),
            "recent_memories": memories,
            "beliefs": [],
            "relationships": [],
            "role_interpretations": [],
            "anamnesis_fragments": [],
            "resonance_orientation": None,
            "observations": [
                {
                    "event_id": event["event_id"],
                    "event_type": event["event_type"],
                    "world_tick": event["world_tick"],
                    "location": event["location"],
                    "actor_ids": event["actor_ids"],
                    "payload": event["payload"],
                }
                for event in agent_history[-4:]
            ],
            "nearby_agents": [],
        }
        scenarios.append(
            {
                "id": f"john-before-sequence-{checkpoint}",
                "decision_sequence": checkpoint,
                "context": context,
            }
        )
    return scenarios


def _derive_somatic_history(
    state: MaterialAgentState, needs_events: list[dict[str, Any]], tick: int
) -> None:
    values = {"energy": state.energy, "hunger": state.hunger, "thirst": state.thirst}
    exposure_fields = {
        "energy": "exhaustion_ticks",
        "hunger": "starvation_ticks",
        "thirst": "dehydration_ticks",
    }
    for need, current in values.items():
        current_condition = somatic_condition_for(need, current)
        condition_start = tick
        fatal_start: int | None = None
        previous_value: float | None = None
        for event in needs_events:
            value = float(event["payload"]["current"][need])
            condition = somatic_condition_for(need, value)
            if previous_value is None or condition != somatic_condition_for(
                need, previous_value
            ):
                condition_start = event["world_tick"]
            if condition == "fatal" and fatal_start is None:
                fatal_start = event["world_tick"]
            elif condition != "fatal":
                fatal_start = None
            previous_value = value
        state.somatic_condition_ticks[need] = max(0, tick - condition_start)
        setattr(
            state,
            exposure_fields[need],
            max(0, tick - fatal_start) if fatal_start is not None else 0,
        )
        if len(needs_events) >= 2:
            previous = float(needs_events[-2]["payload"]["current"][need])
            state.need_trends[need] = (
                "rising" if current > previous else "falling" if current < previous else "stable"
            )


def _consolidated_memories(agent_history: list[dict[str, Any]]) -> list[dict[str, Any]]:
    encoded = [
        event for event in agent_history if event["event_type"] == "MemoryEncoded"
    ]
    groups: dict[str, list[dict[str, Any]]] = {}
    for event in encoded:
        key = " ".join(
            "".join(character for character in event["payload"]["summary"].casefold() if character.isalnum() or character.isspace()).split()
        )
        groups.setdefault(key, []).append(event)
    return [
        {
            "memory_id": group[-1]["payload"]["memory_id"],
            "summary": group[-1]["payload"]["summary"],
            "salience": group[-1]["payload"]["salience"],
            "emotional_tone": group[-1]["payload"]["emotional_tone"],
            "confidence": group[-1]["payload"]["confidence"],
            "occurrence_count": len(group),
            "memory_ids": [event["payload"]["memory_id"] for event in group],
            "source_event_ids": [event["payload"]["source_event_id"] for event in group],
        }
        for group in groups.values()
    ]


def _latest_active_goals(agent_history: list[dict[str, Any]]) -> list[str]:
    revision = next(
        (
            event
            for event in reversed(agent_history)
            if event["event_type"] == "GoalRevised"
        ),
        None,
    )
    return list(revision["payload"].get("active_goals", [])) if revision else []


def query_model(
    model: str, scenario: dict[str, Any], *, think: bool
) -> dict[str, Any]:
    payload = {
        "model": model,
        "stream": False,
        "think": think,
        "format": get_cognition_schema(),
        "options": {"temperature": 0.7, "num_ctx": 8192, "num_predict": 2048},
        "messages": [
            {"role": "system", "content": build_system_prompt()},
            {
                "role": "user",
                "content": json.dumps(scenario["context"], ensure_ascii=False),
            },
        ],
    }
    request = Request(
        "http://127.0.0.1:11434/api/chat",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    started = time.monotonic()
    with urlopen(request, timeout=300) as response:
        body = json.loads(response.read().decode())
    wall_seconds = time.monotonic() - started
    content = body.get("message", {}).get("content", "")
    result: dict[str, Any] = {
        "wall_seconds": wall_seconds,
        "load_seconds": body.get("load_duration", 0) / 1e9,
        "prompt_tokens": body.get("prompt_eval_count", 0),
        "prompt_seconds": body.get("prompt_eval_duration", 0) / 1e9,
        "output_tokens": body.get("eval_count", 0),
        "output_seconds": body.get("eval_duration", 0) / 1e9,
        "thinking_chars": len(body.get("message", {}).get("thinking", "")),
        "content": content,
    }
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as error:
        result.update({"json_valid": False, "error": str(error), "score": {}})
        return result
    result.update(
        {
            "json_valid": True,
            "parsed": parsed,
            "score": score_cognition_response(scenario, parsed),
        }
    )
    return result


def main() -> None:
    args = parse_args()
    refuse_concurrent_live_runtime(args.live_health_url)
    if args.samples < 1:
        raise SystemExit("--samples must be positive")
    models = args.models or ["qwen2.5:3b", "qwen3:4b", "phi4-mini-reasoning"]
    scenarios = build_scenarios(read_events(args.db))
    configurations = [(model, False) for model in models]
    if args.think_phi and "phi4-mini-reasoning" in models:
        configurations.append(("phi4-mini-reasoning", True))
    runs = []
    for model, think in configurations:
        configuration = f"{model}|think={str(think).lower()}"
        for scenario in scenarios:
            for sample in range(1, args.samples + 1):
                print(f"{configuration} {scenario['id']} sample={sample}", flush=True)
                try:
                    result = query_model(model, scenario, think=think)
                except Exception as error:
                    result = {"json_valid": False, "error": repr(error)}
                runs.append(
                    {
                        "configuration": configuration,
                        "model": model,
                        "think": think,
                        "scenario_id": scenario["id"],
                        "sample": sample,
                        "result": result,
                    }
                )
    report = {
        "database": str(args.db),
        "canonical_writes": 0,
        "checkpoints": list(CHECKPOINTS),
        "samples_per_checkpoint": args.samples,
        "scenarios": scenarios,
        "summary": summarize_model_runs(runs),
        "runs": runs,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
