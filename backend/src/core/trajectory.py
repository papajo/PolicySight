"""
Rate Trajectory Service
Handles premium forecasting and peer market comparison logic.
"""

from pydantic import BaseModel
from typing import Optional


class RateForecast(BaseModel):
    """Structured representation of a rate forecast."""
    current_rate: float
    forecasted_rate: float
    peer_average: float
    recommendation: str  # "Stay" or "Switch"
    savings_amount: float
    confidence: float


class RateTrajectory:
    """
    Core service for predicting future insurance premiums.
    Compares user risk profile against anonymized peer market data
    to determine if the user should stay or switch carriers.
    """

    # Average annual rate adjustments by state (placeholder data)
    MARKET_ADJUSTMENT_FACTOR = 1.08  # 8% average annual increase
    SWITCH_SAVINGS_THRESHOLD = 0.10  # 10% savings triggers "Switch" recommendation

    @staticmethod
    def calculate_forecast(
        current_rate: float,
        claims_count: int = 0,
        peer_avg_rate: float = 0.0,
        years_with_carrier: int = 1,
    ) -> RateForecast:
        """
        Calculate the forecasted rate based on:
        - Current rate
        - Claims history (penalty factor)
        - Peer market average
        - Loyalty factor (carriers often increase rates for long-term customers)
        """
        # Base market adjustment
        forecast = current_rate * RateTrajectory.MARKET_ADJUSTMENT_FACTOR

        # Claims penalty (each claim adds ~5% penalty)
        claims_penalty = 1.0 + (claims_count * 0.05)
        forecast *= claims_penalty

        # Loyalty penalty (carriers tend to increase rates for loyal customers)
        loyalty_penalty = 1.0 + (max(0, years_with_carrier - 1) * 0.02)
        forecast *= loyalty_penalty

        # Determine recommendation
        peer_avg = peer_avg_rate if peer_avg_rate > 0 else current_rate * 0.95
        savings = current_rate - peer_avg
        savings_pct = savings / current_rate if current_rate > 0 else 0

        if savings_pct > RateTrajectory.SWITCH_SAVINGS_THRESHOLD and peer_avg > 0:
            recommendation = "Switch"
        else:
            recommendation = "Stay"

        # Confidence decreases with more uncertainty factors
        confidence = 0.85
        if claims_count > 0:
            confidence -= 0.05 * claims_count
        if peer_avg == 0:
            confidence -= 0.20
        confidence = max(0.3, min(0.95, confidence))

        return RateForecast(
            current_rate=current_rate,
            forecasted_rate=round(forecast, 2),
            peer_average=round(peer_avg, 2),
            recommendation=recommendation,
            savings_amount=round(abs(savings), 2),
            confidence=round(confidence, 2),
        )

    @staticmethod
    def generate_llm_prompt(
        current_rate: float,
        claims_history: list[dict],
        peer_data: dict,
    ) -> str:
        """Generate the LLM prompt for rate trajectory analysis."""
        claims_str = "\n".join(
            [f"- Claim #{c.get('id', 'N/A')}: {c.get('status', 'unknown')}" for c in claims_history]
        ) or "No claims history."

        return f"""You are an expert auto insurance rate analyst. 
Analyze the following policyholder's rate trajectory.

Current Monthly Premium: ${current_rate:,.2f}

Claims History:
{claims_str}

Peer Market Data:
{peer_data}

Provide:
1. Forecasted rate for next renewal
2. Whether the user should stay or switch carriers
3. Estimated savings from switching
4. Confidence level in the prediction
5. Key factors driving the rate change"""