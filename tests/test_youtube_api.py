from unittest import TestCase

from lucky_analyzer.youtube_api import YouTubeClient


class YouTubeApiTests(TestCase):
    def test_iso_duration_is_converted_to_seconds(self) -> None:
        self.assertEqual(YouTubeClient._duration_seconds("PT1H2M3S"), 3723)
        self.assertEqual(YouTubeClient._duration_seconds("PT45S"), 45)
        self.assertEqual(YouTubeClient._duration_seconds("P1DT2M"), 86520)

    def test_unknown_duration_returns_zero(self) -> None:
        self.assertEqual(YouTubeClient._duration_seconds("unknown"), 0)
