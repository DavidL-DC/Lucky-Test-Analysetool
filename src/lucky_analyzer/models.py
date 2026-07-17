from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime


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
    written_review_average: float | None = None
    written_review_count: int = 0
    written_review_distribution: tuple[int, int, int, int, int] = (0, 0, 0, 0, 0)
    last_success_at: datetime | None = None
    data_through: date | None = None
