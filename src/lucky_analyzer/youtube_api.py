from __future__ import annotations

import json
import re
import secrets
import time
import urllib.parse
import urllib.request
import webbrowser
from datetime import date, datetime, timezone
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any

from .config import YouTubeConfig
from .models import YouTubeChannelMetrics, YouTubeVideoMetrics


SCOPES = (
    "https://www.googleapis.com/auth/youtube.readonly",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
)


class YouTubeApiError(RuntimeError):
    pass


class YouTubeClient:
    def __init__(self, config: YouTubeConfig):
        self.config = config
        raw = json.loads(config.oauth_client_path.read_text(encoding="utf-8"))
        client = raw.get("installed") or raw.get("web")
        if not client:
            raise YouTubeApiError("Die OAuth-JSON enthält keine Desktop-App-Konfiguration.")
        self.client_id = client["client_id"]
        self.client_secret = client.get("client_secret", "")
        self.auth_uri = client.get("auth_uri", "https://accounts.google.com/o/oauth2/auth")
        self.token_uri = client.get("token_uri", "https://oauth2.googleapis.com/token")

    def fetch(self) -> tuple[YouTubeChannelMetrics, list[YouTubeVideoMetrics]]:
        token = self._access_token()
        channel_data = self._get_json(
            "https://www.googleapis.com/youtube/v3/channels",
            token,
            part="snippet,statistics,contentDetails",
            mine="true",
        )
        if not channel_data.get("items"):
            raise YouTubeApiError("Für das angemeldete Google-Konto wurde kein YouTube-Kanal gefunden.")
        channel = channel_data["items"][0]
        uploads_id = channel["contentDetails"]["relatedPlaylists"]["uploads"]
        video_ids = self._upload_video_ids(uploads_id, token)
        videos = self._videos(video_ids, token)
        analytics = self._analytics(token, channel["id"])
        analytics_by_video = self._video_analytics(token, channel["id"])
        videos = [
            YouTubeVideoMetrics(
                **{**video.__dict__, **analytics_by_video.get(video.video_id, {})}
            )
            for video in videos
        ]
        stats = channel["statistics"]
        return YouTubeChannelMetrics(
            channel_id=channel["id"],
            title=channel["snippet"]["title"],
            subscribers=int(stats.get("subscriberCount", 0)),
            views=int(stats.get("viewCount", 0)),
            video_count=int(stats.get("videoCount", 0)),
            likes=sum(video.likes for video in videos),
            comments=sum(video.comments for video in videos),
            watch_minutes=analytics.get("watch_minutes"),
            average_view_duration=analytics.get("average_view_duration"),
            captured_at=datetime.now(timezone.utc),
        ), videos

    def _upload_video_ids(self, playlist_id: str, token: str) -> list[str]:
        ids: list[str] = []
        page_token = ""
        while True:
            data = self._get_json(
                "https://www.googleapis.com/youtube/v3/playlistItems", token,
                part="contentDetails", playlistId=playlist_id, maxResults="50",
                **({"pageToken": page_token} if page_token else {}),
            )
            ids.extend(item["contentDetails"]["videoId"] for item in data.get("items", []))
            page_token = data.get("nextPageToken", "")
            if not page_token:
                return ids

    def _videos(self, ids: list[str], token: str) -> list[YouTubeVideoMetrics]:
        result: list[YouTubeVideoMetrics] = []
        for start in range(0, len(ids), 50):
            data = self._get_json(
                "https://www.googleapis.com/youtube/v3/videos", token,
                part="snippet,statistics,contentDetails,status", id=",".join(ids[start:start + 50]),
            )
            for item in data.get("items", []):
                if item.get("status", {}).get("privacyStatus") != "public":
                    continue
                stats = item.get("statistics", {})
                result.append(YouTubeVideoMetrics(
                    video_id=item["id"], title=item["snippet"]["title"],
                    published_at=datetime.fromisoformat(item["snippet"]["publishedAt"].replace("Z", "+00:00")),
                    duration_seconds=self._duration_seconds(item["contentDetails"].get("duration", "PT0S")),
                    views=int(stats.get("viewCount", 0)), likes=int(stats.get("likeCount", 0)),
                    comments=int(stats.get("commentCount", 0)),
                ))
        return result

    def _analytics(self, token: str, channel_id: str) -> dict[str, Any]:
        data = self._get_json(
            "https://youtubeanalytics.googleapis.com/v2/reports", token,
            ids=f"channel=={channel_id}", startDate="2005-02-14", endDate=date.today().isoformat(),
            metrics="estimatedMinutesWatched,averageViewDuration",
        )
        row = (data.get("rows") or [[0, 0]])[0]
        return {"watch_minutes": int(row[0]), "average_view_duration": float(row[1])}

    def _video_analytics(self, token: str, channel_id: str) -> dict[str, dict[str, Any]]:
        result: dict[str, dict[str, Any]] = {}
        start_index = 1
        while True:
            data = self._get_json(
                "https://youtubeanalytics.googleapis.com/v2/reports", token,
                ids=f"channel=={channel_id}", startDate="2005-02-14", endDate=date.today().isoformat(),
                dimensions="video", metrics="estimatedMinutesWatched,averageViewDuration",
                sort="-estimatedMinutesWatched", maxResults="200", startIndex=str(start_index),
            )
            rows = data.get("rows") or []
            for row in rows:
                result[row[0]] = {"watch_minutes": int(row[1]), "average_view_duration": float(row[2])}
            if len(rows) < 200:
                return result
            start_index += 200

    def _access_token(self) -> str:
        token = self._read_token()
        if token and float(token.get("expires_at", 0)) > time.time() + 60:
            return token["access_token"]
        if token and token.get("refresh_token"):
            refreshed = self._token_request({
                "client_id": self.client_id, "client_secret": self.client_secret,
                "refresh_token": token["refresh_token"], "grant_type": "refresh_token",
            })
            refreshed["refresh_token"] = token["refresh_token"]
            return self._save_token(refreshed)["access_token"]
        return self._authorize()["access_token"]

    def _authorize(self) -> dict[str, Any]:
        state = secrets.token_urlsafe(24)
        result: dict[str, str] = {}

        class Handler(BaseHTTPRequestHandler):
            def do_GET(inner_self) -> None:
                query = urllib.parse.parse_qs(urllib.parse.urlparse(inner_self.path).query)
                result.update({key: values[0] for key, values in query.items()})
                body = "<h2>Anmeldung abgeschlossen</h2><p>Du kannst dieses Fenster schließen.</p>".encode()
                inner_self.send_response(200); inner_self.send_header("Content-Type", "text/html; charset=utf-8")
                inner_self.send_header("Content-Length", str(len(body))); inner_self.end_headers(); inner_self.wfile.write(body)
            def log_message(self, *_args: Any) -> None:
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        redirect_uri = f"http://127.0.0.1:{server.server_port}/"
        url = self.auth_uri + "?" + urllib.parse.urlencode({
            "client_id": self.client_id, "redirect_uri": redirect_uri, "response_type": "code",
            "scope": " ".join(SCOPES), "access_type": "offline", "prompt": "consent", "state": state,
        })
        webbrowser.open(url)
        server.timeout = 180
        server.handle_request(); server.server_close()
        if result.get("state") != state or "code" not in result:
            raise YouTubeApiError(result.get("error", "YouTube-Anmeldung wurde nicht abgeschlossen."))
        token = self._token_request({
            "client_id": self.client_id, "client_secret": self.client_secret, "code": result["code"],
            "grant_type": "authorization_code", "redirect_uri": redirect_uri,
        })
        return self._save_token(token)

    def _read_token(self) -> dict[str, Any] | None:
        if not self.config.token_path.exists():
            return None
        return json.loads(self.config.token_path.read_text(encoding="utf-8"))

    def _save_token(self, token: dict[str, Any]) -> dict[str, Any]:
        token["expires_at"] = time.time() + int(token.get("expires_in", 3600))
        self.config.token_path.parent.mkdir(parents=True, exist_ok=True)
        self.config.token_path.write_text(json.dumps(token, indent=2), encoding="utf-8")
        return token

    def _token_request(self, values: dict[str, str]) -> dict[str, Any]:
        request = urllib.request.Request(self.token_uri, urllib.parse.urlencode(values).encode(), method="POST")
        return self._open_json(request)

    def _get_json(self, url: str, token: str, **params: str) -> dict[str, Any]:
        request = urllib.request.Request(url + "?" + urllib.parse.urlencode(params), headers={"Authorization": f"Bearer {token}"})
        return self._open_json(request)

    @staticmethod
    def _open_json(request: urllib.request.Request) -> dict[str, Any]:
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except Exception as exc:
            detail = getattr(exc, "read", lambda: b"")().decode("utf-8", "replace")
            raise YouTubeApiError(f"YouTube API: {detail or exc}") from exc

    @staticmethod
    def _duration_seconds(value: str) -> int:
        match = re.fullmatch(r"P(?:(\d+)D)?T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", value)
        if not match:
            return 0
        days, hours, minutes, seconds = (int(part or 0) for part in match.groups())
        return days * 86400 + hours * 3600 + minutes * 60 + seconds
