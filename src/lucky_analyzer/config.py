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


@dataclass(frozen=True)
class YouTubeConfig:
    oauth_client_path: Path
    token_path: Path


@dataclass(frozen=True)
class TikTokConfig:
    client_key: str
    client_secret: str
    redirect_uri: str
    token_path: Path


@dataclass(frozen=True)
class InstagramConfig:
    app_id: str
    app_secret: str
    redirect_uri: str
    token_path: Path
    certificate_path: Path
    private_key_path: Path
    api_version: str


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


def load_youtube_config(project_root: Path) -> YouTubeConfig:
    values = load_local_values(project_root / ".local.env")
    client_path = Path(
        values.get("YOUTUBE_OAUTH_CLIENT_PATH", ".secrets/youtube_oauth_client.json")
    )
    token_path = Path(values.get("YOUTUBE_TOKEN_PATH", ".secrets/youtube_token.json"))
    if not client_path.is_absolute():
        client_path = project_root / client_path
    if not token_path.is_absolute():
        token_path = project_root / token_path
    if not client_path.is_file():
        raise ConfigurationError(f"YouTube-OAuth-Datei fehlt: {client_path.resolve()}")
    return YouTubeConfig(client_path.resolve(), token_path.resolve())


def load_tiktok_config(project_root: Path) -> TikTokConfig:
    values = load_local_values(project_root / ".local.env")
    required = ("TIKTOK_CLIENT_KEY", "TIKTOK_CLIENT_SECRET")
    missing = [name for name in required if not values.get(name)]
    if missing:
        raise ConfigurationError("Fehlende TikTok-Werte: " + ", ".join(missing))
    token_path = Path(values.get("TIKTOK_TOKEN_PATH", ".secrets/tiktok_token.json"))
    if not token_path.is_absolute():
        token_path = project_root / token_path
    return TikTokConfig(
        client_key=values["TIKTOK_CLIENT_KEY"],
        client_secret=values["TIKTOK_CLIENT_SECRET"],
        redirect_uri=values.get(
            "TIKTOK_REDIRECT_URI", "http://127.0.0.1:3456/callback/"
        ),
        token_path=token_path.resolve(),
    )


def load_instagram_config(project_root: Path) -> InstagramConfig:
    values = load_local_values(project_root / ".local.env")
    required = ("INSTAGRAM_APP_ID", "INSTAGRAM_APP_SECRET")
    missing = [name for name in required if not values.get(name)]
    if missing:
        raise ConfigurationError("Fehlende Instagram-Werte: " + ", ".join(missing))

    def local_path(name: str, default: str) -> Path:
        path = Path(values.get(name, default))
        return (project_root / path).resolve() if not path.is_absolute() else path.resolve()

    return InstagramConfig(
        app_id=values["INSTAGRAM_APP_ID"],
        app_secret=values["INSTAGRAM_APP_SECRET"],
        redirect_uri=values.get(
            "INSTAGRAM_REDIRECT_URI", "https://localhost:3457/callback/"
        ),
        token_path=local_path("INSTAGRAM_TOKEN_PATH", ".secrets/instagram_token.json"),
        certificate_path=local_path(
            "INSTAGRAM_CERTIFICATE_PATH", ".secrets/instagram_localhost_cert.pem"
        ),
        private_key_path=local_path(
            "INSTAGRAM_PRIVATE_KEY_PATH", ".secrets/instagram_localhost_key.pem"
        ),
        api_version=values.get("INSTAGRAM_API_VERSION", "v25.0"),
    )

