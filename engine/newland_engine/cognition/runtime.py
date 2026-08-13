from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.request import Request

from .cloud_budget import CloudUsageLedger
from .configuration import (
    LIVE_CLOUD_MODEL_POLICIES,
    ModelSpec,
    validate_live_model_specs,
)
from .dashscope_adapter import DashScopeCognition
from .llm_adapter import OllamaCognition
from .provider import CognitionProvider, GenerativeCognitionPool, RoutedCognition
from .prompt_learning import PromptFailureLedger
from .prompt_registry import PromptRegistry
from .schema import DEFAULT_PROMPT_REGISTRY
from .attention import ProgressiveCognition


DashScopeRequester = Callable[[Request, float], dict[str, Any]]


@dataclass(slots=True)
class ConfiguredCognition:
    cognition: CognitionProvider
    ordinary_specs: tuple[ModelSpec, ...]
    reflective_specs: tuple[ModelSpec, ...]
    cloud_providers: tuple[DashScopeCognition, ...]
    ledger: CloudUsageLedger | None = None
    prompt_registry: PromptRegistry | None = None
    prompt_failure_ledger: PromptFailureLedger | None = None
    attention_controller: ProgressiveCognition | None = None
    _closed: bool = False
    _final_health: dict[str, object] | None = None

    def health(self) -> dict[str, object]:
        if self._final_health is not None:
            return self._final_health
        return {
            "configured_models": {
                "ordinary": [spec.qualified() for spec in self.ordinary_specs],
                "reflective": [
                    spec.qualified() for spec in self.reflective_specs
                ],
            },
            "cloud_budget": (
                self.ledger.snapshot().to_dict() if self.ledger is not None else None
            ),
            "cloud_providers": [
                provider.health() for provider in self.cloud_providers
            ],
            "prompt_registry": (
                self.prompt_registry.health()
                if self.prompt_registry is not None
                else None
            ),
            "prompt_learning": (
                self.prompt_failure_ledger.summary()
                if self.prompt_failure_ledger is not None
                else None
            ),
            "selective_attention": (
                self.attention_controller.health()
                if self.attention_controller is not None
                else {"enabled": False}
            ),
        }

    def close(self) -> None:
        if self._closed:
            return
        self._final_health = self.health()
        self._closed = True
        if self.ledger is not None:
            self.ledger.close()
        if self.prompt_failure_ledger is not None:
            self.prompt_failure_ledger.close()

    def __enter__(self) -> ConfiguredCognition:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()


def build_configured_cognition(
    *,
    ordinary_models: tuple[str, ...],
    reflective_models: tuple[str, ...],
    allow_cloud_live: bool,
    api_key: str,
    base_url: str,
    cloud_token_cap: int | None,
    ledger_path: str | Path,
    prompt_registry_path: str | Path = DEFAULT_PROMPT_REGISTRY,
    prompt_ledger_path: str | Path | None = None,
    selective_attention: bool = False,
    dashscope_requester: DashScopeRequester | None = None,
) -> ConfiguredCognition:
    ordinary_specs = tuple(ModelSpec.parse(value) for value in ordinary_models)
    reflective_specs = (
        tuple(ModelSpec.parse(value) for value in reflective_models)
        if reflective_models
        else ordinary_specs
    )
    validate_live_model_specs(
        ordinary=ordinary_specs,
        reflective=reflective_specs,
        allow_cloud_live=allow_cloud_live,
        api_key=api_key,
        base_url=base_url,
        cloud_token_cap=cloud_token_cap,
    )
    has_cloud = any(
        spec.provider == "dashscope"
        for spec in (*ordinary_specs, *reflective_specs)
    )
    ledger = (
        CloudUsageLedger(ledger_path, global_cap=cloud_token_cap)
        if has_cloud and cloud_token_cap is not None
        else None
    )
    cloud_providers: list[DashScopeCognition] = []
    prompt_registry = PromptRegistry(prompt_registry_path)
    prompt_failure_ledger = PromptFailureLedger(
        prompt_ledger_path or default_prompt_ledger_path(ledger_path)
    )

    def provider_for(spec: ModelSpec) -> CognitionProvider:
        if spec.provider == "ollama":
            return OllamaCognition(
                model=spec.model,
                prompt_registry=prompt_registry,
                failure_ledger=prompt_failure_ledger,
            )
        assert ledger is not None
        provider = DashScopeCognition(
            model=spec.model,
            api_key=api_key,
            base_url=base_url,
            ledger=ledger,
            model_token_cap=LIVE_CLOUD_MODEL_POLICIES[spec.model].token_cap,
            requester=dashscope_requester,
            prompt_registry=prompt_registry,
            failure_ledger=prompt_failure_ledger,
        )
        cloud_providers.append(provider)
        return provider

    try:
        ordinary = GenerativeCognitionPool(
            [provider_for(spec) for spec in ordinary_specs]
        )
        reflective = GenerativeCognitionPool(
            [provider_for(spec) for spec in reflective_specs]
        )
    except BaseException:
        if ledger is not None:
            ledger.close()
        prompt_failure_ledger.close()
        raise
    routed = RoutedCognition(ordinary, reflective)
    attention_controller = ProgressiveCognition(routed) if selective_attention else None
    return ConfiguredCognition(
        cognition=attention_controller or routed,
        ordinary_specs=ordinary_specs,
        reflective_specs=reflective_specs,
        cloud_providers=tuple(cloud_providers),
        ledger=ledger,
        prompt_registry=prompt_registry,
        prompt_failure_ledger=prompt_failure_ledger,
        attention_controller=attention_controller,
    )


def default_cloud_ledger_path(database_path: str | Path) -> Path:
    database = Path(database_path)
    return database.with_name(f"{database.stem}.cloud-runtime.db")


def default_prompt_ledger_path(database_path: str | Path) -> Path:
    database = Path(database_path)
    stem = database.stem.removesuffix(".cloud-runtime")
    return database.with_name(f"{stem}.prompt-runtime.db")
