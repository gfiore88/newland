from __future__ import annotations

from dataclasses import dataclass
from typing import Literal
from urllib.parse import urlparse


ProviderName = Literal["ollama", "dashscope"]


class LiveCloudConfigurationError(ValueError):
    pass


@dataclass(frozen=True, slots=True)
class LiveCloudModelPolicy:
    token_cap: int
    ordinary_allowed: bool


LIVE_CLOUD_MODEL_POLICIES = {
    "qwen-flash-character": LiveCloudModelPolicy(250_000, True),
    "qwen-plus-character": LiveCloudModelPolicy(200_000, False),
    "qwen3-32b": LiveCloudModelPolicy(200_000, False),
}

EXCLUDED_LIVE_CLOUD_MODELS = {
    "qwen3-next-80b-a3b-thinking",
    "qwen3-235b-a22b-thinking-2507",
}


@dataclass(frozen=True, slots=True)
class ModelSpec:
    provider: ProviderName
    model: str

    @classmethod
    def parse(cls, value: str) -> ModelSpec:
        normalized = value.strip()
        if not normalized:
            raise LiveCloudConfigurationError("model spec cannot be empty")
        for provider in ("ollama", "dashscope"):
            prefix = f"{provider}:"
            if normalized.startswith(prefix):
                model = normalized[len(prefix) :].strip()
                if not model:
                    raise LiveCloudConfigurationError(
                        f"model is required after {prefix}"
                    )
                return cls(provider, model)  # type: ignore[arg-type]
        return cls("ollama", normalized)

    def qualified(self) -> str:
        return f"{self.provider}:{self.model}"


def validate_live_model_specs(
    *,
    ordinary: tuple[ModelSpec, ...],
    reflective: tuple[ModelSpec, ...],
    allow_cloud_live: bool,
    api_key: str,
    base_url: str,
    cloud_token_cap: int | None,
) -> None:
    if not ordinary:
        raise LiveCloudConfigurationError(
            "at least one ordinary cognition model is required"
        )
    cloud_specs = tuple(
        spec
        for spec in (*ordinary, *reflective)
        if spec.provider == "dashscope"
    )
    if not cloud_specs:
        return
    if not allow_cloud_live:
        raise LiveCloudConfigurationError(
            "DashScope live cognition requires --allow-cloud-live"
        )
    if not api_key.strip():
        raise LiveCloudConfigurationError(
            "DashScope live cognition requires DASHSCOPE_API_KEY"
        )
    validate_alibaba_endpoint(base_url)
    if cloud_token_cap is None or cloud_token_cap < 1:
        raise LiveCloudConfigurationError(
            "DashScope live cognition requires a positive --cloud-token-cap"
        )

    for spec in cloud_specs:
        if spec.model in EXCLUDED_LIVE_CLOUD_MODELS:
            raise LiveCloudConfigurationError(
                f"{spec.model} is excluded from live cognition by ADR-0019"
            )
        if spec.model not in LIVE_CLOUD_MODEL_POLICIES:
            raise LiveCloudConfigurationError(
                f"DashScope model is not approved for live cognition: {spec.model}"
            )
    for spec in ordinary:
        if spec.provider != "dashscope":
            continue
        policy = LIVE_CLOUD_MODEL_POLICIES[spec.model]
        if not policy.ordinary_allowed:
            raise LiveCloudConfigurationError(
                f"{spec.model} is restricted to reflective cognition"
            )

    smallest_model_cap = min(
        LIVE_CLOUD_MODEL_POLICIES[spec.model].token_cap for spec in cloud_specs
    )
    if cloud_token_cap > smallest_model_cap:
        raise LiveCloudConfigurationError(
            f"cloud token cap exceeds selected model policy ({smallest_model_cap})"
        )


def validate_alibaba_endpoint(base_url: str) -> None:
    endpoint = urlparse(base_url)
    if (
        endpoint.scheme != "https"
        or endpoint.hostname is None
        or not endpoint.hostname.endswith(".aliyuncs.com")
        or not endpoint.path.rstrip("/").endswith("/compatible-mode/v1")
        or endpoint.username is not None
        or endpoint.password is not None
        or endpoint.query
        or endpoint.fragment
    ):
        raise LiveCloudConfigurationError(
            "DASHSCOPE_BASE_URL must be an Alibaba HTTPS compatible-mode/v1 endpoint"
        )
