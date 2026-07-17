from __future__ import annotations

from pathlib import Path

from .apple_api import AppStoreClient
from .config import load_app_store_config
from .database import Database
from .models import DashboardMetrics
from .report_parser import parse_reports
from .storefront_api import StorefrontClient


class AnalyticsService:
    def __init__(self, project_root: Path, database: Database):
        self.project_root = project_root
        self.database = database

    def refresh(self) -> DashboardMetrics:
        run_id = self.database.start_fetch()
        errors: list[str] = []
        try:
            config = load_app_store_config(self.project_root)
            client = AppStoreClient(config)
        except Exception as exc:
            self.database.finish_fetch(run_id, False, str(exc))
            raise

        try:
            reports = client.fetch_latest_reports()
            metrics = parse_reports(reports)
            if not metrics:
                raise ValueError("Die Apple-Berichte enthielten keine passenden Kennzahlen.")
            self.database.upsert_daily_metrics(metrics)
        except Exception as exc:
            errors.append(f"Analytics-Berichte: {exc}")

        try:
            reviews = client.fetch_customer_reviews()
            self.database.upsert_customer_reviews(reviews)
        except Exception as exc:
            errors.append(f"Schriftliche Rezensionen: {exc}")

        try:
            ratings = StorefrontClient(config.app_id).fetch_dach_ratings()
            self.database.upsert_storefront_ratings(ratings)
        except Exception as exc:
            errors.append(f"DACH-Gesamtbewertung: {exc}")

        if errors:
            message = "\n\n".join(errors)
            self.database.finish_fetch(run_id, False, message)
            raise RuntimeError(message)

        self.database.finish_fetch(run_id, True)
        return self.database.dashboard_metrics()
