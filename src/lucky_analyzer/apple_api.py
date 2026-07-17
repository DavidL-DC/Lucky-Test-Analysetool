from __future__ import annotations

import base64
import gzip
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.asymmetric.utils import decode_dss_signature

from .config import AppStoreConfig


API_BASE_URL = "https://api.appstoreconnect.apple.com"
TARGET_REPORTS = {
    "App Store Downloads": "downloads",
    "App Store Installations and Deletions": "installs",
}


class AppStoreApiError(RuntimeError):
    """Ein Aufruf der App Store Connect API ist fehlgeschlagen."""


def _base64url(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def create_jwt(config: AppStoreConfig, now: int | None = None) -> str:
    issued_at = int(time.time() if now is None else now)
    header = {"alg": "ES256", "kid": config.key_id, "typ": "JWT"}
    payload = {
        "iss": config.issuer_id,
        "iat": issued_at,
        "exp": issued_at + 15 * 60,
        "aud": "appstoreconnect-v1",
    }
    encoded_header = _base64url(
        json.dumps(header, separators=(",", ":")).encode("utf-8")
    )
    encoded_payload = _base64url(
        json.dumps(payload, separators=(",", ":")).encode("utf-8")
    )
    signing_input = f"{encoded_header}.{encoded_payload}".encode("ascii")

    key_data = config.private_key_path.read_bytes()
    private_key = serialization.load_pem_private_key(key_data, password=None)
    if not isinstance(private_key, ec.EllipticCurvePrivateKey):
        raise AppStoreApiError("Die P8-Datei enthält keinen EC-Privatschlüssel.")
    der_signature = private_key.sign(signing_input, ec.ECDSA(hashes.SHA256()))
    r, s = decode_dss_signature(der_signature)
    signature = r.to_bytes(32, "big") + s.to_bytes(32, "big")
    return f"{encoded_header}.{encoded_payload}.{_base64url(signature)}"


@dataclass(frozen=True)
class ReportPayload:
    kind: str
    report_name: str
    processing_date: str
    contents: tuple[bytes, ...]


class AppStoreClient:
    def __init__(self, config: AppStoreConfig, timeout: float = 30.0):
        self.config = config
        self.timeout = timeout

    def fetch_latest_reports(self) -> list[ReportPayload]:
        request_id = self._find_or_create_report_request()
        reports = self._get_all(
            f"/v1/analyticsReportRequests/{request_id}/reports"
        )
        candidates: dict[str, list[tuple[str, dict[str, Any]]]] = {
            kind: [] for kind in TARGET_REPORTS.values()
        }
        for report in reports:
            name = str(report.get("attributes", {}).get("name", ""))
            kind = next(
                (value for prefix, value in TARGET_REPORTS.items() if name.startswith(prefix)),
                None,
            )
            if kind is not None:
                candidates[kind].append((name, report))

        selected: list[ReportPayload] = []
        for kind, available in candidates.items():
            if not available:
                continue
            name, report = min(
                available,
                key=lambda item: (
                    "standard" not in item[0].casefold(),
                    "detailed" in item[0].casefold(),
                    item[0],
                ),
            )
            payload = self._latest_report_payload(report, kind, name)
            if payload is not None:
                selected.append(payload)

        found_kinds = {item.kind for item in selected}
        missing = sorted(set(TARGET_REPORTS.values()) - found_kinds)
        if missing:
            raise AppStoreApiError(
                "Apple hat noch nicht alle benötigten Analytics-Berichte bereitgestellt "
                f"({', '.join(missing)}). Neue Report-Anfragen benötigen häufig 1–2 Tage."
            )
        return selected

    def _find_or_create_report_request(self) -> str:
        requests = self._get_all(
            "/v1/analyticsReportRequests",
            {"filter[app]": self.config.app_id},
        )
        for item in requests:
            if item.get("attributes", {}).get("accessType") == "ONGOING":
                return str(item["id"])

        body = {
            "data": {
                "type": "analyticsReportRequests",
                "attributes": {"accessType": "ONGOING"},
                "relationships": {
                    "app": {"data": {"type": "apps", "id": self.config.app_id}}
                },
            }
        }
        created = self._request_json(
            "/v1/analyticsReportRequests", method="POST", body=body
        )
        return str(created["data"]["id"])

    def _latest_report_payload(
        self, report: dict[str, Any], kind: str, name: str
    ) -> ReportPayload | None:
        report_id = str(report["id"])
        instances = self._get_all(
            f"/v1/analyticsReports/{report_id}/instances",
            {"filter[granularity]": "DAILY"},
        )
        if not instances:
            return None
        latest = max(
            instances,
            key=lambda item: str(item.get("attributes", {}).get("processingDate", "")),
        )
        processing_date = str(latest.get("attributes", {}).get("processingDate", ""))
        segments = self._get_all(
            f"/v1/analyticsReportInstances/{latest['id']}/segments"
        )
        contents: list[bytes] = []
        for segment in segments:
            url = segment.get("attributes", {}).get("url")
            if url:
                contents.append(self._download_report(str(url)))
        return ReportPayload(kind, name, processing_date, tuple(contents))

    def _get_all(
        self, path: str, query: dict[str, str] | None = None
    ) -> list[dict[str, Any]]:
        response = self._request_json(path, query=query)
        items = list(response.get("data", []))
        next_url = response.get("links", {}).get("next")
        while next_url:
            response = self._request_json(str(next_url))
            items.extend(response.get("data", []))
            next_url = response.get("links", {}).get("next")
        return items

    def _request_json(
        self,
        path_or_url: str,
        *,
        method: str = "GET",
        query: dict[str, str] | None = None,
        body: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        url = (
            path_or_url
            if path_or_url.startswith("http")
            else API_BASE_URL + path_or_url
        )
        if query:
            url += ("&" if "?" in url else "?") + urllib.parse.urlencode(query)
        encoded_body = json.dumps(body).encode("utf-8") if body is not None else None
        request = urllib.request.Request(
            url,
            data=encoded_body,
            method=method,
            headers={
                "Authorization": f"Bearer {create_jwt(self.config)}",
                "Accept": "application/json",
                "Content-Type": "application/json",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            details = exc.read().decode("utf-8", errors="replace")[:500]
            raise AppStoreApiError(
                f"App Store Connect antwortete mit HTTP {exc.code}: {details}"
            ) from exc
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AppStoreApiError(f"App Store Connect ist nicht erreichbar: {exc}") from exc

    def _download_report(self, url: str) -> bytes:
        try:
            with urllib.request.urlopen(url, timeout=self.timeout) as response:
                content = response.read()
        except (urllib.error.URLError, TimeoutError) as exc:
            raise AppStoreApiError(f"Analytics-Bericht konnte nicht geladen werden: {exc}") from exc
        try:
            return gzip.decompress(content)
        except gzip.BadGzipFile:
            return content
