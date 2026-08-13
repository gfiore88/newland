"""Bounded DashScope client for offline cognition evaluation only.

This module is deliberately outside ``newland_engine.cognition`` and is not
imported by the live CLI.  It must never be used as a runtime failover.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from time import monotonic
from typing import Any, Callable
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from .cognition.parsing import (
    parse_intention,
    parse_memory_appraisals,
    parse_mental_updates,
)
from .cognition.prompting import build_private_context, build_system_prompt
from .cognition.schema import get_cognition_schema
from .cognition.types import (
    AttentionSchedule,
    CognitionContext,
    CognitionResult,
)
from .cognition.validation import validate_cognition_result


class CloudEvaluationConfigurationError(ValueError):
    """Raised before any request when the offline safety gates are not met."""


class CloudQuotaExhausted(RuntimeError):
    """Raised when a local cap or the remote free-only quota stops evaluation."""


@dataclass(frozen=True, slots=True)
class ModelPolicy:
    token_cap: int
    disagreement_only: bool = False
    structured_output: bool = True


MODEL_POLICIES = {
    "qwen-flash-character": ModelPolicy(250_000),
    "qwen-plus-character": ModelPolicy(200_000),
    "qwen3-32b": ModelPolicy(200_000),
    "qwen3-next-80b-a3b-thinking": ModelPolicy(
        100_000, disagreement_only=True, structured_output=False
    ),
    "qwen3-235b-a22b-thinking-2507": ModelPolicy(
        75_000, disagreement_only=True, structured_output=False
    ),
}


@dataclass(slots=True)
class TokenUsage:
    prompt_tokens: int = 0
    completion_tokens: int = 0
    reasoning_tokens: int = 0
    total_tokens: int = 0
    requests: int = 0
    wall_seconds: float = 0.0


Requester = Callable[[Request, float], dict[str, Any]]


class DashScopeEvaluationCognition:
    """OpenAI-compatible DashScope adapter gated for finite offline tests."""

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        base_url: str,
        allow_cloud: bool,
        disagreement_case: bool = False,
        token_cap: int | None = None,
        max_output_tokens: int = 2_048,
        timeout_seconds: float = 120.0,
        max_attempts: int = 2,
        requester: Requester | None = None,
    ) -> None:
        if not allow_cloud:
            raise CloudEvaluationConfigurationError(
                "cloud evaluation requires explicit --allow-cloud opt-in"
            )
        if not api_key.strip():
            raise CloudEvaluationConfigurationError(
                "cloud evaluation requires DASHSCOPE_API_KEY"
            )
        endpoint = urlparse(base_url)
        if (
            endpoint.scheme != "https"
            or endpoint.hostname is None
            or not endpoint.hostname.endswith(".aliyuncs.com")
            or not endpoint.path.rstrip("/").endswith("/compatible-mode/v1")
            or endpoint.username is not None
            or endpoint.query
            or endpoint.fragment
        ):
            raise CloudEvaluationConfigurationError(
                "DASHSCOPE_BASE_URL must be an Alibaba HTTPS compatible-mode/v1 endpoint"
            )
        if model not in MODEL_POLICIES:
            raise CloudEvaluationConfigurationError(
                f"cloud evaluation model is not approved by ADR-0018: {model}"
            )
        policy = MODEL_POLICIES[model]
        if policy.disagreement_only and not disagreement_case:
            raise CloudEvaluationConfigurationError(
                f"{model} is restricted to an explicit disagreement case"
            )
        if max_output_tokens < 1 or max_attempts < 1:
            raise CloudEvaluationConfigurationError(
                "output budget and attempts must be positive"
            )
        if token_cap is not None and token_cap < 1:
            raise CloudEvaluationConfigurationError("local token cap must be positive")
        self.model = model
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._policy = policy
        self._token_cap = min(token_cap or policy.token_cap, policy.token_cap)
        self._max_output_tokens = max_output_tokens
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._requester = requester or _open_json
        self.usage = TokenUsage()

    def decide(self, context: CognitionContext) -> CognitionResult:
        inference_id = str(uuid4())
        canonical_schema = json.dumps(
            get_cognition_schema(), ensure_ascii=False, separators=(",", ":")
        )
        messages = [
            {
                "role": "system",
                "content": (
                    f"{build_system_prompt()} JSON Schema vincolante della risposta "
                    f"finale: {canonical_schema}"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    build_private_context(context), ensure_ascii=False
                ),
            },
        ]
        failures: list[str] = []
        for attempt in range(1, self._max_attempts + 1):
            last_failure = "risposta non valida"
            self._reserve_request(messages)
            try:
                body, elapsed = self._request(messages)
                self._record_usage(body.get("usage", {}), elapsed)
                content = self._final_content(body)
                parsed = json.loads(content)
                result = CognitionResult(
                    intention=parse_intention(parsed["intention"]),
                    memory_appraisals=parse_memory_appraisals(
                        parsed["memory_appraisals"]
                    ),
                    mental_updates=parse_mental_updates(
                        parsed["mental_updates"], context
                    ),
                    attention_schedule=AttentionSchedule(
                        **parsed["attention_schedule"]
                    ),
                    provider="dashscope-evaluation",
                    model=self.model,
                    inference_id=inference_id,
                    attempts=attempt,
                )
                validate_cognition_result(result, context)
                return result
            except CloudQuotaExhausted:
                raise
            except HTTPError as error:
                if error.code in {401, 402, 403}:
                    raise CloudQuotaExhausted(
                        self._redact(self._http_error_message(error))
                    ) from error
                last_failure = self._redact(str(error))
                failures.append(last_failure)
            except (
                AttributeError,
                KeyError,
                TypeError,
                ValueError,
                OSError,
                URLError,
            ) as error:
                last_failure = self._redact(str(error))
                failures.append(last_failure)
            if attempt < self._max_attempts:
                messages.append(
                    {
                        "role": "user",
                        "content": (
                            "La risposta finale precedente non rispettava il contratto: "
                            f"{last_failure}. "
                            "Rivaluta autonomamente lo stesso contesto e restituisci "
                            "soltanto un oggetto JSON valido."
                        ),
                    }
                )
        raise RuntimeError(
            f"DashScope evaluation failed after {self._max_attempts} attempts: "
            + "; ".join(failures)
        )

    def report_metrics(self) -> dict[str, int | float | str]:
        """Return persistence-safe metrics; private reasoning is never included."""
        return {
            "provider": "dashscope-evaluation",
            "model": self.model,
            "requests": self.usage.requests,
            "prompt_tokens": self.usage.prompt_tokens,
            "completion_tokens": self.usage.completion_tokens,
            "reasoning_tokens": self.usage.reasoning_tokens,
            "total_tokens": self.usage.total_tokens,
            "wall_seconds": self.usage.wall_seconds,
            "token_cap": self._token_cap,
        }

    def _request(
        self, messages: list[dict[str, str]]
    ) -> tuple[dict[str, Any], float]:
        payload: dict[str, Any] = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": self._max_output_tokens,
            "stream": False,
        }
        if self._policy.structured_output:
            payload["response_format"] = {"type": "json_object"}
        request = Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started = monotonic()
        body = self._requester(request, self._timeout_seconds)
        return body, monotonic() - started

    def _reserve_request(self, messages: list[dict[str, str]]) -> None:
        serialized = json.dumps(messages, ensure_ascii=False)
        estimated_input = max(1, (len(serialized) + 3) // 4)
        reservation = estimated_input + self._max_output_tokens
        if self.usage.total_tokens + reservation > self._token_cap:
            raise CloudQuotaExhausted(
                f"local token cap would be exceeded for {self.model}"
            )

    def _record_usage(self, usage: Any, elapsed: float) -> None:
        values = usage if isinstance(usage, dict) else {}
        prompt = _non_negative_int(values.get("prompt_tokens"))
        completion = _non_negative_int(values.get("completion_tokens"))
        reported_total = _non_negative_int(values.get("total_tokens"))
        details = values.get("completion_tokens_details", {})
        reasoning = (
            _non_negative_int(details.get("reasoning_tokens"))
            if isinstance(details, dict)
            else 0
        )
        total = reported_total or prompt + completion
        self.usage.prompt_tokens += prompt
        self.usage.completion_tokens += completion
        self.usage.reasoning_tokens += reasoning
        self.usage.total_tokens += total
        self.usage.requests += 1
        self.usage.wall_seconds += elapsed
        if self.usage.total_tokens > self._token_cap:
            raise CloudQuotaExhausted(
                f"local token cap exceeded for {self.model}"
            )

    @staticmethod
    def _final_content(body: dict[str, Any]) -> str:
        return str(body["choices"][0]["message"]["content"])

    def _redact(self, message: str) -> str:
        return message.replace(self._api_key, "[REDACTED]")

    @staticmethod
    def _http_error_message(error: HTTPError) -> str:
        try:
            raw_body = error.read()
        finally:
            error.close()
        try:
            payload = json.loads(raw_body.decode("utf-8"))
        except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
            return f"HTTP {error.code}: {error.reason}"
        code = payload.get("code", "unknown")
        message = payload.get("message", error.reason)
        return f"HTTP {error.code} {code}: {message}"


def _open_json(request: Request, timeout: float) -> dict[str, Any]:
    with build_opener(_NoRedirectHandler).open(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


class _NoRedirectHandler(HTTPRedirectHandler):
    """Never forward the bearer credential through an HTTP redirect."""

    def redirect_request(
        self,
        request: Request,
        file_pointer: Any,
        code: int,
        message: str,
        headers: Any,
        new_url: str,
    ) -> None:
        return None
