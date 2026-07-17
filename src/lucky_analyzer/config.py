from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


class ConfigurationError(ValueError):
    """Die lokale App-Store-Konfiguration ist unvollständig oder ungültig."""


@dataclass(frozen=True)
class AppStoreConfig:
    issuer_id: str
    key_id: str
    private_key_path: Path
    app_id: str
    bundle_id: str


def load_local_values(path: Path) -> dict[str, str]:
    if not path.exists():
        raise ConfigurationError(
            f"Konfigurationsdatei fehlt: {path}. Bitte .local.env.example kopieren."
        )

    values: dict[str, str] = {}
    for line_number, raw_line in enumerate(
        path.read_text(encoding="utf-8").splitlines(), start=1
    ):
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            raise ConfigurationError(f"Ungültige Zeile {line_number} in {path}.")
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def load_app_store_config(project_root: Path) -> AppStoreConfig:
    values = load_local_values(project_root / ".local.env")
    required = {
        "APP_STORE_ISSUER_ID",
        "APP_STORE_KEY_ID",
        "APP_STORE_PRIVATE_KEY_PATH",
        "APP_STORE_APP_ID",
        "APP_STORE_BUNDLE_ID",
    }
    missing = sorted(name for name in required if not values.get(name))
    if missing:
        raise ConfigurationError("Fehlende Werte: " + ", ".join(missing))

    private_key_path = Path(values["APP_STORE_PRIVATE_KEY_PATH"])
    if not private_key_path.is_absolute():
        private_key_path = project_root / private_key_path
    private_key_path = private_key_path.resolve()
    if not private_key_path.is_file():
        raise ConfigurationError(f"P8-Schlüsseldatei fehlt: {private_key_path}")

    return AppStoreConfig(
        issuer_id=values["APP_STORE_ISSUER_ID"],
        key_id=values["APP_STORE_KEY_ID"],
        private_key_path=private_key_path,
        app_id=values["APP_STORE_APP_ID"],
        bundle_id=values["APP_STORE_BUNDLE_ID"],
    )

