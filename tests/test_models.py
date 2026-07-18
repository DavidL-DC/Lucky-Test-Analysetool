from unittest import TestCase

from lucky_analyzer.models import AnalysisPeriod


class AnalysisPeriodTests(TestCase):
    def test_labels_and_days_are_stable_for_the_period_selector(self) -> None:
        self.assertEqual(
            [(period.label, period.days) for period in AnalysisPeriod],
            [
                ("7 Tage", 7),
                ("30 Tage", 30),
                ("90 Tage", 90),
                ("Gesamt", None),
            ],
        )

    def test_period_can_be_selected_by_its_visible_label(self) -> None:
        self.assertIs(
            AnalysisPeriod.from_label("30 Tage"),
            AnalysisPeriod.THIRTY_DAYS,
        )
