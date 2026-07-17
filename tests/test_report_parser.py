from unittest import TestCase

from lucky_analyzer.apple_api import ReportPayload
from lucky_analyzer.report_parser import parse_reports


class ReportParserTests(TestCase):
    def test_download_and_install_reports_are_combined_by_date(self) -> None:
        downloads = (
            "Date\tDownload Type\tCounts\n"
            "2026-07-15\tFirst-time download\t10\n"
            "2026-07-15\tRedownload\t3\n"
            "2026-07-15\tManual update\t7\n"
        ).encode()
        installs = (
            "Date\tEvent\tCounts\n"
            "2026-07-15\tInstall\t8\n"
            "2026-07-15\tDelete\t2\n"
        ).encode()
        result = parse_reports(
            [
                ReportPayload("downloads", "Downloads", "2026-07-16", (downloads,)),
                ReportPayload("installs", "Installs", "2026-07-16", (installs,)),
            ]
        )
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].first_downloads, 10)
        self.assertEqual(result[0].total_downloads, 13)
        self.assertEqual(result[0].updates, 7)
        self.assertEqual(result[0].installations, 8)
        self.assertEqual(result[0].deletions, 2)

