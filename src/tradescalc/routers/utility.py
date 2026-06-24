"""
TradesCalc — Utility Reliability Router.

IEEE 1366 reliability indices, major event day detection,
outage cost estimation, and national benchmarks.
"""

import math

from fastapi import APIRouter, HTTPException

from tradescalc.models.utility import (
    CostBreakdown,
    MajorEventDayRequest,
    MajorEventDayResponse,
    OutageCostRequest,
    OutageCostResponse,
    ReliabilityRequest,
    ReliabilityResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# 1. POST /reliability — SAIDI, SAIFI, CAIDI
# ---------------------------------------------------------------------------
@router.post(
    "/reliability",
    response_model=ReliabilityResponse,
    summary="Calculate reliability indices (SAIDI, SAIFI, CAIDI)",
    description=(
        "Compute IEEE 1366 System Average Interruption Duration Index (SAIDI), "
        "System Average Interruption Frequency Index (SAIFI), and Customer "
        "Average Interruption Duration Index (CAIDI) from a list of outage events."
    ),
    operation_id="calculate_reliability_indices",
)
async def calculate_reliability(request: ReliabilityRequest) -> ReliabilityResponse:
    """Calculate SAIDI, SAIFI, and CAIDI from outage event data."""
    total_customer_minutes: float = sum(e.customers_affected * e.duration_minutes for e in request.outage_events)
    total_customer_interruptions: int = sum(e.customers_affected for e in request.outage_events)
    n = request.total_customers_served

    saidi = total_customer_minutes / n
    saifi = total_customer_interruptions / n

    if saifi == 0:
        raise HTTPException(
            status_code=400,
            detail="SAIFI is zero — no customer interruptions recorded. Cannot compute CAIDI.",
        )

    caidi = saidi / saifi

    return ReliabilityResponse(
        saidi=round(saidi, 4),
        saifi=round(saifi, 4),
        caidi=round(caidi, 4),
        maifi=None,
        total_customer_minutes=round(total_customer_minutes, 2),
        total_customer_interruptions=total_customer_interruptions,
        period=request.period_description,
    )


# ---------------------------------------------------------------------------
# 2. POST /major-event-day — IEEE 1366 2.5-beta method
# ---------------------------------------------------------------------------
@router.post(
    "/major-event-day",
    response_model=MajorEventDayResponse,
    summary="Determine IEEE 1366 Major Event Day threshold (TMED)",
    description=(
        "Apply the IEEE 1366 2.5-beta log-normal method to historical daily "
        "SAIDI values to compute the Major Event Day threshold (TMED). "
        "Optionally test a specific day's SAIDI against the threshold."
    ),
    operation_id="calculate_major_event_day",
)
async def calculate_major_event_day(request: MajorEventDayRequest) -> MajorEventDayResponse:
    """Calculate the TMED threshold using the IEEE 1366 2.5-beta method."""
    values = request.daily_saidi_values

    # Filter out zero/negative values (log undefined)
    positive_values = [v for v in values if v > 0]
    if len(positive_values) < 2:
        raise HTTPException(
            status_code=400,
            detail=(
                "At least 2 positive daily SAIDI values are required for log-normal "
                "analysis. Zero and negative values are excluded."
            ),
        )

    # Natural log transform
    ln_values = [math.log(v) for v in positive_values]

    # Mean (alpha) and standard deviation (beta) of the log values
    n = len(ln_values)
    alpha = sum(ln_values) / n
    variance = sum((x - alpha) ** 2 for x in ln_values) / (n - 1)
    beta = math.sqrt(variance)

    # TMED = exp(alpha + 2.5 * beta)
    tmed = math.exp(alpha + 2.5 * beta)

    # Optionally compare a specific day
    is_major: bool | None = None
    if request.daily_saidi is not None:
        is_major = request.daily_saidi > tmed

    return MajorEventDayResponse(
        threshold_tmed=round(tmed, 4),
        is_major_event_day=is_major,
        daily_saidi=request.daily_saidi,
        method="IEEE 1366 2.5-beta log-normal",
    )


# ---------------------------------------------------------------------------
# 3. POST /outage-cost — Simplified DOE ICE methodology
# ---------------------------------------------------------------------------
# DOE Interruption Cost Estimate (ICE) — simplified per-customer-hour rates
_COST_PER_CUSTOMER_HOUR = {
    "residential": 3.50,
    "commercial": 120.00,
    "industrial": 3000.00,
}


@router.post(
    "/outage-cost",
    response_model=OutageCostResponse,
    summary="Estimate economic cost of an outage (DOE ICE simplified)",
    description=(
        "Estimate the economic impact of a power outage using simplified "
        "DOE Interruption Cost Estimate rates. Costs are weighted by "
        "customer class mix (residential, commercial, industrial)."
    ),
    operation_id="estimate_outage_cost",
)
async def estimate_outage_cost(request: OutageCostRequest) -> OutageCostResponse:
    """Estimate outage cost weighted by customer class mix."""
    mix = request.customer_mix
    total_pct = mix.residential_pct + mix.commercial_pct + mix.industrial_pct

    if not (99.0 <= total_pct <= 101.0):
        raise HTTPException(
            status_code=400,
            detail=f"Customer mix percentages must sum to ~100%. Got {total_pct:.1f}%.",
        )

    n = request.customers_affected
    hours = request.duration_hours

    res_customers = n * (mix.residential_pct / 100.0)
    com_customers = n * (mix.commercial_pct / 100.0)
    ind_customers = n * (mix.industrial_pct / 100.0)

    res_cost = res_customers * hours * _COST_PER_CUSTOMER_HOUR["residential"]
    com_cost = com_customers * hours * _COST_PER_CUSTOMER_HOUR["commercial"]
    ind_cost = ind_customers * hours * _COST_PER_CUSTOMER_HOUR["industrial"]

    total_cost = res_cost + com_cost + ind_cost

    return OutageCostResponse(
        estimated_cost_usd=round(total_cost, 2),
        cost_per_customer=round(total_cost / n, 2),
        cost_breakdown=CostBreakdown(
            residential_cost_usd=round(res_cost, 2),
            commercial_cost_usd=round(com_cost, 2),
            industrial_cost_usd=round(ind_cost, 2),
        ),
    )


# ---------------------------------------------------------------------------
# 4. GET /benchmark — National average reliability benchmarks
# ---------------------------------------------------------------------------
@router.get(
    "/benchmark",
    summary="National average reliability benchmarks",
    description=(
        "Return national average reliability indices published by IEEE/EIA. "
        "Includes averages with and without Major Event Days, and breakdowns "
        "by utility type (cooperative, investor-owned, municipal)."
    ),
    operation_id="get_reliability_benchmarks",
)
async def get_benchmarks() -> dict:
    """Return national average reliability benchmarks."""
    return {
        "source": "IEEE 1366 / EIA-861 annual summaries (composite averages)",
        "note": (
            "Values are approximate national averages compiled from EIA-861 data. "
            "Actual benchmarks vary by year, region, and reporting methodology."
        ),
        "with_major_event_days": {
            "saidi_minutes": 475.0,
            "saifi": 1.5,
            "caidi_minutes": 316.7,
        },
        "without_major_event_days": {
            "saidi_minutes": 130.0,
            "saifi": 1.0,
            "caidi_minutes": 130.0,
        },
        "by_utility_type": {
            "cooperative": {
                "saidi_minutes": 300.0,
                "saifi": 1.7,
                "caidi_minutes": 176.5,
                "note": "Co-ops typically serve rural, long-line territories with higher exposure.",
            },
            "investor_owned": {
                "saidi_minutes": 120.0,
                "saifi": 1.0,
                "caidi_minutes": 120.0,
                "note": "IOUs generally have shorter feeders and more redundancy.",
            },
            "municipal": {
                "saidi_minutes": 90.0,
                "saifi": 0.8,
                "caidi_minutes": 112.5,
                "note": "Municipals often serve compact, urban service territories.",
            },
        },
    }


# ---------------------------------------------------------------------------
# 5. GET /info — Module description
# ---------------------------------------------------------------------------
@router.get(
    "/info",
    summary="Utility module information",
    description="Returns a description of the Utility Reliability module and its available endpoints.",
    operation_id="get_utility_info",
)
async def get_info() -> dict:
    """Return module description and available endpoints."""
    return {
        "module": "Utility — Reliability Indices",
        "description": (
            "IEEE 1366 utility reliability calculations including SAIDI, SAIFI, "
            "CAIDI, Major Event Day detection (2.5-beta method), outage cost "
            "estimation (DOE ICE methodology), and national benchmark comparisons."
        ),
        "standards": ["IEEE 1366-2022", "EIA-861", "DOE ICE Calculator"],
        "endpoints": [
            {
                "path": "/v1/utility/reliability",
                "method": "POST",
                "summary": "Calculate SAIDI, SAIFI, CAIDI from outage events.",
            },
            {
                "path": "/v1/utility/major-event-day",
                "method": "POST",
                "summary": "IEEE 1366 Major Event Day threshold (TMED) via 2.5-beta method.",
            },
            {
                "path": "/v1/utility/outage-cost",
                "method": "POST",
                "summary": "Estimate outage economic cost using DOE ICE methodology.",
            },
            {
                "path": "/v1/utility/benchmark",
                "method": "GET",
                "summary": "National average reliability benchmarks by utility type.",
            },
            {
                "path": "/v1/utility/info",
                "method": "GET",
                "summary": "This endpoint — module description and endpoint listing.",
            },
        ],
    }
