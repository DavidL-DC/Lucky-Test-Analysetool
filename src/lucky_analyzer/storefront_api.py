from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from .models import StorefrontRating


LOOKUP_URL = "https://itunes.apple.com/lookup"
DACH_STOREFRONTS = ("de", "at", "ch")


class StorefrontApiError(RuntimeError):
    """Der öffentliche Apple-Storefront-Lookup ist fehlgeschlagen."""


class StorefrontClient:
    def __init__(self, app_id: str, timeout: float = 20.0):
        self.app_id = app_id
        self.timeout = timeout

    def fetch_dach_ratings(self) -> list[StorefrontRating]:
        return [self.fetch_rating(territory) for territory in DACH_STOREFRONTS]

    def fetch_rating(self, territory: str) -> StorefrontRating:
        query = urllib.parse.urlencode(
            {"id": self.app_id, "country": territory, "entity": "software"}
        )
        request = urllib.request.Request(
            f"{LOOKUP_URL}?{query}",
            headers={"Accept": "application/json", "User-Agent": "LuckyAnalyzer/0.1"},
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            raise StorefrontApiError(
                f"Apple Lookup ({territory.upper()}) antwortete mit HTTP {exc.code}."
            ) from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            raise StorefrontApiError(
                f"Apple Lookup ({territory.upper()}) ist nicht erreichbar: {exc}"
            ) from exc

        results = payload.get("results", [])
        if payload.get("resultCount") != 1 or len(results) != 1:
            raise StorefrontApiError(
                f"Lucky Test wurde im Apple Store {territory.upper()} nicht eindeutig gefunden."
            )
        result = results[0]
        try:
            rating_count = int(result.get("userRatingCount", 0))
            average_rating = float(result.get("averageUserRating", 0.0))
        except (TypeError, ValueError) as exc:
            raise StorefrontApiError(
                f"Apple lieferte ungültige Bewertungsdaten für {territory.upper()}."
            ) from exc
        if rating_count < 0 or not 0.0 <= average_rating <= 5.0:
            raise StorefrontApiError(
                f"Apple lieferte ungültige Bewertungsdaten für {territory.upper()}."
            )
        return StorefrontRating(territory.upper(), average_rating, rating_count)

