import base64
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

from lucky_analyzer.apple_api import AppStoreClient, ReportPayload, create_jwt
from lucky_analyzer.config import AppStoreConfig


def decode_segment(value: str) -> dict[str, object]:
    value += "=" * (-len(value) % 4)
    return json.loads(base64.urlsafe_b64decode(value))


class JwtTests(TestCase):
    def test_jwt_contains_apple_claims_and_raw_signature(self) -> None:
        with TemporaryDirectory() as directory:
            key = ec.generate_private_key(ec.SECP256R1())
            key_path = Path(directory) / "AuthKey.p8"
            key_path.write_bytes(
                key.private_bytes(
                    serialization.Encoding.PEM,
                    serialization.PrivateFormat.PKCS8,
                    serialization.NoEncryption(),
                )
            )
            config = AppStoreConfig(
                issuer_id="issuer",
                key_id="key-id",
                private_key_path=key_path,
                app_id="123",
                bundle_id="de.example.app",
            )
            header, payload, signature = create_jwt(config, now=1000).split(".")
            self.assertEqual(decode_segment(header)["kid"], "key-id")
            self.assertEqual(decode_segment(payload)["iss"], "issuer")
            self.assertEqual(decode_segment(payload)["exp"], 1900)
            signature += "=" * (-len(signature) % 4)
            self.assertEqual(len(base64.urlsafe_b64decode(signature)), 64)


class ReportSelectionTests(TestCase):
    def test_report_requests_are_read_through_the_app_relationship(self) -> None:
        requested_paths: list[str] = []

        class TestClient(AppStoreClient):
            def _get_all(self, path, query=None):
                requested_paths.append(path)
                return [
                    {
                        "id": "request-id",
                        "attributes": {"accessType": "ONGOING"},
                    }
                ]

        config = AppStoreConfig(
            issuer_id="issuer",
            key_id="key",
            private_key_path=Path("unused"),
            app_id="123",
            bundle_id="de.example.app",
        )
        request_id = TestClient(config)._find_or_create_report_request()
        self.assertEqual(request_id, "request-id")
        self.assertEqual(
            requested_paths, ["/v1/apps/123/analyticsReportRequests"]
        )

    def test_standard_report_is_preferred_over_detailed_report(self) -> None:
        class TestClient(AppStoreClient):
            def _find_or_create_report_request(self) -> str:
                return "request-id"

            def _get_all(self, path, query=None):
                return [
                    {"id": "detailed", "attributes": {"name": "App Store Downloads Detailed"}},
                    {"id": "standard", "attributes": {"name": "App Store Downloads Standard"}},
                    {
                        "id": "installs",
                        "attributes": {
                            "name": "App Store Installations and Deletions Standard"
                        },
                    },
                ]

            def _latest_report_payload(self, report, kind, name):
                return ReportPayload(kind, name, "2026-07-16", (b"content",))

        config = AppStoreConfig(
            issuer_id="issuer",
            key_id="key",
            private_key_path=Path("unused"),
            app_id="123",
            bundle_id="de.example.app",
        )
        reports = TestClient(config).fetch_latest_reports()
        names = {report.report_name for report in reports}
        self.assertIn("App Store Downloads Standard", names)
        self.assertNotIn("App Store Downloads Detailed", names)


class CustomerReviewTests(TestCase):
    def test_customer_reviews_are_mapped_from_apple_response(self) -> None:
        class TestClient(AppStoreClient):
            def _get_all(self, path, query=None):
                self.requested_path = path
                self.requested_query = query
                return [
                    {
                        "id": "review-1",
                        "attributes": {
                            "rating": 5,
                            "title": "Sehr gut",
                            "body": "Macht Spaß.",
                            "reviewerNickname": "Tester",
                            "createdDate": "2026-07-16T10:30:00Z",
                            "territory": "DEU",
                        },
                    }
                ]

        config = AppStoreConfig(
            issuer_id="issuer",
            key_id="key",
            private_key_path=Path("unused"),
            app_id="123",
            bundle_id="de.example.app",
        )
        client = TestClient(config)
        reviews = client.fetch_customer_reviews()
        self.assertEqual(client.requested_path, "/v1/apps/123/customerReviews")
        self.assertEqual(client.requested_query["sort"], "-createdDate")
        self.assertEqual(reviews[0].review_id, "review-1")
        self.assertEqual(reviews[0].rating, 5)
        self.assertEqual(reviews[0].territory, "DEU")
