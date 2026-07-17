import json
from unittest import TestCase
from unittest.mock import patch

from lucky_analyzer.storefront_api import StorefrontClient


class FakeResponse:
    def __init__(self, payload: dict[str, object]):
        self.payload = payload

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def read(self) -> bytes:
        return json.dumps(self.payload).encode("utf-8")


class StorefrontClientTests(TestCase):
    def test_rating_and_count_are_read_from_lookup_response(self) -> None:
        payload = {
            "resultCount": 1,
            "results": [{"averageUserRating": 4.75, "userRatingCount": 20}],
        }
        with patch(
            "lucky_analyzer.storefront_api.urllib.request.urlopen",
            return_value=FakeResponse(payload),
        ) as urlopen:
            rating = StorefrontClient("123").fetch_rating("de")

        self.assertEqual(rating.territory, "DE")
        self.assertEqual(rating.average_rating, 4.75)
        self.assertEqual(rating.rating_count, 20)
        requested_url = urlopen.call_args.args[0].full_url
        self.assertIn("id=123", requested_url)
        self.assertIn("country=de", requested_url)

