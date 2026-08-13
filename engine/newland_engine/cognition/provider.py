from dataclasses import replace
from typing import Literal, Protocol

from .types import CognitionContext, CognitionResult
from .exceptions import CognitionUnavailable


class CognitionProvider(Protocol):
    def decide(self, context: CognitionContext) -> CognitionResult: ...


class RoutedCognition:
    """Routes private context to a model tier without choosing agent behavior."""

    def __init__(
        self,
        ordinary: CognitionProvider,
        reflective: CognitionProvider,
    ) -> None:
        self.ordinary = ordinary
        self.reflective = reflective

    def decide(self, context: CognitionContext) -> CognitionResult:
        route = self.route_for(context)
        provider = self.reflective if route == "reflective" else self.ordinary
        return replace(provider.decide(context), route=route)

    @staticmethod
    def route_for(context: CognitionContext) -> Literal["ordinary", "reflective"]:
        observed_types = {
            observation.event.event_type for observation in context.observations
        }
        if "ResonanceSignalReceived" in observed_types or context.active_disputes:
            return "reflective"
        return "ordinary"


class GenerativeCognitionPool:
    def __init__(self, providers: list[CognitionProvider]) -> None:
        if not providers:
            raise ValueError("at least one generative cognition provider is required")
        self.providers = providers

    def decide(self, context: CognitionContext) -> CognitionResult:
        failures: list[dict[str, str]] = []
        stopped_families: set[str] = set()
        for provider in self.providers:
            family = getattr(provider, "provider_family", None)
            if family in stopped_families:
                continue
            try:
                return provider.decide(context)
            except CognitionUnavailable as error:
                failures.extend(error.failures)
                if error.stop_provider_family is not None:
                    stopped_families.add(error.stop_provider_family)
        raise CognitionUnavailable(failures)
