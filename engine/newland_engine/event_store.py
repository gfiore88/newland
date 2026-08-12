from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path
from typing import Self

from .models import AgentMind, EventEnvelope


class EventStore:
    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.connection = sqlite3.connect(self.path)
        self.connection.row_factory = sqlite3.Row
        self.connection.execute("PRAGMA foreign_keys = ON")
        self.connection.execute("PRAGMA journal_mode = WAL")
        self._create_schema()

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS events (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                event_id TEXT NOT NULL UNIQUE,
                schema_version INTEGER NOT NULL,
                world_tick INTEGER NOT NULL CHECK (world_tick >= 0),
                world_time TEXT NOT NULL,
                event_type TEXT NOT NULL,
                actor_ids TEXT NOT NULL,
                location TEXT,
                payload TEXT NOT NULL,
                visibility TEXT NOT NULL CHECK (visibility IN ('public', 'local', 'private')),
                recipient_ids TEXT NOT NULL,
                causation_id TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_events_tick ON events(world_tick, sequence);
            CREATE INDEX IF NOT EXISTS idx_events_type ON events(event_type, sequence);

            CREATE TABLE IF NOT EXISTS mind_snapshots (
                agent_id TEXT PRIMARY KEY,
                last_sequence INTEGER NOT NULL,
                state TEXT NOT NULL
            );
            """
        )
        self.connection.commit()

    def append(self, event: EventEnvelope) -> EventEnvelope:
        return self.append_many([event])[0]

    def append_many(self, events: Iterable[EventEnvelope]) -> list[EventEnvelope]:
        with self.connection:
            return self._insert_events(events)

    def append_many_with_mind(
        self, events: Iterable[EventEnvelope], mind: AgentMind
    ) -> list[EventEnvelope]:
        """Atomically persist one cognitive activation and its resulting mind snapshot."""
        with self.connection:
            persisted = self._insert_events(events)
            self._upsert_mind(mind)
            return persisted

    def events(self, *, after_sequence: int = 0) -> list[EventEnvelope]:
        rows = self.connection.execute(
            "SELECT * FROM events WHERE sequence > ? ORDER BY sequence",
            (after_sequence,),
        ).fetchall()
        return [self._row_to_event(row) for row in rows]

    def event_count(self) -> int:
        row = self.connection.execute("SELECT COUNT(*) AS count FROM events").fetchone()
        return int(row["count"])

    def save_mind(self, mind: AgentMind) -> None:
        with self.connection:
            self._upsert_mind(mind)

    def load_minds(self) -> dict[str, AgentMind]:
        rows = self.connection.execute(
            "SELECT state FROM mind_snapshots ORDER BY agent_id"
        ).fetchall()
        return {
            data["agent_id"]: AgentMind.from_dict(data)
            for row in rows
            if (data := json.loads(row["state"]))
        }

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    def _insert_events(self, events: Iterable[EventEnvelope]) -> list[EventEnvelope]:
        persisted: list[EventEnvelope] = []
        for event in events:
            cursor = self.connection.execute(
                """
                INSERT INTO events (
                    event_id, schema_version, world_tick, world_time, event_type,
                    actor_ids, location, payload, visibility, recipient_ids, causation_id
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    event.event_id,
                    event.schema_version,
                    event.world_tick,
                    event.world_time,
                    event.event_type,
                    json.dumps(event.actor_ids),
                    event.location,
                    json.dumps(event.payload, ensure_ascii=False, sort_keys=True),
                    event.visibility,
                    json.dumps(event.recipient_ids),
                    event.causation_id,
                ),
            )
            persisted.append(replace(event, sequence=cursor.lastrowid))
        return persisted

    def _upsert_mind(self, mind: AgentMind) -> None:
        self.connection.execute(
            """
            INSERT INTO mind_snapshots (agent_id, last_sequence, state)
            VALUES (?, ?, ?)
            ON CONFLICT(agent_id) DO UPDATE SET
                last_sequence = excluded.last_sequence,
                state = excluded.state
            """,
            (
                mind.agent_id,
                mind.last_perceived_sequence,
                json.dumps(mind.to_dict(), ensure_ascii=False, sort_keys=True),
            ),
        )

    @staticmethod
    def _row_to_event(row: sqlite3.Row) -> EventEnvelope:
        return EventEnvelope(
            event_id=row["event_id"],
            sequence=row["sequence"],
            schema_version=row["schema_version"],
            world_tick=row["world_tick"],
            world_time=row["world_time"],
            event_type=row["event_type"],
            actor_ids=tuple(json.loads(row["actor_ids"])),
            location=row["location"],
            payload=json.loads(row["payload"]),
            visibility=row["visibility"],
            recipient_ids=tuple(json.loads(row["recipient_ids"])),
            causation_id=row["causation_id"],
        )
