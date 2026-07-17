from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from lucky_analyzer.database import Database
from lucky_analyzer.models import DailyMetrics


class DatabaseTests(TestCase):
    def test_upsert_does_not_duplicate_a_day(self) -> None:
        with TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            database.upsert_daily_metrics(
                [DailyMetrics(date(2026, 7, 15), first_downloads=4)]
            )
            database.upsert_daily_metrics(
                [DailyMetrics(date(2026, 7, 15), first_downloads=6)]
            )
            run_id = database.start_fetch()
            database.finish_fetch(run_id, True)
            metrics = database.dashboard_metrics()
            self.assertEqual(metrics.first_downloads, 6)
            self.assertEqual(metrics.total_downloads, 6)
            self.assertEqual(metrics.data_through, date(2026, 7, 15))
            self.assertIsNotNone(metrics.last_success_at)

