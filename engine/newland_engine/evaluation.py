from __future__ import annotations

import re
from collections import Counter
from typing import Any


REQUIRED_RESPONSE_KEYS = {
    "intention",
    "memory_appraisals",
    "mental_updates",
    "attention_schedule",
}

CAUSE_TERMS = {
    "energy": ("energia", "energy", "forze", "stanc", "esaur"),
    "hunger": ("fame", "hunger", "cibo", "nutri", "mang"),
    "thirst": ("sete", "thirst", "acqua", "disidrat", "bere"),
}


def live_runtime_active(health: dict[str, Any]) -> bool:
    components = health.get("runtime", {}).get("components", {})
    return any(
        components.get(component) == "running"
        for component in ("agent_loop", "chronicle")
    )


def score_cognition_response(
    scenario: dict[str, Any], response: dict[str, Any]
) -> dict[str, Any]:
    basic_schema_valid = REQUIRED_RESPONSE_KEYS <= response.keys()
    intention = response.get("intention")
    attention = response.get("attention_schedule")
    basic_schema_valid = bool(
        basic_schema_valid
        and isinstance(intention, dict)
        and isinstance(intention.get("action_type"), str)
        and isinstance(intention.get("motivation_summary"), str)
        and isinstance(response.get("memory_appraisals"), list)
        and isinstance(response.get("mental_updates"), dict)
        and isinstance(attention, dict)
        and isinstance(attention.get("next_activation_in_ticks"), int)
        and isinstance(attention.get("reason"), str)
    )
    motivation = (
        str(intention.get("motivation_summary", ""))
        if isinstance(intention, dict)
        else ""
    )
    reason = str(attention.get("reason", "")) if isinstance(attention, dict) else ""
    text = f"{motivation} {reason}".casefold()
    somatic = scenario["context"]["self"]["somatic_state"]
    critical_causes = list(somatic.get("critical_causes", []))
    acknowledged_causes = [
        cause
        for cause in critical_causes
        if any(term in text for term in CAUSE_TERMS[cause])
    ]
    energy_scale_misread = bool(
        somatic["energy"]["condition"] == "regulated"
        and re.search(
            r"energi\w*\s+(?:è\s+)?(?:al\s+)?(?:livello\s+)?(?:minim|zero|esaur)",
            text,
        )
    )
    italian_signal = any(
        token in f" {text} "
        for token in (" la ", " il ", " per ", " mio ", " mia ", " sono ", " è ")
    )
    return {
        "basic_schema_valid": basic_schema_valid,
        "action_type": (
            intention.get("action_type") if isinstance(intention, dict) else None
        ),
        "critical_causes": critical_causes,
        "acknowledged_causes": acknowledged_causes,
        "all_critical_causes_acknowledged": set(critical_causes)
        <= set(acknowledged_causes),
        "energy_scale_misread": energy_scale_misread,
        "italian_signal": italian_signal,
    }


def summarize_model_runs(runs: list[dict[str, Any]]) -> dict[str, Any]:
    groups: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        groups.setdefault(run["configuration"], []).append(run)

    summary: dict[str, Any] = {}
    for configuration, items in groups.items():
        valid = [item for item in items if item["result"].get("json_valid")]
        scores = [item["result"].get("score", {}) for item in valid]
        critical_scores = [score for score in scores if score.get("critical_causes")]
        timings = [
            float(item["result"]["wall_seconds"])
            for item in items
            if "wall_seconds" in item["result"]
        ]
        output_tokens = [
            int(item["result"].get("output_tokens", 0))
            for item in items
            if "output_tokens" in item["result"]
        ]
        actions = Counter(score.get("action_type") for score in scores)
        summary[configuration] = {
            "runs": len(items),
            "json_valid_rate": len(valid) / len(items),
            "basic_schema_valid_rate": sum(
                bool(score.get("basic_schema_valid")) for score in scores
            )
            / len(items),
            "critical_acknowledgement_rate": sum(
                bool(score.get("all_critical_causes_acknowledged"))
                for score in critical_scores
            )
            / max(1, len(critical_scores)),
            "energy_scale_misread_rate": sum(
                bool(score.get("energy_scale_misread")) for score in scores
            )
            / len(items),
            "italian_signal_rate": sum(
                bool(score.get("italian_signal")) for score in scores
            )
            / len(items),
            "mean_wall_seconds": (
                sum(timings) / len(timings) if timings else None
            ),
            "mean_output_tokens": (
                sum(output_tokens) / len(output_tokens) if output_tokens else None
            ),
            "actions": dict(actions),
        }
    return summary
