import json
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .exceptions import CognitionUnavailable
from .types import AttentionSchedule, CognitionContext, CognitionResult
from .validation import validate_cognition_result
from .prompting import build_private_context
from .prompt_learning import PromptFailure, PromptFailureLedger
from .prompt_registry import PromptRegistry
from .schema import DEFAULT_PROMPT_REGISTRY
from .parsing import parse_intention, parse_memory_appraisals, parse_mental_updates


class OllamaCognition:
    provider_family = "ollama"

    def __init__(
        self,
        model: str = "qwen2.5:3b",
        endpoint: str = "http://127.0.0.1:11434/api/chat",
        timeout_seconds: float = 120.0,
        max_attempts: int = 3,
        prompt_registry: PromptRegistry | None = None,
        failure_ledger: PromptFailureLedger | None = None,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts
        self.prompt_registry = prompt_registry or PromptRegistry(
            DEFAULT_PROMPT_REGISTRY
        )
        self.failure_ledger = failure_ledger

    def decide(self, context: CognitionContext) -> CognitionResult:
        inference_id = str(uuid4())
        artifact = self.prompt_registry.snapshot()
        messages = [
            {"role": "system", "content": artifact.system_prompt},
            {
                "role": "user",
                "content": json.dumps(
                    build_private_context(context), ensure_ascii=False
                ),
            },
        ]
        failures: list[dict[str, str]] = []
        contract_failed = False
        for attempt in range(1, self.max_attempts + 1):
            try:
                content = self._request(messages, artifact.schema)
                parsed = json.loads(content)
                intention = parse_intention(parsed["intention"])
                appraisals = parse_memory_appraisals(parsed["memory_appraisals"])
                mental_updates = parse_mental_updates(
                    parsed["mental_updates"], context
                )
                attention_schedule = AttentionSchedule(**parsed["attention_schedule"])
                result = CognitionResult(
                    intention=intention,
                    memory_appraisals=appraisals,
                    mental_updates=mental_updates,
                    attention_schedule=attention_schedule,
                    provider="ollama",
                    model=self.model,
                    inference_id=inference_id,
                    attempts=attempt,
                    prompt_version=artifact.version,
                    prompt_hash=artifact.prompt_hash,
                    schema_hash=artifact.schema_hash,
                )
                validate_cognition_result(result, context)
                self.prompt_registry.observe(
                    artifact.version,
                    first_attempt_valid=attempt == 1,
                    provider=self.provider_family,
                    model=self.model,
                )
                return result
            except _OllamaTransportFailure as error:
                failures.append({"model": self.model, "error": str(error)})
                break
            except (RuntimeError, TypeError, ValueError, json.JSONDecodeError) as error:
                contract_failed = True
                self._record_failure(artifact, attempt, error)
                failures.append({"model": self.model, "error": str(error)})
                messages.extend(
                    [
                        {"role": "assistant", "content": locals().get("content", "")},
                        {
                            "role": "user",
                            "content": (
                                "La risposta precedente non rispettava lo schema o i vincoli: "
                                f"{error}. Rivaluta autonomamente la stessa situazione privata e "
                                "restituisci una sola intenzione JSON valida."
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

    def _request(
        self, messages: list[dict[str, str]], schema: dict[str, object]
    ) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": schema,
            "options": {
                "temperature": 0.7,
                "num_ctx": 8192,
                "num_predict": 2048,
            },
            "messages": messages,
        }
        request = Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.timeout_seconds) as response:
                body = json.loads(response.read().decode("utf-8"))
        except (OSError, URLError, TimeoutError, json.JSONDecodeError) as error:
            raise _OllamaTransportFailure(
                f"Ollama inference failed: {error}"
            ) from error
        try:
            return str(body["message"]["content"])
        except (KeyError, TypeError) as error:
            raise RuntimeError(
                f"Ollama returned no intention content: {error}"
            ) from error

    def _record_failure(self, artifact: object, attempt: int, error: Exception) -> None:
        if self.failure_ledger is None:
            return
        self.failure_ledger.record(
            PromptFailure(
                violation_code=_violation_code(error),
                field_path=_field_path(error),
                observed_type=type(error).__name__,
                provider=self.provider_family,
                model=self.model,
                prompt_version=artifact.version,
                prompt_hash=artifact.prompt_hash,
                schema_hash=artifact.schema_hash,
                attempt=attempt,
                detail=str(error),
            )
        )


def _violation_code(error: Exception) -> str:
    message = str(error).lower()
    if "source_event_id" in message or "source_ids" in message:
        return "reference.source_field"
    if "consume" in message or "carried" in message:
        return "material.consume_unavailable"
    if isinstance(error, json.JSONDecodeError):
        return "response.invalid_json"
    if isinstance(error, (KeyError, AttributeError, TypeError)):
        return "response.shape"
    return "contract.invalid"


def _field_path(error: Exception) -> str:
    if isinstance(error, KeyError) and error.args:
        return str(error.args[0])
    return "response"


class _OllamaTransportFailure(RuntimeError):
    pass
