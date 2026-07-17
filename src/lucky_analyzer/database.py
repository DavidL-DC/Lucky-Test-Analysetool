from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from .models import CustomerReview, DailyMetrics, DashboardMetrics, StorefrontRating


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

CREATE TABLE IF NOT EXISTS customer_reviews (
    review_id TEXT PRIMARY KEY,
    rating INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    title TEXT NOT NULL,
    body TEXT NOT NULL,
    reviewer_nickname TEXT NOT NULL,
    created_at TEXT NOT NULL,
    territory TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS storefront_ratings (
    territory TEXT PRIMARY KEY,
    average_rating REAL NOT NULL,
    rating_count INTEGER NOT NULL,
    updated_at TEXT NOT NULL
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

    def upsert_customer_reviews(self, reviews: Iterable[CustomerReview]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            (
                review.review_id,
                review.rating,
                review.title,
                review.body,
                review.reviewer_nickname,
                review.created_at.isoformat(),
                review.territory,
                now,
            )
            for review in reviews
        ]
        with self._connection() as connection:
            connection.executemany(
                """
                INSERT INTO customer_reviews(
                    review_id, rating, title, body, reviewer_nickname,
                    created_at, territory, updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(review_id) DO UPDATE SET
                    rating = excluded.rating,
                    title = excluded.title,
                    body = excluded.body,
                    reviewer_nickname = excluded.reviewer_nickname,
                    created_at = excluded.created_at,
                    territory = excluded.territory,
                    updated_at = excluded.updated_at
                """,
                rows,
            )

    def upsert_storefront_ratings(self, ratings: Iterable[StorefrontRating]) -> None:
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            (rating.territory, rating.average_rating, rating.rating_count, now)
            for rating in ratings
        ]
        with self._connection() as connection:
            connection.executemany(
                """
                INSERT INTO storefront_ratings(
                    territory, average_rating, rating_count, updated_at
                ) VALUES (?, ?, ?, ?)
                ON CONFLICT(territory) DO UPDATE SET
                    average_rating = excluded.average_rating,
                    rating_count = excluded.rating_count,
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
            review_summary = connection.execute(
                """
                SELECT AVG(rating) AS average_rating, COUNT(*) AS rating_count
                FROM customer_reviews
                """
            ).fetchone()
            review_distribution_rows = connection.execute(
                """
                SELECT rating, COUNT(*) AS count
                FROM customer_reviews
                GROUP BY rating
                """
            ).fetchall()
            dach_summary = connection.execute(
                """
                SELECT
                    CASE WHEN SUM(rating_count) > 0
                        THEN SUM(average_rating * rating_count) / SUM(rating_count)
                        ELSE NULL
                    END AS average_rating,
                    COALESCE(SUM(rating_count), 0) AS rating_count
                FROM storefront_ratings
                WHERE territory IN ('DE', 'AT', 'CH')
                """
            ).fetchone()

        first_downloads = int(totals["first_downloads"])
        redownloads = int(totals["redownloads"])
        review_distribution = [0, 0, 0, 0, 0]
        for row in review_distribution_rows:
            review_distribution[int(row["rating"]) - 1] = int(row["count"])
        return DashboardMetrics(
            first_downloads=first_downloads,
            redownloads=redownloads,
            total_downloads=first_downloads + redownloads,
            updates=int(totals["updates"]),
            installations=int(totals["installations"]),
            deletions=int(totals["deletions"]),
            dach_average_rating=dach_summary["average_rating"],
            dach_rating_count=int(dach_summary["rating_count"]),
            written_review_average=review_summary["average_rating"],
            written_review_count=int(review_summary["rating_count"]),
            written_review_distribution=tuple(review_distribution),
            last_success_at=(
                datetime.fromisoformat(last_run["finished_at"]) if last_run else None
            ),
            data_through=(date.fromisoformat(totals["data_through"]) if totals["data_through"] else None),
        )

    def latest_customer_reviews(self, limit: int = 100) -> list[CustomerReview]:
        with self._connection() as connection:
            rows = connection.execute(
                """
                SELECT review_id, rating, title, body, reviewer_nickname,
                       created_at, territory
                FROM customer_reviews
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()
        return [
            CustomerReview(
                review_id=row["review_id"],
                rating=int(row["rating"]),
                title=row["title"],
                body=row["body"],
                reviewer_nickname=row["reviewer_nickname"],
                created_at=datetime.fromisoformat(row["created_at"]),
                territory=row["territory"],
            )
            for row in rows
        ]
