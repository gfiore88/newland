import json
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .exceptions import CognitionUnavailable
from .types import AttentionSchedule, CognitionContext, CognitionResult
from .validation import validate_cognition_result
from .schema import get_cognition_schema
from .prompting import build_system_prompt, build_private_context
from .parsing import parse_intention, parse_memory_appraisals, parse_mental_updates


class OllamaCognition:
    provider_family = "ollama"

    def __init__(
        self,
        model: str = "qwen2.5:3b",
        endpoint: str = "http://127.0.0.1:11434/api/chat",
        timeout_seconds: float = 120.0,
        max_attempts: int = 3,
    ) -> None:
        self.model = model
        self.endpoint = endpoint
        self.timeout_seconds = timeout_seconds
        self.max_attempts = max_attempts

    def decide(self, context: CognitionContext) -> CognitionResult:
        inference_id = str(uuid4())
        messages = [
            {"role": "system", "content": build_system_prompt()},
            {
                "role": "user",
                "content": json.dumps(
                    build_private_context(context), ensure_ascii=False
                ),
            },
        ]
        failures: list[dict[str, str]] = []
        for attempt in range(1, self.max_attempts + 1):
            try:
                content = self._request(messages)
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
                )
                validate_cognition_result(result, context)
                return result
            except (RuntimeError, TypeError, ValueError, json.JSONDecodeError) as error:
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
        raise CognitionUnavailable(failures)

    def _request(self, messages: list[dict[str, str]]) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": get_cognition_schema(),
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
            raise RuntimeError(f"Ollama inference failed: {error}") from error
        try:
            return str(body["message"]["content"])
        except (KeyError, TypeError) as error:
            raise RuntimeError(
                f"Ollama returned no intention content: {error}"
            ) from error
