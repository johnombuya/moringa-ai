"""Dashboard HTTP tests — no live uvicorn, no OpenAI."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

ROOT = Path(__file__).resolve().parent.parent
DASHBOARD = ROOT / "dashboard"
for path in (ROOT, DASHBOARD):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import app as dashboard_app
from fastapi.testclient import TestClient


class DashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        dashboard_app.EXCEPTION_COUNT = 0
        self.client = TestClient(dashboard_app.app)

    def test_index_returns_200_with_four_sections(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        body = response.text
        for heading in ("System Health", "Feature Quality", "Drift Vector", "Budget"):
            with self.subTest(heading=heading):
                self.assertIn(heading, body)

    def test_metrics_exposes_afyaplus_gauges(self) -> None:
        response = self.client.get("/metrics")
        self.assertEqual(response.status_code, 200)
        text = response.text
        for gauge in (
            "afyaplus_health_up",
            "afyaplus_daily_spend_usd",
            "afyaplus_judge_overall",
        ):
            with self.subTest(gauge=gauge):
                self.assertIn(gauge, text)

    def test_index_empty_artifacts_still_200(self) -> None:
        with TemporaryDirectory() as tmp:
            missing = Path(tmp) / "does_not_exist.csv"
            with patch.multiple(
                dashboard_app,
                QUALITY_GATE_CSV=missing,
                DRIFT_TREND_CSV=missing,
                DRIFT_ALERTS_JSON=missing,
                DAILY_COSTS_CSV=missing,
                SAVINGS_CSV=missing,
                EVAL_RESULTS_CSV=missing,
            ):
                dashboard_app.EXCEPTION_COUNT = 0
                response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertIn("DOWN", response.text)


if __name__ == "__main__":
    unittest.main()
