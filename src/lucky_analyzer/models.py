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
class DashboardMetrics:
    first_downloads: int = 0
    redownloads: int = 0
    total_downloads: int = 0
    updates: int = 0
    installations: int = 0
    deletions: int = 0
    average_rating: float | None = None
    rating_count: int | None = None
    last_success_at: datetime | None = None
    data_through: date | None = None

