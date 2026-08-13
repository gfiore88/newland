class CognitionUnavailable(RuntimeError):
    def __init__(self, failures: list[dict[str, str]]) -> None:
        super().__init__("no generative cognition provider returned a valid intention")
        self.failures = failures
