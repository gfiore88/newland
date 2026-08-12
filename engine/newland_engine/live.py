from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from threading import Event, Lock, Thread, current_thread
from typing import Any

from .chronicle import (
    ChronicleStore,
    ChronicleUnavailable,
    ChronicleWorker,
    ChroniclerProvider,
    GenerativeChroniclerPool,
    OllamaChronicler,
    default_chronicle_path,
)
from .cognition import (
    CognitionProvider,
    GenerativeCognitionPool,
    OllamaCognition,
    RoutedCognition,
)
from .inference import AdmittedChronicler, AdmittedCognition, InferenceAdmission
from .event_store import EventStore
from .observer import ObserverServer
from .simulation import NewlandSimulation


class LiveSupervisor:
    """Owns Newland's local lifecycle without entering the simulated world."""

    def __init__(
        self,
        database_path: str | Path,
        *,
        chronicle_database_path: str | Path | None = None,
        static_directory: str | Path = "ui/dist",
        host: str = "127.0.0.1",
        port: int = 8765,
        models: tuple[str, ...] = ("qwen2.5:3b",),
        reflective_models: tuple[str, ...] = (),
        chronicle_models: tuple[str, ...] = (),
        agent_weight: int = 8,
        batch_size: int = 20,
        poll_interval: float = 2.0,
        cognition: CognitionProvider | None = None,
        chronicler: ChroniclerProvider | None = None,
        emit: Callable[[list[object]], None] = lambda events: None,
    ) -> None:
        if poll_interval <= 0:
            raise ValueError("poll_interval must be positive")
        if not models and cognition is None:
            raise ValueError("at least one cognition model is required")
        self.database_path = Path(database_path)
        self.chronicle_database_path = Path(
            chronicle_database_path or default_chronicle_path(database_path)
        )
        self.static_directory = Path(static_directory)
        if not (self.static_directory / "index.html").is_file():
            raise ValueError(
                "WebGL build not found; run `npm run build --prefix ui` first"
            )
        self.host = host
        self.port = port
        self.models = models
        self.reflective_models = reflective_models or models
        self.chronicle_models = chronicle_models or models
        self.batch_size = batch_size
        self.poll_interval = poll_interval
        self.emit = emit
        self.stop_event = Event()
        self._booted = Event()
        self._lock = Lock()
        self._threads: dict[str, Thread] = {}
        self._components = {
            "agent_loop": "created",
            "chronicle": "created",
            "observer": "created",
        }
        self._successful_activations = 0
        self._cognition_deferrals = 0
        self._chronicle_entries = 0
        self._failures: list[dict[str, str]] = []
        self.admission = InferenceAdmission(agent_weight=agent_weight)

        if cognition is None:
            ordinary = GenerativeCognitionPool(
                [OllamaCognition(model=model) for model in self.models]
            )
            reflective = GenerativeCognitionPool(
                [OllamaCognition(model=model) for model in self.reflective_models]
            )
            cognition = RoutedCognition(ordinary, reflective)
        if chronicler is None:
            chronicler = GenerativeChroniclerPool(
                [OllamaChronicler(model=model) for model in self.chronicle_models]
            )
        self.cognition = AdmittedCognition(cognition, self.admission)
        self.chronicler = AdmittedChronicler(chronicler, self.admission)
        self.observer: ObserverServer | None = None

    def start(self) -> None:
        if self._threads:
            raise RuntimeError("live supervisor is already started")
        self._start_thread("agent_loop", self._run_agents)
        if not self._booted.wait(timeout=10):
            self.stop_event.set()
            raise RuntimeError("agent runtime did not initialize within 10 seconds")
        if self._component("agent_loop") == "failed":
            raise RuntimeError("agent runtime failed during initialization")

        self.observer = ObserverServer(
            self.database_path,
            chronicle_database_path=self.chronicle_database_path,
            host=self.host,
            port=self.port,
            static_directory=self.static_directory,
            operational_health=self.health,
        )
        self._start_thread("observer", self._run_observer)
        self._start_thread("chronicle", self._run_chronicle)

    def wait(self) -> None:
        while not self.stop_event.wait(0.25):
            continue

    def shutdown(self) -> None:
        self.stop_event.set()
        self.admission.close()
        if self.observer is not None:
            self.observer.shutdown()
        current = current_thread()
        for thread in tuple(self._threads.values()):
            if thread is current:
                continue
            thread.join()

    @property
    def address(self) -> tuple[str, int] | None:
        if self.observer is None:
            return None
        address = self.observer.address
        return address.host, address.port

    def health(self) -> dict[str, Any]:
        with self._lock:
            components = dict(self._components)
            activations = self._successful_activations
            deferrals = self._cognition_deferrals
            chronicle_entries = self._chronicle_entries
            failures = list(self._failures[-20:])
        return {
            "components": components,
            "successful_activations": activations,
            "cognition_deferrals": deferrals,
            "chronicle_entries": chronicle_entries,
            "chronicle_progress": self._chronicle_progress(),
            "configured_models": {
                "agent": list(self.models),
                "reflective": list(self.reflective_models),
                "chronicle": list(self.chronicle_models),
            },
            "inference": self.admission.snapshot().to_dict(),
            "failures": failures,
            "stopping": self.stop_event.is_set(),
        }

    def _run_agents(self) -> None:
        try:
            with NewlandSimulation(
                self.database_path, cognition=self.cognition
            ) as simulation:
                self._set_component("agent_loop", "running")
                self._booted.set()
                while not self.stop_event.is_set():
                    events = simulation.run(max_activations=1)
                    if not events:
                        self.stop_event.wait(0.05)
                        continue
                    self.emit(list(events))
                    with self._lock:
                        if any(
                            event.event_type == "CognitionDeferred" for event in events
                        ):
                            self._cognition_deferrals += 1
                        else:
                            self._successful_activations += 1
        except BaseException as error:
            if self.stop_event.is_set():
                self._set_component("agent_loop", "stopped")
                return
            self._record_failure("agent_loop", error)
            self._set_component("agent_loop", "failed")
            self._booted.set()
            self.stop_event.set()
            return
        self._set_component("agent_loop", "stopped")

    def _run_chronicle(self) -> None:
        self._set_component("chronicle", "running")
        worker = ChronicleWorker(
            self.database_path,
            self.chronicle_database_path,
            self.chronicler,
            batch_size=self.batch_size,
        )
        while not self.stop_event.is_set():
            try:
                entry = worker.run_once()
                if entry is not None:
                    with self._lock:
                        self._chronicle_entries += 1
            except ChronicleUnavailable as error:
                self._record_failure("chronicle", error)
            except Exception as error:
                self._record_failure("chronicle", error)
            self.stop_event.wait(self.poll_interval)
        self._set_component("chronicle", "stopped")

    def _run_observer(self) -> None:
        self._set_component("observer", "running")
        try:
            assert self.observer is not None
            self.observer.serve_forever()
        except Exception as error:
            self._record_failure("observer", error)
            self._set_component("observer", "failed")
            return
        self._set_component("observer", "stopped")

    def _start_thread(self, name: str, target: Callable[[], None]) -> None:
        thread = Thread(target=target, name=f"newland-{name}", daemon=True)
        self._threads[name] = thread
        thread.start()

    def _set_component(self, component: str, state: str) -> None:
        with self._lock:
            self._components[component] = state

    def _component(self, component: str) -> str:
        with self._lock:
            return self._components[component]

    def _record_failure(self, component: str, error: BaseException) -> None:
        with self._lock:
            self._failures.append(
                {"component": component, "error": f"{type(error).__name__}: {error}"}
            )

    def _chronicle_progress(self) -> dict[str, int]:
        try:
            with EventStore(self.database_path, read_only=True) as event_store:
                events = event_store.events()
            canonical_sequence = events[-1].sequence or 0 if events else 0
            narrated_through = 0
            if self.chronicle_database_path.is_file():
                with ChronicleStore(
                    self.chronicle_database_path, read_only=True
                ) as chronicle_store:
                    narrated_through = chronicle_store.last_source_sequence()
            return {
                "canonical_sequence": canonical_sequence,
                "narrated_through_sequence": narrated_through,
                "backlog_events": max(0, canonical_sequence - narrated_through),
            }
        except (OSError, RuntimeError):
            return {
                "canonical_sequence": 0,
                "narrated_through_sequence": 0,
                "backlog_events": 0,
            }
