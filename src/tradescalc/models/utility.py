"""
TradesCalc — Utility Reliability Models.

Pydantic v2 models for IEEE 1366 reliability indices,
major event day detection, and outage cost estimation.
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Reliability Index Calculations (SAIDI / SAIFI / CAIDI)
# ---------------------------------------------------------------------------
class OutageEvent(BaseModel):
    """A single outage event used for reliability index calculations."""

    customers_affected: int = Field(
        ...,
        gt=0,
        description="Number of customers who lost service during this event.",
        json_schema_extra={"examples": [450]},
    )
    duration_minutes: float = Field(
        ...,
        gt=0,
        description="Duration of the outage in minutes.",
        json_schema_extra={"examples": [120.0]},
    )
    event_date: str | None = Field(
        default=None,
        description="Date of the event (ISO-8601 string, e.g. '2024-07-15'). Optional metadata.",
        json_schema_extra={"examples": ["2024-07-15"]},
    )


class ReliabilityRequest(BaseModel):
    """Request body for calculating SAIDI, SAIFI, and CAIDI from outage data."""

    outage_events: list[OutageEvent] = Field(
        ...,
        min_length=1,
        description="List of outage events in the reporting period.",
    )
    total_customers_served: int = Field(
        ...,
        gt=0,
        description="Total number of customers served by the utility during the reporting period.",
        json_schema_extra={"examples": [15000]},
    )
    period_description: str | None = Field(
        default=None,
        description="Human-readable label for the period (e.g. 'Q2 2024', '2024 Annual').",
        json_schema_extra={"examples": ["Q2 2024"]},
    )


class ReliabilityResponse(BaseModel):
    """Calculated IEEE 1366 reliability indices."""

    saidi: float = Field(
        ...,
        description="System Average Interruption Duration Index — average outage minutes per customer served.",
    )
    saifi: float = Field(
        ...,
        description="SAIFI — average number of interruptions per customer served.",
    )
    caidi: float = Field(
        ...,
        description="CAIDI — average outage duration per affected customer (minutes).",
    )
    maifi: float | None = Field(
        default=None,
        description="Momentary Average Interruption Frequency Index (if momentary data supplied).",
    )
    total_customer_minutes: float = Field(
        ...,
        description="Sum of (customers_affected × duration_minutes) across all events.",
    )
    total_customer_interruptions: int = Field(
        ...,
        description="Sum of customers_affected across all events.",
    )
    period: str | None = Field(
        default=None,
        description="Period label echoed back from the request.",
    )


# ---------------------------------------------------------------------------
# Major Event Day Detection (IEEE 1366 — 2.5-beta method)
# ---------------------------------------------------------------------------
class MajorEventDayRequest(BaseModel):
    """Request body for IEEE 1366 Major Event Day threshold calculation."""

    daily_saidi_values: list[float] = Field(
        ...,
        min_length=2,
        description=(
            "Historical daily SAIDI values (in minutes) used to derive the "
            "log-normal threshold (TMED). At least 2 values required; 5+ years of "
            "daily data recommended per IEEE 1366."
        ),
    )
    daily_saidi: float | None = Field(
        default=None,
        description=(
            "The daily SAIDI value to test against the computed TMED threshold. "
            "If omitted, only the threshold is returned."
        ),
    )


class MajorEventDayResponse(BaseModel):
    """Result of the IEEE 1366 Major Event Day analysis."""

    threshold_tmed: float = Field(
        ...,
        description="Computed TMED threshold (minutes). Days exceeding this are classified as Major Event Days.",
    )
    is_major_event_day: bool | None = Field(
        default=None,
        description="Whether the provided daily_saidi exceeds the TMED threshold.",
    )
    daily_saidi: float | None = Field(
        default=None,
        description="The daily SAIDI value that was tested (echoed back).",
    )
    method: str = Field(
        default="IEEE 1366 2.5-beta log-normal",
        description="Statistical method used for threshold calculation.",
    )


# ---------------------------------------------------------------------------
# Outage Cost Estimation (DOE ICE simplified methodology)
# ---------------------------------------------------------------------------
class CustomerMix(BaseModel):
    """Percentage breakdown of customer classes (must sum to ≈ 100)."""

    residential_pct: float = Field(
        default=80.0,
        ge=0,
        le=100,
        description="Percentage of affected customers that are residential.",
    )
    commercial_pct: float = Field(
        default=15.0,
        ge=0,
        le=100,
        description="Percentage of affected customers that are commercial.",
    )
    industrial_pct: float = Field(
        default=5.0,
        ge=0,
        le=100,
        description="Percentage of affected customers that are industrial.",
    )


class OutageCostRequest(BaseModel):
    """Request body for estimating the economic cost of an outage."""

    customers_affected: int = Field(
        ...,
        gt=0,
        description="Number of customers affected by the outage.",
        json_schema_extra={"examples": [2000]},
    )
    duration_hours: float = Field(
        ...,
        gt=0,
        description="Duration of the outage in hours.",
        json_schema_extra={"examples": [4.0]},
    )
    customer_mix: CustomerMix = Field(
        default_factory=CustomerMix,
        description="Customer class breakdown. Defaults to 80% residential, 15% commercial, 5% industrial.",
    )


class CostBreakdown(BaseModel):
    """Cost breakdown by customer class."""

    residential_cost_usd: float = Field(..., description="Estimated cost from residential customers.")
    commercial_cost_usd: float = Field(..., description="Estimated cost from commercial customers.")
    industrial_cost_usd: float = Field(..., description="Estimated cost from industrial customers.")


class OutageCostResponse(BaseModel):
    """Estimated economic cost of an outage event."""

    estimated_cost_usd: float = Field(
        ...,
        description="Total estimated economic cost of the outage in USD.",
    )
    cost_per_customer: float = Field(
        ...,
        description="Average cost per affected customer in USD.",
    )
    cost_breakdown: CostBreakdown = Field(
        ...,
        description="Cost breakdown by customer class.",
    )
