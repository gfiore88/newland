from __future__ import annotations

from collections.abc import Callable
from dataclasses import asdict, dataclass
from threading import Condition
from time import monotonic
from typing import Literal, Protocol, TypeVar

from .chronicle import ChronicleContext, ChronicleEntry, ChroniclerProvider
from .cognition import CognitionContext, CognitionProvider, CognitionResult

Workload = Literal["agent", "chronicle"]
ResultT = TypeVar("ResultT")


@dataclass(frozen=True, slots=True)
class InferenceAdmissionSnapshot:
    agent_queue_depth: int
    chronicle_queue_depth: int
    in_flight: Workload | None
    completed_agent_jobs: int
    completed_chronicle_jobs: int
    failed_agent_jobs: int
    failed_chronicle_jobs: int
    consecutive_agent_jobs: int
    agent_weight: int
    total_agent_wait_seconds: float
    total_chronicle_wait_seconds: float
    accepting: bool

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


class InferenceAdmission:
    """Serializes local inference while giving waiting agent minds priority."""

    def __init__(self, *, agent_weight: int = 8) -> None:
        if agent_weight < 1:
            raise ValueError("agent_weight must be positive")
        self.agent_weight = agent_weight
        self._condition = Condition()
        self._waiting: dict[Workload, int] = {"agent": 0, "chronicle": 0}
        self._in_flight: Workload | None = None
        self._completed: dict[Workload, int] = {"agent": 0, "chronicle": 0}
        self._failed: dict[Workload, int] = {"agent": 0, "chronicle": 0}
        self._wait_seconds: dict[Workload, float] = {
            "agent": 0.0,
            "chronicle": 0.0,
        }
        self._consecutive_agent_jobs = 0
        self._accepting = True

    def close(self) -> None:
        """Reject queued and future jobs while allowing the active call to finish."""
        with self._condition:
            self._accepting = False
            self._condition.notify_all()

    def run(self, workload: Workload, operation: Callable[[], ResultT]) -> ResultT:
        if workload not in {"agent", "chronicle"}:
            raise ValueError(f"unsupported inference workload: {workload}")
        queued_at = monotonic()
        with self._condition:
            if not self._accepting:
                raise InferenceAdmissionClosed("inference admission is closed")
            self._waiting[workload] += 1
            while not self._may_start(workload):
                self._condition.wait()
                if not self._accepting:
                    self._waiting[workload] -= 1
                    self._condition.notify_all()
                    raise InferenceAdmissionClosed("inference admission is closed")
            self._waiting[workload] -= 1
            self._wait_seconds[workload] += monotonic() - queued_at
            self._in_flight = workload

        failed = False
        try:
            return operation()
        except BaseException:
            failed = True
            raise
        finally:
            with self._condition:
                if failed:
                    self._failed[workload] += 1
                else:
                    self._completed[workload] += 1
                if workload == "agent":
                    self._consecutive_agent_jobs += 1
                else:
                    self._consecutive_agent_jobs = 0
                self._in_flight = None
                self._condition.notify_all()

    def snapshot(self) -> InferenceAdmissionSnapshot:
        with self._condition:
            return InferenceAdmissionSnapshot(
                agent_queue_depth=self._waiting["agent"],
                chronicle_queue_depth=self._waiting["chronicle"],
                in_flight=self._in_flight,
                completed_agent_jobs=self._completed["agent"],
                completed_chronicle_jobs=self._completed["chronicle"],
                failed_agent_jobs=self._failed["agent"],
                failed_chronicle_jobs=self._failed["chronicle"],
                consecutive_agent_jobs=self._consecutive_agent_jobs,
                agent_weight=self.agent_weight,
                total_agent_wait_seconds=self._wait_seconds["agent"],
                total_chronicle_wait_seconds=self._wait_seconds["chronicle"],
                accepting=self._accepting,
            )

    def _may_start(self, workload: Workload) -> bool:
        if self._in_flight is not None:
            return False
        if workload == "agent":
            return not (
                self._waiting["chronicle"] > 0
                and self._consecutive_agent_jobs >= self.agent_weight
            )
        return not (
            self._waiting["agent"] > 0
            and self._consecutive_agent_jobs < self.agent_weight
        )


class InferenceAdmissionClosed(RuntimeError):
    pass


class AdmittedCognition:
    def __init__(
        self, provider: CognitionProvider, admission: InferenceAdmission
    ) -> None:
        self.provider = provider
        self.admission = admission

    def decide(self, context: CognitionContext) -> CognitionResult:
        return self.admission.run("agent", lambda: self.provider.decide(context))


class AdmittedChronicler:
    def __init__(
        self, provider: ChroniclerProvider, admission: InferenceAdmission
    ) -> None:
        self.provider = provider
        self.admission = admission

    def narrate(self, context: ChronicleContext) -> ChronicleEntry:
        return self.admission.run(
            "chronicle", lambda: self.provider.narrate(context)
        )
