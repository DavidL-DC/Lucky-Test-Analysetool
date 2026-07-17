from datetime import date, datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from lucky_analyzer.database import Database
from lucky_analyzer.models import (
    CustomerReview, DailyMetrics, StorefrontRating,
    YouTubeChannelMetrics, YouTubeVideoMetrics,
)


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

    def test_customer_reviews_are_upserted_and_summarized(self) -> None:
        with TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            first = CustomerReview(
                review_id="one",
                rating=3,
                title="Titel",
                body="Text",
                reviewer_nickname="Name",
                created_at=datetime(2026, 7, 15, tzinfo=timezone.utc),
                territory="DEU",
            )
            second = CustomerReview(
                review_id="two",
                rating=5,
                title="Titel 2",
                body="Text 2",
                reviewer_nickname="Name 2",
                created_at=datetime(2026, 7, 16, tzinfo=timezone.utc),
                territory="DEU",
            )
            database.upsert_customer_reviews([first, second])
            database.upsert_customer_reviews(
                [
                    CustomerReview(
                        review_id="one",
                        rating=5,
                        title=first.title,
                        body=first.body,
                        reviewer_nickname=first.reviewer_nickname,
                        created_at=first.created_at,
                        territory=first.territory,
                    )
                ]
            )
            metrics = database.dashboard_metrics()
            self.assertEqual(metrics.written_review_count, 2)
            self.assertEqual(metrics.written_review_average, 5.0)
            self.assertEqual(metrics.written_review_distribution, (0, 0, 0, 0, 2))
            latest_reviews = database.latest_customer_reviews()
            self.assertEqual([review.review_id for review in latest_reviews], ["two", "one"])
            self.assertEqual(latest_reviews[0].body, "Text 2")

    def test_dach_rating_is_weighted_by_country_rating_counts(self) -> None:
        with TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            database.upsert_storefront_ratings(
                [
                    StorefrontRating("DE", 5.0, 10),
                    StorefrontRating("AT", 4.0, 5),
                    StorefrontRating("CH", 3.0, 5),
                ]
            )
            metrics = database.dashboard_metrics()
            self.assertEqual(metrics.dach_rating_count, 20)
            self.assertEqual(metrics.dach_average_rating, 4.25)

    def test_youtube_sync_removes_videos_missing_from_latest_result(self) -> None:
        with TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            channel = YouTubeChannelMetrics("channel", "Lucky Test", 10, 100, 2, 8, 3)

            def video(video_id: str) -> YouTubeVideoMetrics:
                return YouTubeVideoMetrics(
                    video_id, video_id, datetime(2026, 7, 1, tzinfo=timezone.utc),
                    60, 10, 2, 1,
                )

            database.save_youtube_metrics(channel, [video("public"), video("private")])
            database.save_youtube_metrics(channel, [video("public")])

            self.assertEqual(
                [item.video_id for item in database.youtube_videos()], ["public"]
            )
