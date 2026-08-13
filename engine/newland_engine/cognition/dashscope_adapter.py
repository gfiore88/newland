from __future__ import annotations

import json
import hashlib
from dataclasses import replace
from collections.abc import Callable
from time import monotonic
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from .cloud_budget import CloudBudgetExceeded, CloudUsageLedger
from .configuration import validate_alibaba_endpoint
from .exceptions import CognitionUnavailable
from .parsing import parse_intention, parse_memory_appraisals, parse_mental_updates
from .prompting import build_private_context
from .prompt_learning import PromptFailure, PromptFailureLedger
from .prompt_registry import PromptArtifact, PromptRegistry
from .schema import DEFAULT_PROMPT_REGISTRY
from .types import (
    AttentionSchedule,
    CognitionContext,
    CognitionResult,
    ContextExpansionRequest,
)
from .attention import (
    ATTENTION_SYSTEM_INSTRUCTION,
    COMPACT_SCHEMA_LEGEND,
    compact_schema_contract,
    parse_context_expansion,
    progressive_response_schema,
)
from .validation import validate_cognition_result


Requester = Callable[[Request, float], dict[str, Any]]
Clock = Callable[[], float]


class DashScopeCognition:
    """Live DashScope mind with persistent budget and bounded repair."""

    provider_family = "dashscope"

    def __init__(
        self,
        *,
        model: str,
        api_key: str,
        base_url: str,
        ledger: CloudUsageLedger,
        model_token_cap: int,
        max_output_tokens: int = 2_048,
        timeout_seconds: float = 120.0,
        max_attempts: int = 2,
        circuit_failure_threshold: int = 3,
        circuit_cooldown_seconds: float = 60.0,
        requester: Requester | None = None,
        clock: Clock = monotonic,
        prompt_registry: PromptRegistry | None = None,
        failure_ledger: PromptFailureLedger | None = None,
    ) -> None:
        validate_alibaba_endpoint(base_url)
        if not api_key.strip():
            raise ValueError("DashScope cognition requires an API key")
        if min(model_token_cap, max_output_tokens, max_attempts) < 1:
            raise ValueError("DashScope budgets and attempts must be positive")
        if circuit_failure_threshold < 1 or circuit_cooldown_seconds <= 0:
            raise ValueError("DashScope circuit settings must be positive")
        self.model = model
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._ledger = ledger
        self._model_token_cap = model_token_cap
        self._max_output_tokens = max_output_tokens
        self._timeout_seconds = timeout_seconds
        self._max_attempts = max_attempts
        self._failure_threshold = circuit_failure_threshold
        self._cooldown_seconds = circuit_cooldown_seconds
        self._requester = requester or _open_json
        self._clock = clock
        self.prompt_registry = prompt_registry or PromptRegistry(
            DEFAULT_PROMPT_REGISTRY
        )
        self.failure_ledger = failure_ledger
        self._consecutive_transport_failures = 0
        self._circuit_opened_at: float | None = None
        self._requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._total_wall_seconds = 0.0

    def decide(
        self, context: CognitionContext
    ) -> CognitionResult | ContextExpansionRequest:
        if self._circuit_is_open():
            raise CognitionUnavailable(
                [{"model": self.model, "error": "DashScope circuit is open"}]
            )
        inference_id = str(uuid4())
        artifact = self.prompt_registry.snapshot()
        response_schema = (
            progressive_response_schema(artifact.schema)
            if context.attention_level != "full"
            else artifact.schema
        )
        progressive = context.attention_level != "full"
        schema = (
            compact_schema_contract(response_schema)
            if progressive
            else json.dumps(
                response_schema, ensure_ascii=False, separators=(",", ":")
            )
        )
        attention_instruction = (
            f" {ATTENTION_SYSTEM_INSTRUCTION}"
            if context.attention_level != "full"
            else ""
        )
        contract_legend = f" {COMPACT_SCHEMA_LEGEND}" if progressive else ""
        effective_system_prompt = (
            f"{artifact.system_prompt}{attention_instruction}{contract_legend}"
        )
        effective_version = artifact.version
        effective_prompt_hash = artifact.prompt_hash
        effective_schema_hash = artifact.schema_hash
        if progressive:
            effective_version += "+selective-attention-v1"
            effective_prompt_hash = hashlib.sha256(
                effective_system_prompt.encode()
            ).hexdigest()
            effective_schema_hash = hashlib.sha256(schema.encode()).hexdigest()
        effective_artifact = replace(
            artifact,
            version=effective_version,
            prompt_hash=effective_prompt_hash,
            schema_hash=effective_schema_hash,
        )
        messages = [
            {
                "role": "system",
                "content": (
                    f"{effective_system_prompt} "
                    f"{'Contratto compatto' if progressive else 'JSON Schema'} "
                    f"vincolante della risposta finale: {schema}"
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    build_private_context(context), ensure_ascii=False
                ),
            },
        ]
        failures: list[dict[str, str]] = []
        contract_failed = False
        for attempt in range(1, self._max_attempts + 1):
            parsed_response: Any = None
            try:
                body = self._budgeted_request(messages)
                content = str(body["choices"][0]["message"]["content"])
                parsed_response = json.loads(content)
                if (
                    context.attention_level != "full"
                    and "context_expansion" in parsed_response
                ):
                    expansion = parse_context_expansion(parsed_response)
                    self._consecutive_transport_failures = 0
                    self.prompt_registry.observe(
                        artifact.version,
                        first_attempt_valid=attempt == 1,
                        provider=self.provider_family,
                        model=self.model,
                        tokens=_reported_total_tokens(body),
                    )
                    return expansion
                result = CognitionResult(
                    intention=parse_intention(parsed_response["intention"]),
                    memory_appraisals=parse_memory_appraisals(
                        parsed_response["memory_appraisals"]
                    ),
                    mental_updates=parse_mental_updates(
                        parsed_response["mental_updates"], context
                    ),
                    attention_schedule=AttentionSchedule(
                        **parsed_response["attention_schedule"]
                    ),
                    provider="dashscope",
                    model=self.model,
                    inference_id=inference_id,
                    attempts=attempt,
                    prompt_version=effective_version,
                    prompt_hash=effective_prompt_hash,
                    schema_hash=effective_schema_hash,
                )
                validate_cognition_result(result, context)
                self._consecutive_transport_failures = 0
                self.prompt_registry.observe(
                    artifact.version,
                    first_attempt_valid=attempt == 1,
                    provider=self.provider_family,
                    model=self.model,
                    tokens=_reported_total_tokens(body),
                )
                return result
            except _TerminalCloudFailure as error:
                failures.append({"model": self.model, "error": str(error)})
                raise CognitionUnavailable(
                    failures, stop_provider_family="dashscope"
                ) from error
            except CloudBudgetExceeded as error:
                failures.append({"model": self.model, "error": str(error)})
                raise CognitionUnavailable(
                    failures, stop_provider_family="dashscope"
                ) from error
            except _TransportFailure as error:
                failures.append({"model": self.model, "error": str(error)})
                self._record_transport_failure()
                break
            except (
                AttributeError,
                KeyError,
                TypeError,
                ValueError,
                json.JSONDecodeError,
            ) as error:
                contract_failed = True
                self._record_prompt_failure(effective_artifact, attempt, error)
                message = self._redact(str(error))
                message += _material_contract_detail(parsed_response, context)
                failures.append({"model": self.model, "error": message})
                if attempt < self._max_attempts:
                    messages.extend(
                        [
                            {
                                "role": "assistant",
                                "content": locals().get("content", ""),
                            },
                            {
                                "role": "user",
                                "content": (
                                    "La risposta finale precedente non rispettava il "
                                    f"contratto: {message}. Rivaluta autonomamente lo "
                                    "stesso contesto e restituisci soltanto un oggetto "
                                    "JSON valido."
                                ),
                            },
                        ]
                    )
        if contract_failed:
            self.prompt_registry.observe(
                artifact.version,
                first_attempt_valid=False,
                provider=self.provider_family,
                model=self.model,
            )
        raise CognitionUnavailable(failures)

    def _record_prompt_failure(
        self, artifact: PromptArtifact, attempt: int, error: Exception
    ) -> None:
        if self.failure_ledger is None:
            return
        message = str(error)
        lowered = message.lower()
        if "source_event_id" in lowered or "source_ids" in lowered:
            code = "reference.source_field"
        elif "consume" in lowered or "carried" in lowered:
            code = "material.consume_unavailable"
        elif isinstance(error, json.JSONDecodeError):
            code = "response.invalid_json"
        elif isinstance(error, (KeyError, AttributeError, TypeError)):
            code = "response.shape"
        else:
            code = "contract.invalid"
        field = str(error.args[0]) if isinstance(error, KeyError) and error.args else "response"
        self.failure_ledger.record(
            PromptFailure(
                violation_code=code,
                field_path=field,
                observed_type=type(error).__name__,
                provider=self.provider_family,
                model=self.model,
                prompt_version=artifact.version,
                prompt_hash=artifact.prompt_hash,
                schema_hash=artifact.schema_hash,
                attempt=attempt,
                detail=message,
            )
        )

    def health(self) -> dict[str, object]:
        ledger = self._ledger.snapshot()
        return {
            "provider": "dashscope",
            "model": self.model,
            "requests": self._requests,
            "successful_requests": self._successful_requests,
            "failed_requests": self._failed_requests,
            "total_wall_seconds": self._total_wall_seconds,
            "circuit_state": "open" if self._circuit_is_open() else "closed",
            "consecutive_transport_failures": self._consecutive_transport_failures,
            "budget": ledger.to_dict(),
        }

    def _budgeted_request(self, messages: list[dict[str, str]]) -> dict[str, Any]:
        serialized = json.dumps(messages, ensure_ascii=False)
        estimated_input = max(1, (len(serialized) + 3) // 4)
        reservation = self._ledger.reserve(
            provider="dashscope",
            model=self.model,
            estimated_input_tokens=estimated_input,
            max_output_tokens=self._max_output_tokens,
            model_cap=self._model_token_cap,
        )
        payload = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": self._max_output_tokens,
            "stream": False,
            "response_format": {"type": "json_object"},
        }
        request = Request(
            f"{self._base_url}/chat/completions",
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self._api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        started = self._clock()
        self._requests += 1
        try:
            body = self._requester(request, self._timeout_seconds)
        except HTTPError as error:
            elapsed = max(0.0, self._clock() - started)
            self._settle_unknown(reservation, elapsed)
            message = self._redact(_http_error_message(error))
            if error.code in {401, 402, 403}:
                raise _TerminalCloudFailure(message) from error
            raise _TransportFailure(message) from error
        except (OSError, URLError, TimeoutError) as error:
            elapsed = max(0.0, self._clock() - started)
            self._settle_unknown(reservation, elapsed)
            raise _TransportFailure(self._redact(str(error))) from error

        elapsed = max(0.0, self._clock() - started)
        usage = body.get("usage")
        if isinstance(usage, dict):
            prompt = _non_negative_int(usage.get("prompt_tokens"))
            completion = _non_negative_int(usage.get("completion_tokens"))
            details = usage.get("completion_tokens_details")
            reasoning = (
                _non_negative_int(details.get("reasoning_tokens"))
                if isinstance(details, dict)
                else 0
            )
            reported_total = usage.get("total_tokens")
            total = (
                _non_negative_int(reported_total)
                if reported_total is not None
                else None
            )
        else:
            prompt = completion = reasoning = 0
            total = None
        self._ledger.settle(
            reservation,
            prompt_tokens=prompt,
            completion_tokens=completion,
            reasoning_tokens=reasoning,
            total_tokens=total,
        )
        self._successful_requests += 1
        self._total_wall_seconds += elapsed
        return body

    def _settle_unknown(self, reservation: Any, elapsed: float) -> None:
        self._ledger.settle(
            reservation,
            prompt_tokens=0,
            completion_tokens=0,
            reasoning_tokens=0,
            total_tokens=None,
        )
        self._failed_requests += 1
        self._total_wall_seconds += elapsed

    def _record_transport_failure(self) -> None:
        self._consecutive_transport_failures += 1
        if self._consecutive_transport_failures >= self._failure_threshold:
            self._circuit_opened_at = self._clock()

    def _circuit_is_open(self) -> bool:
        if self._circuit_opened_at is None:
            return False
        if self._clock() - self._circuit_opened_at < self._cooldown_seconds:
            return True
        self._circuit_opened_at = None
        self._consecutive_transport_failures = 0
        return False

    def _redact(self, message: str) -> str:
        return message.replace(self._api_key, "[REDACTED]")


class _TerminalCloudFailure(RuntimeError):
    pass


class _TransportFailure(RuntimeError):
    pass


def _open_json(request: Request, timeout: float) -> dict[str, Any]:
    with build_opener(_NoRedirectHandler).open(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def _http_error_message(error: HTTPError) -> str:
    try:
        raw_body = error.read()
    finally:
        error.close()
    try:
        payload = json.loads(raw_body.decode("utf-8"))
    except (AttributeError, UnicodeDecodeError, json.JSONDecodeError):
        return f"HTTP {error.code}: {error.reason}"
    return (
        f"HTTP {error.code} {payload.get('code', 'unknown')}: "
        f"{payload.get('message', error.reason)}"
    )


def _non_negative_int(value: Any) -> int:
    try:
        return max(0, int(value or 0))
    except (TypeError, ValueError):
        return 0


def _reported_total_tokens(body: dict[str, Any]) -> int | None:
    usage = body.get("usage")
    if not isinstance(usage, dict) or usage.get("total_tokens") is None:
        return None
    return _non_negative_int(usage["total_tokens"])


class _NoRedirectHandler(HTTPRedirectHandler):
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


def _material_contract_detail(
    parsed_response: Any, context: CognitionContext
) -> str:
    if not isinstance(parsed_response, dict):
        return ""
    intention = parsed_response.get("intention")
    if not isinstance(intention, dict) or intention.get("action_type") != "consume":
        return ""
    consume = context.action_contracts.get("consume", {})
    carried = consume.get("carried", {}) if isinstance(consume, dict) else {}
    if carried:
        identifiers = ", ".join(sorted(str(key) for key in carried))
        return (
            " Per consume, resource_id deve essere uno dei carried disponibili: "
            f"{identifiers}."
        )
    return (
        " action_contracts.consume.carried è vuoto: consume non è "
        "materialmente disponibile; non inventare resource_id."
    )
