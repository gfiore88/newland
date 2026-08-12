from __future__ import annotations

import json
import re
import sqlite3
from collections.abc import Iterable
from dataclasses import dataclass, field, replace
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Protocol, Self
from urllib.error import URLError
from urllib.request import Request, urlopen
from uuid import uuid4

from .event_store import EventStore
from .models import EventEnvelope
from .projections import event_projection, world_projection
from .world import replay


@dataclass(frozen=True, slots=True)
class ChronicleEntry:
    from_sequence: int
    through_sequence: int
    world_tick: int
    world_time: str
    title: str
    prose: str
    source_event_ids: tuple[str, ...]
    provider: str
    model: str
    inference_id: str
    attempts: int
    prompt_version: str = "silent-chronicler-v2"
    entry_id: str = field(default_factory=lambda: str(uuid4()))
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    sequence: int | None = None

    def __post_init__(self) -> None:
        if self.from_sequence < 1 or self.through_sequence < self.from_sequence:
            raise ValueError("invalid chronicle source sequence range")
        if not self.title.strip() or not self.prose.strip():
            raise ValueError("chronicle title and prose are required")
        if not self.source_event_ids:
            raise ValueError("chronicle entry requires source events")
        if self.attempts < 1:
            raise ValueError("chronicle attempts must be positive")

    def to_dict(self) -> dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "sequence": self.sequence,
            "from_sequence": self.from_sequence,
            "through_sequence": self.through_sequence,
            "world_tick": self.world_tick,
            "world_time": self.world_time,
            "title": self.title,
            "prose": self.prose,
            "source_event_ids": self.source_event_ids,
            "provider": self.provider,
            "model": self.model,
            "inference_id": self.inference_id,
            "attempts": self.attempts,
            "prompt_version": self.prompt_version,
            "created_at": self.created_at,
        }


class ChronicleStore:
    def __init__(self, path: str | Path, *, read_only: bool = False) -> None:
        self.path = Path(path)
        if read_only:
            database_uri = f"{self.path.resolve().as_uri()}?mode=ro"
            self.connection = sqlite3.connect(database_uri, uri=True)
        else:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            self.connection = sqlite3.connect(self.path)
            self.connection.execute("PRAGMA journal_mode = WAL")
            self._create_schema()
        self.connection.row_factory = sqlite3.Row

    def _create_schema(self) -> None:
        self.connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS chronicle_entries (
                sequence INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id TEXT NOT NULL UNIQUE,
                from_sequence INTEGER NOT NULL CHECK (from_sequence >= 1),
                through_sequence INTEGER NOT NULL CHECK (through_sequence >= from_sequence),
                world_tick INTEGER NOT NULL CHECK (world_tick >= 0),
                world_time TEXT NOT NULL,
                title TEXT NOT NULL,
                prose TEXT NOT NULL,
                source_event_ids TEXT NOT NULL,
                provider TEXT NOT NULL,
                model TEXT NOT NULL,
                inference_id TEXT NOT NULL,
                attempts INTEGER NOT NULL CHECK (attempts >= 1),
                prompt_version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(from_sequence, through_sequence)
            );
            CREATE INDEX IF NOT EXISTS idx_chronicle_through_sequence
                ON chronicle_entries(through_sequence, sequence);
            """
        )
        self.connection.commit()

    def append(self, entry: ChronicleEntry) -> ChronicleEntry:
        with self.connection:
            cursor = self.connection.execute(
                """
                INSERT INTO chronicle_entries (
                    entry_id, from_sequence, through_sequence, world_tick,
                    world_time, title, prose, source_event_ids, provider, model,
                    inference_id, attempts, prompt_version, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.entry_id,
                    entry.from_sequence,
                    entry.through_sequence,
                    entry.world_tick,
                    entry.world_time,
                    entry.title,
                    entry.prose,
                    json.dumps(entry.source_event_ids),
                    entry.provider,
                    entry.model,
                    entry.inference_id,
                    entry.attempts,
                    entry.prompt_version,
                    entry.created_at,
                ),
            )
        return replace(entry, sequence=cursor.lastrowid)

    def entries(self, *, after_sequence: int = 0) -> list[ChronicleEntry]:
        rows = self.connection.execute(
            "SELECT * FROM chronicle_entries WHERE sequence > ? ORDER BY sequence",
            (after_sequence,),
        ).fetchall()
        return [self._row_to_entry(row) for row in rows]

    def last_source_sequence(self) -> int:
        row = self.connection.execute(
            "SELECT COALESCE(MAX(through_sequence), 0) AS sequence FROM chronicle_entries"
        ).fetchone()
        return int(row["sequence"])

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

    @staticmethod
    def _row_to_entry(row: sqlite3.Row) -> ChronicleEntry:
        return ChronicleEntry(
            entry_id=row["entry_id"],
            sequence=row["sequence"],
            from_sequence=row["from_sequence"],
            through_sequence=row["through_sequence"],
            world_tick=row["world_tick"],
            world_time=row["world_time"],
            title=row["title"],
            prose=row["prose"],
            source_event_ids=tuple(json.loads(row["source_event_ids"])),
            provider=row["provider"],
            model=row["model"],
            inference_id=row["inference_id"],
            attempts=row["attempts"],
            prompt_version=row["prompt_version"],
            created_at=row["created_at"],
        )


