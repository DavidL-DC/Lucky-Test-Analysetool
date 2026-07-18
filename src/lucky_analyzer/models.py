from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum


class AnalysisPeriod(Enum):
    SEVEN_DAYS = ("7 Tage", 7)
    THIRTY_DAYS = ("30 Tage", 30)
    NINETY_DAYS = ("90 Tage", 90)
    ALL_TIME = ("Gesamt", None)

    def __init__(self, label: str, days: int | None):
        self.label = label
        self.days = days

    @classmethod
    def from_label(cls, label: str) -> "AnalysisPeriod":
        for period in cls:
            if period.label == label:
                return period
        raise ValueError(f"Unbekannter Analysezeitraum: {label}")


@dataclass(frozen=True)
class DailyMetrics:
    metric_date: date
    first_downloads: int = 0
    redownloads: int = 0
    updates: int = 0
    installations: int = 0
    deletions: int = 0

    @property
    def total_downloads(self) -> int:
        return self.first_downloads + self.redownloads


@dataclass(frozen=True)
class CustomerReview:
    review_id: str
    rating: int
    title: str
    body: str
    reviewer_nickname: str
    created_at: datetime
    territory: str


@dataclass(frozen=True)
class StorefrontRating:
    territory: str
    average_rating: float
    rating_count: int


@dataclass(frozen=True)
class DashboardMetrics:
    first_downloads: int = 0
    redownloads: int = 0
    total_downloads: int = 0
    updates: int = 0
    installations: int = 0
    deletions: int = 0
    dach_average_rating: float | None = None
    dach_rating_count: int = 0
    dach_rating_history_available: bool = False
    written_review_average: float | None = None
    written_review_count: int = 0
    written_review_distribution: tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)
    last_success_at: datetime | None = None
    data_through: date | None = None


@dataclass(frozen=True)
class YouTubeChannelMetrics:
    channel_id: str
    title: str
    subscribers: int
    views: int
    video_count: int
    likes: int
    comments: int
    watch_minutes: int | None = None
    average_view_duration: float | None = None
    captured_at: datetime | None = None


@dataclass(frozen=True)
class YouTubeVideoMetrics:
    video_id: str
    title: str
    published_at: datetime
    duration_seconds: int
    views: int
    likes: int
    comments: int
    watch_minutes: int | None = None
    average_view_duration: float | None = None


@dataclass(frozen=True)
class TikTokAccountMetrics:
    open_id: str
    display_name: str
    username: str
    followers: int
    following: int
    likes: int
    video_count: int
    captured_at: datetime | None = None


@dataclass(frozen=True)
class TikTokVideoMetrics:
    video_id: str
    title: str
    description: str
    published_at: datetime
    duration_seconds: int
    views: int
    likes: int
    comments: int
    shares: int


@dataclass(frozen=True)
class InstagramAccountMetrics:
    account_id: str
    username: str
    followers: int
    following: int
    media_count: int
    reach: int | None = None
    profile_views: int | None = None
    views: int | None = None
    total_interactions: int | None = None
    captured_at: datetime | None = None


@dataclass(frozen=True)
class InstagramMediaMetrics:
    media_id: str
    caption: str
    media_type: str
    product_type: str
    published_at: datetime
    likes: int
    comments: int
    views: int | None = None
    reach: int | None = None
    saved: int | None = None
    shares: int | None = None
    total_interactions: int | None = None
    watch_time_ms: int | None = None
    average_watch_time_ms: int | None = None
