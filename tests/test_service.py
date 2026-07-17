from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import patch

from lucky_analyzer.database import Database
from lucky_analyzer.models import CustomerReview, StorefrontRating
from lucky_analyzer.service import AnalyticsService


class ServiceTests(TestCase):
    def test_reviews_are_saved_while_analytics_reports_are_pending(self) -> None:
        review = CustomerReview(
            review_id="review-1",
            rating=4,
            title="Gut",
            body="Rezension",
            reviewer_nickname="Tester",
            created_at=datetime(2026, 7, 16, tzinfo=timezone.utc),
            territory="DEU",
        )

        class TestClient:
            def __init__(self, config):
                pass

            def fetch_latest_reports(self):
                raise RuntimeError("Berichte noch nicht bereit")

            def fetch_customer_reviews(self):
                return [review]

        class TestStorefrontClient:
            def __init__(self, app_id):
                pass

            def fetch_dach_ratings(self):
                return [
                    StorefrontRating("DE", 4.0, 1),
                    StorefrontRating("AT", 0.0, 0),
                    StorefrontRating("CH", 0.0, 0),
                ]

        with TemporaryDirectory() as directory:
            root = Path(directory)
            database = Database(root / "test.sqlite3")
            service = AnalyticsService(root, database)
            with (
                patch(
                    "lucky_analyzer.service.load_app_store_config",
                    return_value=SimpleNamespace(app_id="123"),
                ),
                patch("lucky_analyzer.service.AppStoreClient", TestClient),
                patch("lucky_analyzer.service.StorefrontClient", TestStorefrontClient),
            ):
                with self.assertRaisesRegex(RuntimeError, "Berichte noch nicht bereit"):
                    service.refresh()

            metrics = database.dashboard_metrics()
            self.assertEqual(metrics.written_review_count, 1)
            self.assertEqual(metrics.written_review_average, 4.0)
