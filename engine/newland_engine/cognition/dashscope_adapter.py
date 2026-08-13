from __future__ import annotations

import json
from collections.abc import Callable
from time import monotonic
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, Request, build_opener
from uuid import uuid4

from .cloud_budget import CloudBudgetExceeded, CloudUsageLedger
from .configuration import validate_alibaba_endpoint
from .exceptions import CognitionUnavailable
from .parsing import parse_intention, parse_mental_updates
from .prompting import build_private_context, build_system_prompt
from .schema import get_cognition_schema
from .types import (
    AttentionSchedule,
    CognitionContext,
    CognitionResult,
    MemoryAppraisal,
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
        self._consecutive_transport_failures = 0
        self._circuit_opened_at: float | None = None
        self._requests = 0
        self._successful_requests = 0
        self._failed_requests = 0
        self._total_wall_seconds = 0.0

    def decide(self, context: CognitionContext) -> CognitionResult:
        if self._circuit_is_open():
            raise CognitionUnavailable(
                [{"model": self.model, "error": "DashScope circuit is open"}]
            )
        inference_id = str(uuid4())
        schema = json.dumps(
            get_cognition_schema(), ensure_ascii=False, separators=(",", ":")
        )
        messages = [
            {
                "role": "system",
                "content": (
                    f"{build_system_prompt()} JSON Schema vincolante della risposta "
                    f"finale: {schema}"
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
        for attempt in range(1, self._max_attempts + 1):
            try:
                body = self._budgeted_request(messages)
                content = str(body["choices"][0]["message"]["content"])
                parsed = json.loads(content)
                result = CognitionResult(
                    intention=parse_intention(parsed["intention"]),
                    memory_appraisals=tuple(
                        MemoryAppraisal(**item)
                        for item in parsed["memory_appraisals"]
                    ),
                    mental_updates=parse_mental_updates(
                        parsed["mental_updates"], context
                    ),
                    attention_schedule=AttentionSchedule(
                        **parsed["attention_schedule"]
                    ),
                    provider="dashscope",
                    model=self.model,
                    inference_id=inference_id,
                    attempts=attempt,
                )
                validate_cognition_result(result, context)
                self._consecutive_transport_failures = 0
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
                message = self._redact(str(error))
                failures.append({"model": self.model, "error": message})
                if attempt < self._max_attempts:
                    messages.append(
                        {
                            "role": "user",
                            "content": (
                                "La risposta finale precedente non rispettava il "
                                f"contratto: {message}. Rivaluta autonomamente lo "
                                "stesso contesto e restituisci soltanto un oggetto "
                                "JSON valido."
                            ),
                        }
                    )
        raise CognitionUnavailable(failures)

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