@dataclass(frozen=True, slots=True)
class ChronicleContext:
    events: tuple[EventEnvelope, ...]
    world: dict[str, Any]


class ChroniclerProvider(Protocol):
    def narrate(self, context: ChronicleContext) -> ChronicleEntry: ...


class ChronicleUnavailable(RuntimeError):
    def __init__(self, failures: list[dict[str, str]]) -> None:
        super().__init__("no generative chronicler returned a valid entry")
        self.failures = failures


class OllamaChronicler:
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

    def narrate(self, context: ChronicleContext) -> ChronicleEntry:
        if not context.events:
            raise ValueError("chronicler requires at least one event")
        inference_id = str(uuid4())
        messages = [
            {"role": "system", "content": self._system_prompt()},
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "world": context.world,
                        "events": [event_projection(event) for event in context.events],
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        valid_event_ids = {event.event_id for event in context.events}
        failures: list[dict[str, str]] = []
        for attempt in range(1, self.max_attempts + 1):
            try:
                content = self._request(
                    messages,
                    schema=self._schema(),
                    temperature=0.82,
                )
                parsed = json.loads(content)
                passages = tuple(parsed["passages"])
                passage_sources: set[str] = set()
                prose_parts: list[str] = []
                for passage in passages:
                    text = str(passage["text"]).strip()
                    source_ids = tuple(passage["source_event_ids"])
                    if not text or not source_ids:
                        raise ValueError(
                            "each chronicle passage requires text and source events"
                        )
                    unknown = set(source_ids) - valid_event_ids
                    if unknown:
                        raise ValueError(
                            f"chronicle references unknown events: {sorted(unknown)}"
                        )
                    cited_events = [
                        event
                        for event in context.events
                        if event.event_id in source_ids
                    ]
                    self._validate_passage_claims(text, cited_events)
                    prose_parts.append(text)
                    passage_sources.update(source_ids)
                source_event_ids = tuple(
                    event.event_id
                    for event in context.events
                    if event.event_id in passage_sources
                )
                first = context.events[0]
                last = context.events[-1]
                if first.sequence is None or last.sequence is None:
                    raise ValueError("chronicle requires persisted source events")
                self._review_grounding(context, str(parsed["title"]), passages)
                return ChronicleEntry(
                    from_sequence=first.sequence,
                    through_sequence=last.sequence,
                    world_tick=last.world_tick,
                    world_time=last.world_time,
                    title=str(parsed["title"]),
                    prose="\n\n".join(prose_parts),
                    source_event_ids=source_event_ids,
                    provider="ollama",
                    model=self.model,
                    inference_id=inference_id,
                    attempts=attempt,
                )
            except (
                RuntimeError,
                TypeError,
                ValueError,
                KeyError,
                json.JSONDecodeError,
            ) as error:
                failures.append({"model": self.model, "error": str(error)})
                messages.extend(
                    [
                        {"role": "assistant", "content": locals().get("content", "")},
                        {
                            "role": "user",
                            "content": (
                                "La voce precedente non era valida: "
                                f"{error}. Riscrivi usando soltanto gli eventi forniti "
                                "e restituisci esclusivamente il JSON richiesto."
                            ),
                        },
                    ]
                )
        raise ChronicleUnavailable(failures)

    def _review_grounding(
        self,
        context: ChronicleContext,
        title: str,
        passages: tuple[dict[str, Any], ...],
    ) -> None:
        review_messages = [
            {
                "role": "system",
                "content": (
                    "Sei il revisore fattuale del Diario di Newland. Verifica con severità "
                    "che ogni affermazione della bozza sia direttamente sostenuta dagli eventi "
                    "citati. Rifiuta inferenze su assenze, cause, possibilità future, conoscenza "
                    "o ignoranza, motivazioni e stati interiori non espliciti. Anche una sola "
                    "affermazione non sostenuta rende supported=false. Non riscrivere la bozza."
                ),
            },
            {
                "role": "user",
                "content": json.dumps(
                    {
                        "events": [event_projection(event) for event in context.events],
                        "draft": {"title": title, "passages": passages},
                    },
                    ensure_ascii=False,
                ),
            },
        ]
        review = json.loads(
            self._request(
                review_messages,
                schema=self._review_schema(),
                temperature=0.05,
            )
        )
        if review["supported"] is not True:
            issues = review.get("issues", [])
            raise ValueError(f"chronicle grounding review failed: {issues}")

    def _request(
        self,
        messages: list[dict[str, str]],
        *,
        schema: dict[str, Any],
        temperature: float,
    ) -> str:
        payload = {
            "model": self.model,
            "stream": False,
            "think": False,
            "format": schema,
            "options": {
                "temperature": temperature,
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
            return str(body["message"]["content"])
        except (
            OSError,
            URLError,
            TimeoutError,
            KeyError,
            TypeError,
            json.JSONDecodeError,
        ) as error:
            raise RuntimeError(f"Ollama chronicle inference failed: {error}") from error

    @staticmethod
    def _system_prompt() -> str:
        return (
            "Sei il Cronista Silenzioso di Newland: una voce extradiegetica in terza persona, "
            "mai un abitante e mai un decisore. Scrivi in italiano una breve voce di diario "
            "sobria, concreta, rurale e malinconica. Puoi narrare esclusivamente fatti contenuti "
            "negli eventi forniti; non inventare azioni, parole, sentimenti, intenzioni, luoghi, "
            "cause o significati. Distingui un fatto materiale da un'esperienza privata registrata: "
            "non trasformare una percezione soggettiva in verità del mondo. Non predire il futuro "
            "e non suggerire comportamenti. L'elenco non è una storia completa: non affermare che "
            "qualcosa non sia accaduto soltanto perché non compare negli eventi. La sezione world "
            "serve a risolvere nomi e stato, non autorizza ipotesi. Dividi la voce in brevi passaggi; "
            "Evita frasi grammaticalmente negative, salvo quando un evento citato registra "
            "esplicitamente un rifiuto o un diniego. "
            "per ogni passaggio cita tutti e soli gli event_id che sostengono ogni sua affermazione. "
            "Prima di rispondere, elimina autonomamente qualsiasi frase non sostenuta. "
            "Restituisci soltanto il JSON richiesto."
        )

    @staticmethod
    def _validate_passage_claims(text: str, cited_events: list[EventEnvelope]) -> None:
        contains_negation = re.search(
            r"\b(non|nessun[oaie]?|senza|mai|ignot[oaie]?)\b",
            text,
            flags=re.IGNORECASE,
        )
        explicit_negative_outcome = any(
            "Rejected" in event.event_type
            or "Declined" in event.event_type
            or event.payload.get("response") == "decline"
            for event in cited_events
        )
        if contains_negation and not explicit_negative_outcome:
            raise ValueError(
                "chronicle passage infers an absence without an explicit negative event"
            )

    @staticmethod
    def _schema() -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["title", "passages"],
            "properties": {
                "title": {"type": "string", "minLength": 1, "maxLength": 120},
                "passages": {
                    "type": "array",
                    "minItems": 1,
                    "maxItems": 8,
                    "items": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["text", "source_event_ids"],
                        "properties": {
                            "text": {
                                "type": "string",
                                "minLength": 1,
                                "maxLength": 1200,
                            },
                            "source_event_ids": {
                                "type": "array",
                                "minItems": 1,
                                "uniqueItems": True,
                                "items": {"type": "string"},
                            },
                        },
                    },
                },
            },
        }

    @staticmethod
    def _review_schema() -> dict[str, Any]:
        return {
            "type": "object",
            "additionalProperties": False,
            "required": ["supported", "issues"],
            "properties": {
                "supported": {"type": "boolean"},
                "issues": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
        }


class GenerativeChroniclerPool:
    def __init__(self, providers: Iterable[ChroniclerProvider]) -> None:
        self.providers = tuple(providers)
        if not self.providers:
            raise ValueError("at least one generative chronicler is required")

    def narrate(self, context: ChronicleContext) -> ChronicleEntry:
        failures: list[dict[str, str]] = []
        for provider in self.providers:
            try:
                return provider.narrate(context)
            except ChronicleUnavailable as error:
                failures.extend(error.failures)
            except (RuntimeError, TypeError, ValueError) as error:
                failures.append({"model": type(provider).__name__, "error": str(error)})
        raise ChronicleUnavailable(failures)


class ChronicleWorker:
    def __init__(
        self,
        event_database_path: str | Path,
        chronicle_database_path: str | Path,
        chronicler: ChroniclerProvider,
        *,
        batch_size: int = 20,
    ) -> None:
        if not 1 <= batch_size <= 200:
            raise ValueError("batch_size must be between 1 and 200")
        self.event_database_path = Path(event_database_path)
        self.chronicle_database_path = Path(chronicle_database_path)
        self.chronicler = chronicler
        self.batch_size = batch_size

    def run_once(self) -> ChronicleEntry | None:
        with ChronicleStore(self.chronicle_database_path) as chronicle_store:
            after_sequence = chronicle_store.last_source_sequence()
            with EventStore(self.event_database_path, read_only=True) as event_store:
                all_events = event_store.events()
            pending = [
                event for event in all_events if (event.sequence or 0) > after_sequence
            ][: self.batch_size]
            if not pending:
                return None
            through_sequence = pending[-1].sequence or 0
            context = ChronicleContext(
                events=tuple(pending),
                world=world_projection(
                    replay(
                        [
                            event
                            for event in all_events
                            if (event.sequence or 0) <= through_sequence
                        ]
                    )
                ),
            )
            entry = self.chronicler.narrate(context)
            return chronicle_store.append(entry)


def default_chronicle_path(event_database_path: str | Path) -> Path:
    path = Path(event_database_path)
    return path.with_name(f"{path.stem}.chronicle.db")
