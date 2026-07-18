from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from lucky_analyzer.database import Database
from lucky_analyzer.models import (
    CustomerReview, DailyMetrics, StorefrontRating,
    YouTubeChannelMetrics, YouTubeVideoMetrics,
    TikTokAccountMetrics, TikTokVideoMetrics,
    InstagramAccountMetrics, InstagramMediaMetrics,
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

    def test_dashboard_metrics_filter_app_events_by_period(self) -> None:
        with TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            database.upsert_daily_metrics(
                [
                    DailyMetrics(date(2026, 7, 1), first_downloads=10, updates=1),
                    DailyMetrics(date(2026, 7, 4), first_downloads=4, updates=2),
                    DailyMetrics(date(2026, 7, 10), first_downloads=1, updates=3),
                ]
            )

            metrics = database.dashboard_metrics(period_days=7, as_of=date(2026, 7, 10))

            self.assertEqual(metrics.first_downloads, 5)
            self.assertEqual(metrics.total_downloads, 5)
            self.assertEqual(metrics.updates, 5)
            self.assertEqual(metrics.data_through, date(2026, 7, 10))

    def test_dashboard_metrics_keep_all_events_for_total_period(self) -> None:
        with TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            database.upsert_daily_metrics(
                [
                    DailyMetrics(date(2026, 1, 1), first_downloads=10),
                    DailyMetrics(date(2026, 7, 10), first_downloads=2),
                ]
            )

            metrics = database.dashboard_metrics(period_days=None)

            self.assertEqual(metrics.first_downloads, 12)

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

    def test_youtube_period_growth_uses_historical_snapshots(self) -> None:
        with TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            old_time = datetime.now(timezone.utc) - timedelta(days=40)
            new_time = datetime.now(timezone.utc)
            old_channel = YouTubeChannelMetrics(
                "channel", "Lucky", 100, 1_000, 1, 50, 10,
                watch_minutes=200, captured_at=old_time,
            )
            new_channel = YouTubeChannelMetrics(
                "channel", "Lucky", 112, 1_300, 1, 80, 16,
                watch_minutes=260, captured_at=new_time,
            )
            old_video = YouTubeVideoMetrics(
                "video", "Video", old_time, 60, 1_000, 50, 10, 200
            )
            new_video = YouTubeVideoMetrics(
                "video", "Video", old_time, 60, 1_300, 80, 16, 260
            )
            database.save_youtube_metrics(old_channel, [old_video])
            database.save_youtube_metrics(new_channel, [new_video])

            totals = database.social_period_growth("youtube", 30)
            items = database.social_item_period_growth("youtube", 30)

            self.assertEqual(totals["subscribers"], 12)
            self.assertEqual(totals["items_views"], 300)
            self.assertEqual(items["video"]["likes"], 30)

    def test_tiktok_sync_replaces_the_public_video_list(self) -> None:
        with TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            account = TikTokAccountMetrics("user", "Lucky", "lucky", 5, 1, 20, 1)

            def video(video_id: str) -> TikTokVideoMetrics:
                return TikTokVideoMetrics(
                    video_id, video_id, "", datetime(2026, 7, 1, tzinfo=timezone.utc),
                    12, 100, 10, 2, 1,
                )

            database.save_tiktok_metrics(account, [video("old")])
            database.save_tiktok_metrics(account, [video("current")])

            self.assertEqual(database.latest_tiktok_account().followers, 5)
            self.assertEqual([item.video_id for item in database.tiktok_videos()], ["current"])

    def test_instagram_sync_replaces_media_and_keeps_latest_account(self) -> None:
        with TemporaryDirectory() as directory:
            database = Database(Path(directory) / "test.sqlite3")
            account = InstagramAccountMetrics("ig", "lucky", 12, 3, 1, reach=50)

            def medium(media_id: str) -> InstagramMediaMetrics:
                return InstagramMediaMetrics(
                    media_id, media_id, "IMAGE", "FEED",
                    datetime(2026, 7, 1, tzinfo=timezone.utc), 4, 1, views=20,
                )

            database.save_instagram_metrics(account, [medium("old")])
            database.save_instagram_metrics(account, [medium("current")])

            self.assertEqual(database.latest_instagram_account().reach, 50)
            self.assertEqual(
                [item.media_id for item in database.instagram_media()], ["current"]
            )
