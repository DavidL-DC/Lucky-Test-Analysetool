from __future__ import annotations

from pathlib import Path

from .apple_api import AppStoreClient
from .config import load_app_store_config
from .database import Database
from .models import DashboardMetrics
from .report_parser import parse_reports


class AnalyticsService:
    def __init__(self, project_root: Path, database: Database):
        self.project_root = project_root
        self.database = database

    def refresh(self) -> DashboardMetrics:
        run_id = self.database.start_fetch()
        try:
            config = load_app_store_config(self.project_root)
            reports = AppStoreClient(config).fetch_latest_reports()
            metrics = parse_reports(reports)
            if not metrics:
                raise ValueError("Die Apple-Berichte enthielten keine passenden Kennzahlen.")
            self.database.upsert_daily_metrics(metrics)
            self.database.finish_fetch(run_id, True)
        except Exception as exc:
            self.database.finish_fetch(run_id, False, str(exc))
            raise
        return self.database.dashboard_metrics()

