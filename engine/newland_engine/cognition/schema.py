from __future__ import annotations

from pathlib import Path
from typing import Any

from .prompt_registry import PromptRegistry


DEFAULT_PROMPT_REGISTRY = (
    Path(__file__).resolve().parents[3] / "docs/prompts/agent-cognition"
)


def get_cognition_schema() -> dict[str, Any]:
    """Compatibility accessor backed by the external prompt registry."""
    return PromptRegistry(DEFAULT_PROMPT_REGISTRY).snapshot().schema
