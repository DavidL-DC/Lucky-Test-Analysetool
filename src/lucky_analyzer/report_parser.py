from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import date
from typing import Iterable

from .apple_api import ReportPayload
from .models import DailyMetrics


class ReportFormatError(ValueError):
    """Ein Apple-Bericht hat nicht das erwartete Format."""


def parse_reports(reports: Iterable[ReportPayload]) -> list[DailyMetrics]:
    values: dict[date, dict[str, int]] = defaultdict(
        lambda: {
            "first_downloads": 0,
            "redownloads": 0,
            "updates": 0,
            "installations": 0,
            "deletions": 0,
        }
    )
    for report in reports:
        for content in report.contents:
            _parse_content(content, report.kind, values)

    return [
        DailyMetrics(metric_date=metric_date, **metrics)
        for metric_date, metrics in sorted(values.items())
    ]


def _parse_content(
    content: bytes, kind: str, values: dict[date, dict[str, int]]
) -> None:
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text), delimiter="\t")
    required = {"Date", "Counts"}
    if not reader.fieldnames or not required.issubset(reader.fieldnames):
        raise ReportFormatError(
            f"Pflichtspalten fehlen: {', '.join(sorted(required))}"
        )

    for line_number, row in enumerate(reader, start=2):
        try:
            metric_date = date.fromisoformat(row["Date"])
            count = int(row["Counts"])
        except (TypeError, ValueError) as exc:
            raise ReportFormatError(
                f"Ungültiges Datum oder Counts in Berichtszeile {line_number}."
            ) from exc

        if kind == "downloads":
            download_type = (row.get("Download Type") or "").strip().casefold()
            if download_type == "first-time download":
                values[metric_date]["first_downloads"] += count
            elif download_type == "redownload":
                values[metric_date]["redownloads"] += count
            elif "update" in download_type:
                values[metric_date]["updates"] += count
        elif kind == "installs":
            event = (row.get("Event") or "").strip().casefold()
            if event == "install":
                values[metric_date]["installations"] += count
            elif event in {"delete", "deletion"}:
                values[metric_date]["deletions"] += count

