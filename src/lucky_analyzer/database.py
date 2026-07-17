from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, Iterator

from .models import (
    CustomerReview, DailyMetrics, DashboardMetrics, StorefrontRating,
    YouTubeChannelMetrics, YouTubeVideoMetrics,
    TikTokAccountMetrics, TikTokVideoMetrics,
    InstagramAccountMetrics, InstagramMediaMetrics,
)


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

CREATE TABLE IF NOT EXISTS youtube_channel_snapshots (
    captured_at TEXT PRIMARY KEY, channel_id TEXT NOT NULL, title TEXT NOT NULL,
    subscribers INTEGER NOT NULL, views INTEGER NOT NULL, video_count INTEGER NOT NULL,
    likes INTEGER NOT NULL, comments INTEGER NOT NULL, watch_minutes INTEGER,
    average_view_duration REAL
);

CREATE TABLE IF NOT EXISTS youtube_videos (
    video_id TEXT PRIMARY KEY, title TEXT NOT NULL, published_at TEXT NOT NULL,
    duration_seconds INTEGER NOT NULL, views INTEGER NOT NULL, likes INTEGER NOT NULL,
    comments INTEGER NOT NULL, watch_minutes INTEGER, average_view_duration REAL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS tiktok_account_snapshots (
    captured_at TEXT PRIMARY KEY, open_id TEXT NOT NULL, display_name TEXT NOT NULL,
    username TEXT NOT NULL, followers INTEGER NOT NULL, following INTEGER NOT NULL,
    likes INTEGER NOT NULL, video_count INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS tiktok_videos (
    video_id TEXT PRIMARY KEY, title TEXT NOT NULL, description TEXT NOT NULL,
    published_at TEXT NOT NULL, duration_seconds INTEGER NOT NULL,
    views INTEGER NOT NULL, likes INTEGER NOT NULL, comments INTEGER NOT NULL,
    shares INTEGER NOT NULL, updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS instagram_account_snapshots (
    captured_at TEXT PRIMARY KEY, account_id TEXT NOT NULL, username TEXT NOT NULL,
    followers INTEGER NOT NULL, following INTEGER NOT NULL, media_count INTEGER NOT NULL,
    reach INTEGER, profile_views INTEGER, views INTEGER, total_interactions INTEGER
);

CREATE TABLE IF NOT EXISTS instagram_media (
    media_id TEXT PRIMARY KEY, caption TEXT NOT NULL, media_type TEXT NOT NULL,
    product_type TEXT NOT NULL, published_at TEXT NOT NULL, likes INTEGER NOT NULL,
    comments INTEGER NOT NULL, views INTEGER, reach INTEGER, saved INTEGER,
    shares INTEGER, total_interactions INTEGER, watch_time_ms INTEGER,
    average_watch_time_ms INTEGER, updated_at TEXT NOT NULL
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

    def save_youtube_metrics(
        self, channel: YouTubeChannelMetrics, videos: Iterable[YouTubeVideoMetrics]
    ) -> None:
        captured_at = (channel.captured_at or datetime.now(timezone.utc)).isoformat()
        now = datetime.now(timezone.utc).isoformat()
        video_rows = [
            (v.video_id, v.title, v.published_at.isoformat(), v.duration_seconds,
             v.views, v.likes, v.comments, v.watch_minutes,
             v.average_view_duration, now)
            for v in videos
        ]
        with self._connection() as connection:
            connection.execute(
                """INSERT INTO youtube_channel_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (captured_at, channel.channel_id, channel.title, channel.subscribers,
                 channel.views, channel.video_count, channel.likes, channel.comments,
                 channel.watch_minutes, channel.average_view_duration),
            )
            connection.execute("DELETE FROM youtube_videos")
            connection.executemany(
                """INSERT INTO youtube_videos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(video_id) DO UPDATE SET title=excluded.title,
                   published_at=excluded.published_at, duration_seconds=excluded.duration_seconds,
                   views=excluded.views, likes=excluded.likes, comments=excluded.comments,
                   watch_minutes=excluded.watch_minutes,
                   average_view_duration=excluded.average_view_duration,
                   updated_at=excluded.updated_at""",
                video_rows,
            )

    def latest_youtube_channel(self) -> YouTubeChannelMetrics | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM youtube_channel_snapshots ORDER BY captured_at DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        return YouTubeChannelMetrics(
            channel_id=row["channel_id"], title=row["title"], subscribers=row["subscribers"],
            views=row["views"], video_count=row["video_count"], likes=row["likes"],
            comments=row["comments"], watch_minutes=row["watch_minutes"],
            average_view_duration=row["average_view_duration"],
            captured_at=datetime.fromisoformat(row["captured_at"]),
        )

    def youtube_videos(self) -> list[YouTubeVideoMetrics]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM youtube_videos ORDER BY published_at DESC"
            ).fetchall()
        return [YouTubeVideoMetrics(
            video_id=r["video_id"], title=r["title"],
            published_at=datetime.fromisoformat(r["published_at"]),
            duration_seconds=r["duration_seconds"], views=r["views"], likes=r["likes"],
            comments=r["comments"], watch_minutes=r["watch_minutes"],
            average_view_duration=r["average_view_duration"],
        ) for r in rows]

    def save_tiktok_metrics(
        self, account: TikTokAccountMetrics, videos: Iterable[TikTokVideoMetrics]
    ) -> None:
        captured_at = (account.captured_at or datetime.now(timezone.utc)).isoformat()
        now = datetime.now(timezone.utc).isoformat()
        rows = [
            (v.video_id, v.title, v.description, v.published_at.isoformat(),
             v.duration_seconds, v.views, v.likes, v.comments, v.shares, now)
            for v in videos
        ]
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO tiktok_account_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (captured_at, account.open_id, account.display_name, account.username,
                 account.followers, account.following, account.likes, account.video_count),
            )
            connection.execute("DELETE FROM tiktok_videos")
            connection.executemany(
                """INSERT INTO tiktok_videos VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(video_id) DO UPDATE SET title=excluded.title,
                   description=excluded.description, published_at=excluded.published_at,
                   duration_seconds=excluded.duration_seconds, views=excluded.views,
                   likes=excluded.likes, comments=excluded.comments, shares=excluded.shares,
                   updated_at=excluded.updated_at""",
                rows,
            )

    def latest_tiktok_account(self) -> TikTokAccountMetrics | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM tiktok_account_snapshots ORDER BY captured_at DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        return TikTokAccountMetrics(
            open_id=row["open_id"], display_name=row["display_name"], username=row["username"],
            followers=row["followers"], following=row["following"], likes=row["likes"],
            video_count=row["video_count"], captured_at=datetime.fromisoformat(row["captured_at"]),
        )

    def tiktok_videos(self) -> list[TikTokVideoMetrics]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM tiktok_videos ORDER BY published_at DESC"
            ).fetchall()
        return [TikTokVideoMetrics(
            video_id=r["video_id"], title=r["title"], description=r["description"],
            published_at=datetime.fromisoformat(r["published_at"]),
            duration_seconds=r["duration_seconds"], views=r["views"], likes=r["likes"],
            comments=r["comments"], shares=r["shares"],
        ) for r in rows]

    def save_instagram_metrics(
        self, account: InstagramAccountMetrics, media: Iterable[InstagramMediaMetrics]
    ) -> None:
        captured_at = (account.captured_at or datetime.now(timezone.utc)).isoformat()
        now = datetime.now(timezone.utc).isoformat()
        rows = [(
            item.media_id, item.caption, item.media_type, item.product_type,
            item.published_at.isoformat(), item.likes, item.comments, item.views,
            item.reach, item.saved, item.shares, item.total_interactions,
            item.watch_time_ms, item.average_watch_time_ms, now,
        ) for item in media]
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO instagram_account_snapshots VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (captured_at, account.account_id, account.username, account.followers,
                 account.following, account.media_count, account.reach,
                 account.profile_views, account.views, account.total_interactions),
            )
            connection.execute("DELETE FROM instagram_media")
            connection.executemany(
                "INSERT INTO instagram_media VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                rows,
            )

    def latest_instagram_account(self) -> InstagramAccountMetrics | None:
        with self._connection() as connection:
            row = connection.execute(
                "SELECT * FROM instagram_account_snapshots ORDER BY captured_at DESC LIMIT 1"
            ).fetchone()
        if not row:
            return None
        return InstagramAccountMetrics(
            account_id=row["account_id"], username=row["username"],
            followers=row["followers"], following=row["following"],
            media_count=row["media_count"], reach=row["reach"],
            profile_views=row["profile_views"], views=row["views"],
            total_interactions=row["total_interactions"],
            captured_at=datetime.fromisoformat(row["captured_at"]),
        )

    def instagram_media(self) -> list[InstagramMediaMetrics]:
        with self._connection() as connection:
            rows = connection.execute(
                "SELECT * FROM instagram_media ORDER BY published_at DESC"
            ).fetchall()
        return [InstagramMediaMetrics(
            media_id=r["media_id"], caption=r["caption"], media_type=r["media_type"],
            product_type=r["product_type"], published_at=datetime.fromisoformat(r["published_at"]),
            likes=r["likes"], comments=r["comments"], views=r["views"], reach=r["reach"],
            saved=r["saved"], shares=r["shares"], total_interactions=r["total_interactions"],
            watch_time_ms=r["watch_time_ms"], average_watch_time_ms=r["average_watch_time_ms"],
        ) for r in rows]
