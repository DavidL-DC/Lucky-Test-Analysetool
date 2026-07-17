from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from .models import DailyMetrics, DashboardMetrics


SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_app_metrics (
    metric_date TEXT PRIMARY KEY,
    first_downloads INTEGER NOT NULL DEFAULT 0,
    redownloads INTEGER NOT NULL DEFAULT 0,
    updates INTEGER NOT NULL DEFAULT 0,
    installations INTEGER NOT NULL DEFAULT 0,
    deletions INTEGER NOT NULL DEFAULT 0,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS fetch_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL CHECK (status IN ('running', 'success', 'error')),
    message TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS app_rating_snapshots (
    captured_at TEXT PRIMARY KEY,
    average_rating REAL,
    rating_count INTEGER
);
"""


class Database:
    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        return connection

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = self.connect()
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize(self) -> None:
        with self._connection() as connection:
            connection.executescript(SCHEMA)

    def start_fetch(self) -> int:
        started_at = datetime.now(timezone.utc).isoformat()
        with self._connection() as connection:
            cursor = connection.execute(
                "INSERT INTO fetch_runs(started_at, status) VALUES (?, 'running')",
                (started_at,),
            )
            return int(cursor.lastrowid)

    def finish_fetch(self, run_id: int, success: bool, message: str = "") -> None:
        with self._connection() as connection:
            connection.execute(
                """
                UPDATE fetch_runs
                SET finished_at = ?, status = ?, message = ?
                WHERE id = ?
                """,
                (
                    datetime.now(timezone.utc).isoformat(),
                    "success" if success else "error",
                    message,
                    run_id,
                ),
            )

    def upsert_daily_metrics(self, metrics: Iterable[DailyMetrics]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            (
                item.metric_date.isoformat(),
                item.first_downloads,
                item.redownloads,
                item.updates,
                item.installations,
                item.deletions,
                now,
            )
            for item in metrics
        ]
        with self._connection() as connection:
            connection.executemany(
                """
                INSERT INTO daily_app_metrics(
                    metric_date, first_downloads, redownloads, updates,
                    installations, deletions, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(metric_date) DO UPDATE SET
                    first_downloads = excluded.first_downloads,
                    redownloads = excluded.redownloads,
                    updates = excluded.updates,
                    installations = excluded.installations,
                    deletions = excluded.deletions,
                    updated_at = excluded.updated_at
                """,
                rows,
            )

    def dashboard_metrics(self) -> DashboardMetrics:
        with self._connection() as connection:
            totals = connection.execute(
                """
                SELECT
                    COALESCE(SUM(first_downloads), 0) AS first_downloads,
                    COALESCE(SUM(redownloads), 0) AS redownloads,
                    COALESCE(SUM(updates), 0) AS updates,
                    COALESCE(SUM(installations), 0) AS installations,
                    COALESCE(SUM(deletions), 0) AS deletions,
                    MAX(metric_date) AS data_through
                FROM daily_app_metrics
                """
            ).fetchone()
            last_run = connection.execute(
                """
                SELECT finished_at FROM fetch_runs
                WHERE status = 'success' ORDER BY id DESC LIMIT 1
                """
            ).fetchone()
            rating = connection.execute(
                """
                SELECT average_rating, rating_count FROM app_rating_snapshots
                ORDER BY captured_at DESC LIMIT 1
                """
            ).fetchone()

        first_downloads = int(totals["first_downloads"])
        redownloads = int(totals["redownloads"])
        return DashboardMetrics(
            first_downloads=first_downloads,
            redownloads=redownloads,
            total_downloads=first_downloads + redownloads,
            updates=int(totals["updates"]),
            installations=int(totals["installations"]),
            deletions=int(totals["deletions"]),
            average_rating=rating["average_rating"] if rating else None,
            rating_count=rating["rating_count"] if rating else None,
            last_success_at=(
                datetime.fromisoformat(last_run["finished_at"]) if last_run else None
            ),
            data_through=(date.fromisoformat(totals["data_through"]) if totals["data_through"] else None),
        )
