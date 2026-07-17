from __future__ import annotations

import ipaddress
import json
import secrets
import ssl
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.x509.oid import NameOID

from .config import InstagramConfig
from .models import InstagramAccountMetrics, InstagramMediaMetrics


SCOPES = "instagram_business_basic,instagram_business_manage_insights"


class InstagramApiError(RuntimeError):
    pass


class InstagramClient:
    def __init__(self, config: InstagramConfig):
        self.config = config
        self.graph_root = f"https://graph.instagram.com/{config.api_version}"

    def fetch(self) -> tuple[InstagramAccountMetrics, list[InstagramMediaMetrics]]:
        token = self._access_token()
        profile = self._graph_json(
            "/me", token,
            fields="id,user_id,username,followers_count,follows_count,media_count",
        )
        account_id = str(profile.get("user_id") or profile.get("id") or "")
        if not account_id:
            raise InstagramApiError("Instagram lieferte keine Konto-ID.")
        account_insights = self._account_insights(account_id, token)
        media = self._media(account_id, token)
        return InstagramAccountMetrics(
            account_id=account_id, username=profile.get("username", ""),
            followers=int(profile.get("followers_count", 0)),
            following=int(profile.get("follows_count", 0)),
            media_count=int(profile.get("media_count", 0)),
            captured_at=datetime.now(timezone.utc), **account_insights,
        ), media

    def _media(self, account_id: str, token: str) -> list[InstagramMediaMetrics]:
        fields = (
            "id,caption,media_type,media_product_type,timestamp,"
            "like_count,comments_count"
        )
        url: str | None = self._graph_url(f"/{account_id}/media", fields=fields, limit="100")
        result: list[InstagramMediaMetrics] = []
        while url:
            response = self._request_json(url, token)
            for item in response.get("data", []):
                insights = self._media_insights(str(item["id"]), token)
                timestamp = item.get("timestamp", "").replace("Z", "+00:00")
                result.append(InstagramMediaMetrics(
                    media_id=str(item["id"]), caption=item.get("caption", ""),
                    media_type=item.get("media_type", ""),
                    product_type=item.get("media_product_type", ""),
                    published_at=datetime.fromisoformat(timestamp),
                    likes=int(item.get("like_count", 0)),
                    comments=int(item.get("comments_count", 0)), **insights,
                ))
            url = response.get("paging", {}).get("next")
        return result

    def _media_insights(self, media_id: str, token: str) -> dict[str, int | None]:
        mapping = {
            "views": "views", "reach": "reach", "saved": "saved", "shares": "shares",
            "total_interactions": "total_interactions",
            "ig_reels_video_view_total_time": "watch_time_ms",
            "ig_reels_avg_watch_time": "average_watch_time_ms",
        }
        values: dict[str, int | None] = {field: None for field in mapping.values()}
        for metric, field in mapping.items():
            try:
                response = self._graph_json(f"/{media_id}/insights", token, metric=metric)
            except InstagramApiError:
                continue
            values[field] = self._insight_value(response)
        return values

    def _account_insights(self, account_id: str, token: str) -> dict[str, int | None]:
        values: dict[str, int | None] = {
            "reach": None, "profile_views": None, "views": None,
            "total_interactions": None,
        }
        since = int((datetime.now(timezone.utc) - timedelta(days=30)).timestamp())
        until = int(datetime.now(timezone.utc).timestamp())
        for metric in values:
            try:
                response = self._graph_json(
                    f"/{account_id}/insights", token, metric=metric, period="day",
                    since=str(since), until=str(until),
                )
            except InstagramApiError:
                continue
            values[metric] = self._insight_value(response, total=True)
        return values

    @staticmethod
    def _insight_value(response: dict[str, Any], total: bool = False) -> int | None:
        data = response.get("data") or []
        if not data:
            return None
        metric = data[0]
        if "total_value" in metric:
            value = metric["total_value"].get("value")
            return int(value) if isinstance(value, (int, float)) else None
        raw_values = [entry.get("value") for entry in metric.get("values", [])]
        numbers = [value for value in raw_values if isinstance(value, (int, float))]
        if not numbers:
            return None
        return int(sum(numbers) if total else numbers[-1])

    def _access_token(self) -> str:
        token = self._read_token()
        if token and float(token.get("expires_at", 0)) > time.time() + 7 * 86400:
            return token["access_token"]
        if token and token.get("access_token"):
            try:
                refreshed = self._request_json(
                    "https://graph.instagram.com/refresh_access_token?" + urllib.parse.urlencode({
                        "grant_type": "ig_refresh_token", "access_token": token["access_token"],
                    })
                )
                return self._save_token(refreshed)["access_token"]
            except InstagramApiError:
                pass
        return self._authorize()["access_token"]

    def _authorize(self) -> dict[str, Any]:
        parsed = urllib.parse.urlparse(self.config.redirect_uri)
        if parsed.scheme != "https" or parsed.hostname != "localhost" or not parsed.port:
            raise InstagramApiError(
                "Die Instagram-Redirect-URI muss https://localhost mit festem Port verwenden."
            )
        self._ensure_local_certificate()
        state = secrets.token_urlsafe(24)
        result: dict[str, str] = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(inner_self) -> None:
                query = urllib.parse.parse_qs(urllib.parse.urlparse(inner_self.path).query)
                result.update({key: values[0] for key, values in query.items()})
                body = "<h2>Instagram-Anmeldung abgeschlossen</h2><p>Du kannst dieses Fenster schließen.</p>".encode("utf-8")
                inner_self.send_response(200)
                inner_self.send_header("Content-Type", "text/html; charset=utf-8")
                inner_self.send_header("Content-Length", str(len(body)))
                inner_self.end_headers()
                inner_self.wfile.write(body)

            def log_message(self, *_args: Any) -> None:
                return

        server = HTTPServer(("127.0.0.1", parsed.port), Handler)
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(self.config.certificate_path, self.config.private_key_path)
        server.socket = context.wrap_socket(server.socket, server_side=True)
        auth_url = "https://www.instagram.com/oauth/authorize?" + urllib.parse.urlencode({
            "client_id": self.config.app_id, "redirect_uri": self.config.redirect_uri,
            "response_type": "code", "scope": SCOPES, "state": state,
        })
        webbrowser.open(auth_url)
        deadline = time.monotonic() + 240
        server.timeout = 10
        while not result and time.monotonic() < deadline:
            try:
                server.handle_request()
            except ssl.SSLError:
                continue
        server.server_close()
        if result.get("state") != state or not result.get("code"):
            raise InstagramApiError(
                result.get("error_description") or result.get("error_reason")
                or result.get("error") or "Instagram-Anmeldung wurde nicht abgeschlossen."
            )
        short_token = self._post_form("https://api.instagram.com/oauth/access_token", {
            "client_id": self.config.app_id, "client_secret": self.config.app_secret,
            "grant_type": "authorization_code", "redirect_uri": self.config.redirect_uri,
            "code": result["code"].removesuffix("#_"),
        })
        access_token = short_token.get("access_token")
        if not access_token:
            raise InstagramApiError("Instagram lieferte kein Zugriffstoken.")
        long_token = self._request_json(
            "https://graph.instagram.com/access_token?" + urllib.parse.urlencode({
                "grant_type": "ig_exchange_token", "client_secret": self.config.app_secret,
                "access_token": access_token,
            })
        )
        return self._save_token(long_token)

    def _ensure_local_certificate(self) -> None:
        if self.config.certificate_path.exists() and self.config.private_key_path.exists():
            return
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        subject = issuer = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "localhost")])
        now = datetime.now(timezone.utc)
        certificate = (
            x509.CertificateBuilder().subject_name(subject).issuer_name(issuer)
            .public_key(key.public_key()).serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(minutes=5)).not_valid_after(now + timedelta(days=825))
            .add_extension(x509.SubjectAlternativeName([
                x509.DNSName("localhost"), x509.IPAddress(ipaddress.ip_address("127.0.0.1"))
            ]), critical=False).sign(key, hashes.SHA256())
        )
        self.config.certificate_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.private_key_path.write_bytes(key.private_bytes(
            serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        ))
        self.config.certificate_path.write_bytes(certificate.public_bytes(serialization.Encoding.PEM))

    def _read_token(self) -> dict[str, Any] | None:
        if not self.config.token_path.exists():
            return None
        return json.loads(self.config.token_path.read_text(encoding="utf-8"))

    def _save_token(self, token: dict[str, Any]) -> dict[str, Any]:
        if "access_token" not in token:
            raise InstagramApiError(self._error_text(token))
        token["expires_at"] = time.time() + int(token.get("expires_in", 5184000))
        self.config.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")
        return token

    def _graph_json(self, path: str, token: str, **params: str) -> dict[str, Any]:
        return self._request_json(self._graph_url(path, **params), token)

    def _graph_url(self, path: str, **params: str) -> str:
        return self.graph_root + path + ("?" + urllib.parse.urlencode(params) if params else "")

    def _post_form(self, url: str, values: dict[str, str]) -> dict[str, Any]:
        request = urllib.request.Request(
            url, urllib.parse.urlencode(values).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
        )
        return self._open_json(request)

    def _request_json(self, url: str, token: str | None = None) -> dict[str, Any]:
        headers = {"Authorization": f"Bearer {token}"} if token else {}
        return self._open_json(urllib.request.Request(url, headers=headers))

    @staticmethod
    def _open_json(request: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception as exc:
            detail = getattr(exc, "read", lambda: b"")().decode("utf-8", "replace")
            try:
                parsed = json.loads(detail)
                message = InstagramClient._error_text(parsed)
            except (ValueError, TypeError):
                message = detail or str(exc)
            raise InstagramApiError(f"Instagram API: {message}") from exc

    @staticmethod
    def _error_text(response: dict[str, Any]) -> str:
        error = response.get("error", response)
        return str(error.get("message") or error.get("error_description") or error)
