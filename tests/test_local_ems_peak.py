# SPDX-License-Identifier: GPL-3.0-or-later
"""Unit tests for the calculation core, no HA installation required."""
import sys
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "custom_components" / "local_ems"))
from peak import Sample, calculate_peak, quarter_start_utc  # noqa: E402


class PeakTests(unittest.TestCase):
    def test_example_4_minutes(self):
        start = datetime(2026, 11, 2, 11, 0, tzinfo=UTC)
        values = [
            Sample(start, 100.0),
            Sample(start + timedelta(minutes=2), 100.5),
            Sample(start + timedelta(minutes=3), 100.75),
            Sample(start + timedelta(minutes=4), 101.0),
        ]
        r = calculate_peak(values, start + timedelta(minutes=4), start, 9, 10, timedelta(seconds=180))
        self.assertTrue(r.valid)
        self.assertEqual(r.committed_kw, 4)
        self.assertEqual(r.forecast_kw, 15)
        self.assertEqual(r.minutes_to_limit, 6)

    def test_missing_start_is_not_zero(self):
        start = datetime(2026, 11, 2, 11, 0, tzinfo=UTC)
        values = [Sample(start + timedelta(minutes=1), 100.0)]
        r = calculate_peak(values, start + timedelta(minutes=2), start, 9, 10, timedelta(seconds=180))
        self.assertFalse(r.valid)
        self.assertEqual(r.quality, "missing_boundary")

    def test_interpolated_boundary(self):
        start = datetime(2026, 11, 2, 11, 0, tzinfo=UTC)
        values = [
            Sample(start - timedelta(seconds=10), 100.0),
            Sample(start + timedelta(seconds=10), 100.1),
            Sample(start + timedelta(minutes=4), 101.05),
        ]
        r = calculate_peak(values, start + timedelta(minutes=4), start, 9, 10, timedelta(seconds=180))
        self.assertTrue(r.valid)
        self.assertEqual(r.quality, "estimated_boundary")
        self.assertAlmostEqual(r.energy_kwh, 1.0, places=3)

    def test_reject_meter_reset(self):
        start = datetime(2026, 11, 2, 11, 0, tzinfo=UTC)
        values = [Sample(start, 100), Sample(start + timedelta(minutes=1), 99)]
        r = calculate_peak(values, start + timedelta(minutes=1), start, 9, 10, timedelta(seconds=180))
        self.assertEqual(r.quality, "counter_reset")

    def test_stale(self):
        start = datetime(2026, 11, 2, 11, 0, tzinfo=UTC)
        values = [Sample(start, 100)]
        r = calculate_peak(values, start + timedelta(minutes=5), start, 9, 10, timedelta(seconds=180))
        self.assertEqual(r.quality, "stale")

    def test_no_threshold_before_end(self):
        start = datetime(2026, 11, 2, 11, 0, tzinfo=UTC)
        values = [Sample(start, 100), Sample(start + timedelta(minutes=5), 100.1)]
        r = calculate_peak(values, start + timedelta(minutes=5), start, 9, 10, timedelta(seconds=180))
        self.assertTrue(r.valid)
        self.assertIsNone(r.minutes_to_limit)

    def test_dst_uses_local_clock_quarters(self):
        # The second 02:32 in Vienna, after the DST fallback.
        second_0232 = datetime(2026, 10, 25, 1, 32, tzinfo=UTC)
        self.assertEqual(
            quarter_start_utc(second_0232, "Europe/Vienna"),
            datetime(2026, 10, 25, 1, 30, tzinfo=UTC),
        )


if __name__ == "__main__":
    unittest.main()
