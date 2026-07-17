from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from lucky_analyzer.config import ConfigurationError, load_app_store_config


class ConfigTests(TestCase):
    def test_missing_local_file_is_reported(self) -> None:
        with TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ConfigurationError, "Konfigurationsdatei fehlt"):
                load_app_store_config(Path(directory))

    def test_complete_configuration_is_loaded(self) -> None:
        with TemporaryDirectory() as directory:
            root = Path(directory)
            key_path = root / "key.p8"
            key_path.write_text("test", encoding="utf-8")
            (root / ".local.env").write_text(
                "\n".join(
                    [
                        "APP_STORE_ISSUER_ID=issuer",
                        "APP_STORE_KEY_ID=key-id",
                        "APP_STORE_PRIVATE_KEY_PATH=key.p8",
                        "APP_STORE_APP_ID=1234",
                        "APP_STORE_BUNDLE_ID=de.example.app",
                    ]
                ),
                encoding="utf-8",
            )
            config = load_app_store_config(root)
            self.assertEqual(config.app_id, "1234")
            self.assertEqual(config.private_key_path, key_path.resolve())

