from __future__ import annotations

import hashlib
import json
import secrets
import string
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from .config import TikTokConfig
from .models import TikTokAccountMetrics, TikTokVideoMetrics


SCOPES = "user.info.basic,user.info.profile,user.info.stats,video.list"
API_ROOT = "https://open.tiktokapis.com/v2"


class TikTokApiError(RuntimeError):
    pass


class TikTokClient:
    def __init__(self, config: TikTokConfig):
        self.config = config

    def fetch(self) -> tuple[TikTokAccountMetrics, list[TikTokVideoMetrics]]:
        token = self._access_token()
        user_response = self._request_json(
            f"{API_ROOT}/user/info/?" + urllib.parse.urlencode({
                "fields": "open_id,display_name,username,follower_count,following_count,likes_count,video_count"
            }),
            token,
        )
        self._raise_api_error(user_response)
        user = user_response.get("data", {}).get("user", {})
        if not user.get("open_id"):
            raise TikTokApiError("TikTok lieferte keine Kontodaten.")
        account = TikTokAccountMetrics(
            open_id=user["open_id"], display_name=user.get("display_name", ""),
            username=user.get("username", ""), followers=int(user.get("follower_count", 0)),
            following=int(user.get("following_count", 0)), likes=int(user.get("likes_count", 0)),
            video_count=int(user.get("video_count", 0)), captured_at=datetime.now(timezone.utc),
        )
        return account, self._videos(token)

    def _videos(self, token: str) -> list[TikTokVideoMetrics]:
        fields = (
            "id,title,video_description,create_time,duration,"
            "view_count,like_count,comment_count,share_count"
        )
        videos: list[TikTokVideoMetrics] = []
        cursor: int | None = None
        while True:
            body: dict[str, Any] = {"max_count": 20}
            if cursor is not None:
                body["cursor"] = cursor
            response = self._request_json(
                f"{API_ROOT}/video/list/?" + urllib.parse.urlencode({"fields": fields}),
                token, body,
            )
            self._raise_api_error(response)
            data = response.get("data", {})
            for item in data.get("videos", []):
                videos.append(TikTokVideoMetrics(
                    video_id=item["id"], title=item.get("title", ""),
                    description=item.get("video_description", ""),
                    published_at=datetime.fromtimestamp(int(item.get("create_time", 0)), timezone.utc),
                    duration_seconds=int(item.get("duration", 0)), views=int(item.get("view_count", 0)),
                    likes=int(item.get("like_count", 0)), comments=int(item.get("comment_count", 0)),
                    shares=int(item.get("share_count", 0)),
                ))
            if not data.get("has_more"):
                return videos
            new_cursor = int(data["cursor"])
            if cursor == new_cursor:
                raise TikTokApiError("TikTok lieferte beim Videoabruf wiederholt denselben Cursor.")
            cursor = new_cursor

    def _access_token(self) -> str:
        token = self._read_token()
        if token and float(token.get("expires_at", 0)) > time.time() + 60:
            return token["access_token"]
        if token and token.get("refresh_token"):
            refreshed = self._token_request({
                "client_key": self.config.client_key,
                "client_secret": self.config.client_secret,
                "grant_type": "refresh_token",
                "refresh_token": token["refresh_token"],
            })
            return self._save_token(refreshed)["access_token"]
        return self._authorize()["access_token"]

    def _authorize(self) -> dict[str, Any]:
        parsed = urllib.parse.urlparse(self.config.redirect_uri)
        if parsed.hostname not in ("127.0.0.1", "localhost") or not parsed.port:
            raise TikTokApiError("Die TikTok-Redirect-URI benötigt localhost und einen festen Port.")
        state = secrets.token_urlsafe(24)
        alphabet = string.ascii_letters + string.digits + "-._~"
        verifier = "".join(secrets.choice(alphabet) for _ in range(64))
        challenge = hashlib.sha256(verifier.encode("ascii")).hexdigest()
        result: dict[str, str] = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(inner_self) -> None:
                query = urllib.parse.parse_qs(urllib.parse.urlparse(inner_self.path).query)
                result.update({key: values[0] for key, values in query.items()})
                body = "<h2>TikTok-Anmeldung abgeschlossen</h2><p>Du kannst dieses Fenster schließen.</p>".encode("utf-8")
                inner_self.send_response(200)
                inner_self.send_header("Content-Type", "text/html; charset=utf-8")
                inner_self.send_header("Content-Length", str(len(body)))
                inner_self.end_headers()
                inner_self.wfile.write(body)

            def log_message(self, *_args: Any) -> None:
                return

        server = HTTPServer((parsed.hostname, parsed.port), Handler)
        auth_url = "https://www.tiktok.com/v2/auth/authorize/?" + urllib.parse.urlencode({
            "client_key": self.config.client_key, "scope": SCOPES,
            "response_type": "code", "redirect_uri": self.config.redirect_uri,
            "state": state, "code_challenge": challenge, "code_challenge_method": "S256",
        })
        webbrowser.open(auth_url)
        server.timeout = 180
        server.handle_request()
        server.server_close()
        if result.get("state") != state or not result.get("code"):
            raise TikTokApiError(
                result.get("error_description") or result.get("error")
                or "TikTok-Anmeldung wurde nicht abgeschlossen."
            )
        return self._save_token(self._token_request({
            "client_key": self.config.client_key,
            "client_secret": self.config.client_secret,
            "code": result["code"], "grant_type": "authorization_code",
            "redirect_uri": self.config.redirect_uri, "code_verifier": verifier,
        }))

    def _read_token(self) -> dict[str, Any] | None:
        if not self.config.token_path.exists():
            return None
        return json.loads(self.config.token_path.read_text(encoding="utf-8"))

    def _save_token(self, token: dict[str, Any]) -> dict[str, Any]:
        if "access_token" not in token:
            raise TikTokApiError(self._error_text(token))
        token["expires_at"] = time.time() + int(token.get("expires_in", 86400))
        self.config.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")
        return token

    def _token_request(self, values: dict[str, str]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{API_ROOT}/oauth/token/", urllib.parse.urlencode(values).encode(),
            headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST",
        )
        return self._open_json(request)

    def _request_json(
        self, url: str, token: str, body: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        data = json.dumps(body).encode() if body is not None else None
        request = urllib.request.Request(
            url, data, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            method="POST" if body is not None else "GET",
        )
        return self._open_json(request)

    @staticmethod
    def _open_json(request: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception as exc:
            detail = getattr(exc, "read", lambda: b"")().decode("utf-8", "replace")
            raise TikTokApiError(f"TikTok API: {detail or exc}") from exc

    @classmethod
    def _raise_api_error(cls, response: dict[str, Any]) -> None:
        error = response.get("error", {})
        if error and error.get("code") not in (None, "ok"):
            raise TikTokApiError(cls._error_text(response))

    @staticmethod
    def _error_text(response: dict[str, Any]) -> str:
        error = response.get("error", response)
        return f"TikTok API: {error.get('code', 'Fehler')} · {error.get('message') or error.get('error_description', '')}"
