from unittest import TestCase

from lucky_analyzer.tiktok_api import TikTokApiError, TikTokClient


class TikTokApiTests(TestCase):
    def test_ok_response_is_accepted(self) -> None:
        TikTokClient._raise_api_error({"error": {"code": "ok", "message": ""}})

    def test_api_error_is_reported(self) -> None:
        with self.assertRaisesRegex(TikTokApiError, "scope_not_authorized"):
            TikTokClient._raise_api_error({
                "error": {"code": "scope_not_authorized", "message": "Scope fehlt"}
            })
