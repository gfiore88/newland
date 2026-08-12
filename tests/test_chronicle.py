from __future__ import annotations

import tempfile
import unittest
from dataclasses import replace
from pathlib import Path

from newland_engine.chronicle import (
    ChronicleContext,
    ChronicleEntry,
    ChronicleStore,
    ChronicleUnavailable,
    ChronicleWorker,
    GenerativeChroniclerPool,
    OllamaChronicler,
)
from newland_engine.cli import build_parser
from newland_engine.event_store import EventStore
from newland_engine.models import EventEnvelope, world_time_for_tick


class RecordingChronicler:
    def __init__(self) -> None:
        self.contexts: list[ChronicleContext] = []

    def narrate(self, context: ChronicleContext) -> ChronicleEntry:
        self.contexts.append(context)
        first = context.events[0]
        last = context.events[-1]
        assert first.sequence is not None
        assert last.sequence is not None
        return ChronicleEntry(
            from_sequence=first.sequence,
            through_sequence=last.sequence,
            world_tick=last.world_tick,
            world_time=last.world_time,
            title="Una soglia quieta",
            prose="Elia giunse nel villaggio, mentre il mattino restava immobile.",
            source_event_ids=tuple(event.event_id for event in context.events),
            provider="test-double",
            model="generated",
            inference_id="inference-test",
            attempts=1,
        )


class FailingChronicler:
    def narrate(self, context: ChronicleContext) -> ChronicleEntry:
        raise ChronicleUnavailable([{"model": "failed", "error": "offline"}])


class ChronicleTests(unittest.TestCase):
    def test_cli_defaults_to_a_continuous_generative_chronicler(self) -> None:
        args = build_parser().parse_args(["chronicle"])

        self.assertEqual("chronicle", args.command)
        self.assertFalse(args.once)
        self.assertEqual(20, args.batch_size)
        self.assertIsNone(args.models)

    def test_worker_writes_derived_entry_without_touching_canonical_log(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event_path = Path(directory) / "newland.db"
            chronicle_path = Path(directory) / "newland.chronicle.db"
            original_events = self._seed(event_path)
            chronicler = RecordingChronicler()
            worker = ChronicleWorker(
                event_path,
                chronicle_path,
                chronicler,
                batch_size=1,
            )

            first = worker.run_once()
            second = worker.run_once()
            exhausted = worker.run_once()

            self.assertEqual((1, 1), (first.from_sequence, first.through_sequence))
            self.assertEqual((2, 2), (second.from_sequence, second.through_sequence))
            self.assertIsNone(exhausted)
            with ChronicleStore(chronicle_path, read_only=True) as store:
                self.assertEqual([1, 2], [entry.sequence for entry in store.entries()])
            with EventStore(event_path, read_only=True) as store:
                self.assertEqual(
                    [event.event_id for event in original_events],
                    [event.event_id for event in store.events()],
                )
            self.assertEqual(
                "Elia", chronicler.contexts[-1].world["agents"]["elia"]["name"]
            )

    def test_failed_generation_leaves_no_entry_and_can_be_retried(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            event_path = Path(directory) / "newland.db"
            chronicle_path = Path(directory) / "newland.chronicle.db"
            self._seed(event_path)
            worker = ChronicleWorker(event_path, chronicle_path, FailingChronicler())

            with self.assertRaises(ChronicleUnavailable):
                worker.run_once()

            with ChronicleStore(chronicle_path, read_only=True) as store:
                self.assertEqual([], store.entries())
                self.assertEqual(0, store.last_source_sequence())

    def test_pool_fails_over_only_to_another_generative_provider(self) -> None:
        events = [
            replace(event, sequence=index)
            for index, event in enumerate(self._events(), start=1)
        ]
        successful = RecordingChronicler()
        pool = GenerativeChroniclerPool([FailingChronicler(), successful])

        entry = pool.narrate(ChronicleContext(tuple(events), {"agents": {}}))

        self.assertEqual("generated", entry.model)
        self.assertEqual(1, len(successful.contexts))

    def test_ollama_rejects_prose_with_invented_provenance(self) -> None:
        events = [
            replace(event, sequence=index)
            for index, event in enumerate(self._events(), start=1)
        ]
        chronicler = OllamaChronicler(max_attempts=1)
        chronicler._request = lambda messages, **kwargs: (  # type: ignore[method-assign]
            '{"title":"Titolo","passages":['
            '{"text":"Testo","source_event_ids":["invented"]}]}'
        )

        with self.assertRaises(ChronicleUnavailable) as raised:
            chronicler.narrate(ChronicleContext(tuple(events), {"agents": {}}))

        self.assertIn("unknown events", raised.exception.failures[0]["error"])

    def test_ollama_retries_instead_of_accepting_unsupported_prose(self) -> None:
        events = [
            replace(event, sequence=index)
            for index, event in enumerate(self._events(), start=1)
        ]
        chronicler = OllamaChronicler(max_attempts=1)
        responses = iter(
            [
                json_for_passage(events[0].event_id),
                '{"supported":false,"issues":["future claim"]}',
            ]
        )
        chronicler._request = lambda messages, **kwargs: next(responses)  # type: ignore[method-assign]

        with self.assertRaises(ChronicleUnavailable) as raised:
            chronicler.narrate(ChronicleContext(tuple(events), {"agents": {}}))

        self.assertIn("grounding review failed", raised.exception.failures[0]["error"])

    def test_ollama_rejects_inferred_absence_without_a_negative_event(self) -> None:
        events = [replace(self._events()[0], sequence=1)]
        chronicler = OllamaChronicler(max_attempts=1)
        responses = iter(
            [
                (
                    '{"title":"Titolo","passages":['
                    f'{{"text":"Non vi erano altri luoghi.",'
                    f'"source_event_ids":["{events[0].event_id}"]}}]}}'
                ),
            ]
        )
        chronicler._request = lambda messages, **kwargs: next(responses)  # type: ignore[method-assign]

        with self.assertRaises(ChronicleUnavailable) as raised:
            chronicler.narrate(ChronicleContext(tuple(events), {"agents": {}}))

        self.assertIn("infers an absence", raised.exception.failures[0]["error"])

    @staticmethod
    def _seed(path: Path) -> list[EventEnvelope]:
        events = ChronicleTests._events()
        with EventStore(path) as store:
            return store.append_many(events)

    @staticmethod
    def _events() -> list[EventEnvelope]:
        return [
            EventEnvelope(
                event_type="WorldInitialized",
                world_tick=0,
                world_time=world_time_for_tick(0),
                payload={"locations": {"village": []}},
            ),
            EventEnvelope(
                event_type="AgentRegistered",
                world_tick=0,
                world_time=world_time_for_tick(0),
                actor_ids=("elia",),
                location="village",
                payload={"name": "Elia", "location": "village"},
                visibility="private",
                recipient_ids=("elia",),
            ),
        ]


def json_for_passage(event_id: str) -> str:
    return (
        '{"title":"Titolo","passages":['
        f'{{"text":"Testo","source_event_ids":["{event_id}"]}}]}}'
    )


if __name__ == "__main__":
    unittest.main()
