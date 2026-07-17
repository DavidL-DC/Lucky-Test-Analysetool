from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from cryptography import x509

from lucky_analyzer.config import InstagramConfig
from lucky_analyzer.instagram_api import InstagramClient


class InstagramApiTests(TestCase):
    def test_insight_value_supports_series_and_total_value(self) -> None:
        self.assertEqual(InstagramClient._insight_value({
            "data": [{"values": [{"value": 2}, {"value": 3}]}]
        }), 3)
        self.assertEqual(InstagramClient._insight_value({
            "data": [{"total_value": {"value": 8}}]
        }), 8)

    def test_local_certificate_contains_localhost(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            config = InstagramConfig(
                "app", "secret", "https://localhost:3457/callback/",
                root / "token.json", root / "cert.pem", root / "key.pem", "v25.0",
            )
            InstagramClient(config)._ensure_local_certificate()
            certificate = x509.load_pem_x509_certificate(config.certificate_path.read_bytes())
            names = certificate.extensions.get_extension_for_class(
                x509.SubjectAlternativeName
            ).value.get_values_for_type(x509.DNSName)
            self.assertIn("localhost", names)
