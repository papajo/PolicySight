"""
Unit tests for the Lapse Bridge service.
"""

import pytest
from datetime import datetime, timedelta
from src.core.lapse import CoverageGapBridge, CoverageStatus


class TestCoverageGapBridge:
    def test_check_coverage_active(self):
        renewal = datetime.utcnow() + timedelta(days=30)
        status = CoverageGapBridge.check_coverage_status(
            renewal_date=renewal,
            has_active_policy=True,
        )
        assert status.is_covered
        assert 29 <= status.days_until_lapse <= 30  # Allow for timing delta

    def test_check_coverage_no_policy(self):
        status = CoverageGapBridge.check_coverage_status(
            renewal_date=None,
            has_active_policy=False,
        )
        assert not status.is_covered
        assert status.days_until_lapse == 0

    def test_should_trigger_when_uncovered(self):
        status = CoverageStatus(user_id=1, is_covered=False)
        assert CoverageGapBridge.should_trigger_bridge(status)

    def test_should_trigger_near_lapse(self):
        status = CoverageStatus(user_id=1, is_covered=True, days_until_lapse=3)
        assert CoverageGapBridge.should_trigger_bridge(status)

    def test_should_not_trigger_when_covered(self):
        status = CoverageStatus(user_id=1, is_covered=True, days_until_lapse=30)
        assert not CoverageGapBridge.should_trigger_bridge(status)

    def test_should_not_trigger_with_active_bridge(self):
        status = CoverageStatus(
            user_id=1, is_covered=True, days_until_lapse=3, bridge_active=True
        )
        assert not CoverageGapBridge.should_trigger_bridge(status)

    def test_calculate_bridge_cost(self):
        cost = CoverageGapBridge.calculate_bridge_cost(days=30)
        assert cost["days"] == 30
        assert cost["daily_rate"] == 5.0
        assert cost["total_cost"] == 150.0

    def test_generate_lapse_alert_uncovered(self):
        status = CoverageStatus(user_id=1, is_covered=False)
        alert = CoverageGapBridge.generate_lapse_alert(status)
        assert "Coverage Lapse Detected" in alert

    def test_generate_lapse_alert_imminent(self):
        status = CoverageStatus(user_id=1, is_covered=True, days_until_lapse=5)
        alert = CoverageGapBridge.generate_lapse_alert(status)
        assert "Coverage at Risk" in alert
        assert "5" in alert

    def test_generate_lapse_alert_reminder(self):
        status = CoverageStatus(user_id=1, is_covered=True, days_until_lapse=15)
        alert = CoverageGapBridge.generate_lapse_alert(status)
        assert "Renewal Reminder" in alert

    def test_generate_lapse_alert_ok(self):
        status = CoverageStatus(user_id=1, is_covered=True, days_until_lapse=90)
        alert = CoverageGapBridge.generate_lapse_alert(status)
        assert "Coverage is active" in alert