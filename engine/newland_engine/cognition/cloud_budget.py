from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from pathlib import Path
from threading import RLock
from uuid import uuid4


class CloudBudgetExceeded(RuntimeError):
    pass


@dataclass(frozen=True, slots=True)
class CloudReservation:
    reservation_id: str
    provider: str
    model: str
    reserved_tokens: int


@dataclass(frozen=True, slots=True)
class CloudBudgetSnapshot:
    global_cap: int
    consumed_tokens: int
    reserved_tokens: int
    remaining_tokens: int
    settled_requests: int
    interrupted_reservations: int

    def to_dict(self) -> dict[str, int]:
        return {
            "global_cap": self.global_cap,
            "consumed_tokens": self.consumed_tokens,
            "reserved_tokens": self.reserved_tokens,
            "remaining_tokens": self.remaining_tokens,
            "settled_requests": self.settled_requests,
            "interrupted_reservations": self.interrupted_reservations,
        }


class CloudUsageLedger:
    """Non-canonical persistent accounting for bounded cloud inference."""

    def __init__(self, path: str | Path, *, global_cap: int) -> None:
        if global_cap < 1:
            raise ValueError("cloud global cap must be positive")
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.global_cap = global_cap
        self._lock = RLock()
        self._connection = sqlite3.connect(self.path, check_same_thread=False)
        self._connection.row_factory = sqlite3.Row
        with self._connection:
            self._connection.execute(
                """
                CREATE TABLE IF NOT EXISTS cloud_reservations (
                    reservation_id TEXT PRIMARY KEY,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    reserved_tokens INTEGER NOT NULL,
                    charged_tokens INTEGER NOT NULL DEFAULT 0,
                    prompt_tokens INTEGER NOT NULL DEFAULT 0,
                    completion_tokens INTEGER NOT NULL DEFAULT 0,
                    reasoning_tokens INTEGER NOT NULL DEFAULT 0,
                    status TEXT NOT NULL CHECK (
                        status IN ('reserved', 'settled', 'interrupted')
                    ),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    settled_at TEXT
                )
                """
            )
            self._connection.execute(
                "CREATE INDEX IF NOT EXISTS cloud_reservations_model "
                "ON cloud_reservations(provider, model, status)"
            )
        self._recover_interrupted_reservations()

    def reserve(
        self,
        *,
        provider: str,
        model: str,
        estimated_input_tokens: int,
        max_output_tokens: int,
        model_cap: int,
    ) -> CloudReservation:
        if estimated_input_tokens < 0 or max_output_tokens < 1 or model_cap < 1:
            raise ValueError("cloud reservation budgets must be positive")
        requested = estimated_input_tokens + max_output_tokens
        with self._lock, self._connection:
            global_total = self._accounted_tokens()
            model_total = self._accounted_tokens(provider=provider, model=model)
            if global_total + requested > self.global_cap:
                raise CloudBudgetExceeded(
                    "persistent cloud token cap would be exceeded"
                )
            if model_total + requested > model_cap:
                raise CloudBudgetExceeded(
                    f"persistent token cap would be exceeded for {model}"
                )
            reservation = CloudReservation(
                reservation_id=str(uuid4()),
                provider=provider,
                model=model,
                reserved_tokens=requested,
            )
            self._connection.execute(
                """
                INSERT INTO cloud_reservations (
                    reservation_id, provider, model, reserved_tokens, status
                ) VALUES (?, ?, ?, ?, 'reserved')
                """,
                (
                    reservation.reservation_id,
                    provider,
                    model,
                    requested,
                ),
            )
        return reservation

    def settle(
        self,
        reservation: CloudReservation,
        *,
        prompt_tokens: int,
        completion_tokens: int,
        reasoning_tokens: int,
        total_tokens: int | None,
    ) -> None:
        values = (prompt_tokens, completion_tokens, reasoning_tokens)
        if any(value < 0 for value in values):
            raise ValueError("provider token usage cannot be negative")
        charged = (
            reservation.reserved_tokens
            if total_tokens is None
            else max(0, total_tokens)
        )
        with self._lock, self._connection:
            cursor = self._connection.execute(
                """
                UPDATE cloud_reservations
                SET charged_tokens = ?, prompt_tokens = ?, completion_tokens = ?,
                    reasoning_tokens = ?, status = 'settled',
                    settled_at = CURRENT_TIMESTAMP
                WHERE reservation_id = ? AND status = 'reserved'
                """,
                (
                    charged,
                    prompt_tokens,
                    completion_tokens,
                    reasoning_tokens,
                    reservation.reservation_id,
                ),
            )
            if cursor.rowcount != 1:
                raise ValueError("cloud reservation is unknown or already settled")

    def snapshot(self) -> CloudBudgetSnapshot:
        with self._lock:
            row = self._connection.execute(
                """
                SELECT
                    COALESCE(SUM(CASE WHEN status != 'reserved'
                        THEN charged_tokens ELSE 0 END), 0) AS consumed,
                    COALESCE(SUM(CASE WHEN status = 'reserved'
                        THEN reserved_tokens ELSE 0 END), 0) AS reserved,
                    SUM(CASE WHEN status = 'settled' THEN 1 ELSE 0 END) AS settled,
                    SUM(CASE WHEN status = 'interrupted' THEN 1 ELSE 0 END)
                        AS interrupted
                FROM cloud_reservations
                """
            ).fetchone()
        consumed = int(row["consumed"])
        reserved = int(row["reserved"])
        return CloudBudgetSnapshot(
            global_cap=self.global_cap,
            consumed_tokens=consumed,
            reserved_tokens=reserved,
            remaining_tokens=max(0, self.global_cap - consumed - reserved),
            settled_requests=int(row["settled"] or 0),
            interrupted_reservations=int(row["interrupted"] or 0),
        )

    def close(self) -> None:
        with self._lock:
            self._connection.close()

    def __enter__(self) -> CloudUsageLedger:
        return self

    def __exit__(self, exc_type: object, exc: object, traceback: object) -> None:
        self.close()

    def _recover_interrupted_reservations(self) -> None:
        with self._lock, self._connection:
            self._connection.execute(
                """
                UPDATE cloud_reservations
                SET charged_tokens = reserved_tokens, status = 'interrupted',
                    settled_at = CURRENT_TIMESTAMP
                WHERE status = 'reserved'
                """
            )

    def _accounted_tokens(
        self, *, provider: str | None = None, model: str | None = None
    ) -> int:
        filters = ""
        parameters: tuple[str, ...] = ()
        if provider is not None and model is not None:
            filters = "WHERE provider = ? AND model = ?"
            parameters = (provider, model)
        row = self._connection.execute(
            f"""
            SELECT COALESCE(SUM(
                CASE WHEN status = 'reserved'
                    THEN reserved_tokens ELSE charged_tokens END
            ), 0) AS accounted
            FROM cloud_reservations {filters}
            """,
            parameters,
        ).fetchone()
        return int(row["accounted"])
