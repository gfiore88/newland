class CognitionUnavailable(RuntimeError):
    def __init__(
        self,
        failures: list[dict[str, str]],
        *,
        stop_provider_family: str | None = None,
    ) -> None:
        super().__init__("no generative cognition provider returned a valid intention")
        self.failures = failures
        self.stop_provider_family = stop_provider_family
