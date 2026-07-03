"""
Unit tests for the Rate Trajectory service.
"""

import pytest
from src.core.trajectory import RateTrajectory


class TestRateTrajectory:
    def test_forecast_higher_than_current(self):
        forecast = RateTrajectory.calculate_forecast(current_rate=100.0)
        assert forecast.forecasted_rate > forecast.current_rate

    def test_forecast_with_claims_penalty(self):
        no_claims = RateTrajectory.calculate_forecast(current_rate=100.0, claims_count=0)
        with_claims = RateTrajectory.calculate_forecast(current_rate=100.0, claims_count=2)
        assert with_claims.forecasted_rate > no_claims.forecasted_rate

    def test_forecast_with_loyalty_penalty(self):
        new = RateTrajectory.calculate_forecast(current_rate=100.0, years_with_carrier=1)
        loyal = RateTrajectory.calculate_forecast(current_rate=100.0, years_with_carrier=5)
        assert loyal.forecasted_rate > new.forecasted_rate

    def test_recommendation_switch_when_peer_lower(self):
        forecast = RateTrajectory.calculate_forecast(
            current_rate=200.0,
            peer_avg_rate=160.0,
        )
        assert forecast.recommendation == "Switch"
        assert forecast.savings_amount > 0

    def test_recommendation_stay_when_peer_similar(self):
        forecast = RateTrajectory.calculate_forecast(
            current_rate=100.0,
            peer_avg_rate=99.0,
        )
        assert forecast.recommendation == "Stay"

    def test_confidence_decreases_with_claims(self):
        no_claims = RateTrajectory.calculate_forecast(current_rate=100.0, claims_count=0)
        many_claims = RateTrajectory.calculate_forecast(current_rate=100.0, claims_count=3)
        assert many_claims.confidence < no_claims.confidence

    def test_confidence_not_below_threshold(self):
        forecast = RateTrajectory.calculate_forecast(
            current_rate=100.0,
            claims_count=10,
            peer_avg_rate=0.0,
        )
        assert forecast.confidence >= 0.3

    def test_forecast_returns_all_fields(self):
        forecast = RateTrajectory.calculate_forecast(
            current_rate=150.0,
            claims_count=1,
            peer_avg_rate=140.0,
            years_with_carrier=2,
        )
        assert forecast.current_rate == 150.0
        assert forecast.forecasted_rate > 0
        assert forecast.peer_average > 0
        assert forecast.recommendation in ("Stay", "Switch")
        assert forecast.savings_amount >= 0
        assert 0 <= forecast.confidence <= 1