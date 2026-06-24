"""
TradesCalc — Fire Protection Engineering Router.

Hydrant flow testing, friction loss, pump discharge pressure,
needed fire flow, ISO grading, and NERIS incident type codes.
"""

from fastapi import APIRouter, HTTPException

from tradescalc.models.fire import (
    HydrantFlowRequest,
    HydrantFlowResponse,
    FrictionLossRequest,
    FrictionLossResponse,
    PumpPressureRequest,
    PumpPressureResponse,
    PressureBreakdown,
    NeededFireFlowRequest,
    NeededFireFlowResponse,
    ISOGradingResponse,
    ISOGradingCategory,
    NERISCodeResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Construction class factors for Needed Fire Flow (ISO)
# ---------------------------------------------------------------------------
_CONSTRUCTION_FACTORS: dict[int, float] = {
    1: 1.5,   # Frame
    2: 1.0,   # Joisted Masonry
    3: 1.0,   # Heavy Timber
    4: 0.8,   # Non-Combustible
    5: 0.8,   # Modified Fire Resistive
    6: 0.6,   # Fire Resistive
}


# ---------------------------------------------------------------------------
# 1. POST /hydrant-flow — Available fire flow at 20 psi residual
# ---------------------------------------------------------------------------
@router.post(
    "/hydrant-flow",
    response_model=HydrantFlowResponse,
    summary="Calculate available fire flow from hydrant flow test",
    description=(
        "Estimate the available fire flow at 20 psi residual pressure using "
        "standard hydrant flow test data. Formula: "
        "Available GPM = Flow_test × ((Static − 20) / (Static − Residual))^0.54"
    ),
    operation_id="calculate_hydrant_flow",
)
async def calculate_hydrant_flow(request: HydrantFlowRequest) -> HydrantFlowResponse:
    """Calculate available fire flow at 20 psi residual."""
    sp = request.static_pressure_psi
    rp = request.residual_pressure_psi
    flow = request.flow_at_residual_gpm

    if rp >= sp:
        raise HTTPException(
            status_code=400,
            detail="Residual pressure must be less than static pressure.",
        )
    if sp <= 20:
        raise HTTPException(
            status_code=400,
            detail="Static pressure must exceed 20 psi to calculate flow at 20 psi residual.",
        )

    pressure_ratio = (sp - 20.0) / (sp - rp)
    coefficient = pressure_ratio ** 0.54
    available_gpm = flow * coefficient

    return HydrantFlowResponse(
        available_flow_at_20psi_gpm=round(available_gpm, 1),
        flow_coefficient=round(coefficient, 4),
        static_psi=sp,
        residual_psi=rp,
    )


# ---------------------------------------------------------------------------
# 2. POST /friction-loss — Hazen-Williams friction loss
# ---------------------------------------------------------------------------
@router.post(
    "/friction-loss",
    response_model=FrictionLossResponse,
    summary="Calculate Hazen-Williams friction loss",
    description=(
        "Compute friction loss through a hose or pipe using the Hazen-Williams "
        "formula: FL = (4.52 × Q^1.85) / (C^1.85 × d^4.87) per foot of pipe."
    ),
    operation_id="calculate_friction_loss",
)
async def calculate_friction_loss(request: FrictionLossRequest) -> FrictionLossResponse:
    """Calculate friction loss using Hazen-Williams formula."""
    q = request.flow_gpm
    c = request.c_factor
    d = request.hose_diameter_inches
    length = request.length_ft

    # FL per foot = (4.52 * Q^1.85) / (C^1.85 * d^4.87)
    fl_per_foot = (4.52 * (q ** 1.85)) / ((c ** 1.85) * (d ** 4.87))
    fl_total = fl_per_foot * length
    fl_per_100 = fl_per_foot * 100.0

    return FrictionLossResponse(
        friction_loss_psi=round(fl_total, 2),
        friction_loss_per_100ft=round(fl_per_100, 2),
        formula_used="Hazen-Williams",
    )


# ---------------------------------------------------------------------------
# 3. POST /pump-pressure — Engine pump discharge pressure
# ---------------------------------------------------------------------------
@router.post(
    "/pump-pressure",
    response_model=PumpPressureResponse,
    summary="Calculate engine pump discharge pressure (PDP)",
    description=(
        "Compute the required engine pump discharge pressure: "
        "PDP = Nozzle Pressure + Friction Loss + Elevation + Appliance Loss. "
        "Elevation converts at 0.434 psi per foot of head."
    ),
    operation_id="calculate_pump_pressure",
)
async def calculate_pump_pressure(request: PumpPressureRequest) -> PumpPressureResponse:
    """Calculate engine pump discharge pressure."""
    elevation_pressure = request.elevation_ft * 0.434

    pdp = (
        request.nozzle_pressure_psi
        + request.friction_loss_psi
        + elevation_pressure
        + request.appliance_loss_psi
    )

    return PumpPressureResponse(
        engine_pressure_psi=round(pdp, 2),
        breakdown=PressureBreakdown(
            nozzle_pressure_psi=request.nozzle_pressure_psi,
            friction_loss_psi=request.friction_loss_psi,
            elevation_pressure_psi=round(elevation_pressure, 2),
            appliance_loss_psi=request.appliance_loss_psi,
        ),
    )


# ---------------------------------------------------------------------------
# 4. POST /needed-fire-flow — ISO/NFPA needed fire flow (simplified)
# ---------------------------------------------------------------------------
@router.post(
    "/needed-fire-flow",
    response_model=NeededFireFlowResponse,
    summary="Calculate Needed Fire Flow (ISO/NFPA simplified)",
    description=(
        "Compute Needed Fire Flow using the ISO formula: "
        "NFF = 18 × F × √Area, adjusted for occupancy and exposure factors. "
        "Result is capped between 500 and 12,000 GPM. Duration is assigned "
        "based on final NFF value."
    ),
    operation_id="calculate_needed_fire_flow",
)
async def calculate_needed_fire_flow(request: NeededFireFlowRequest) -> NeededFireFlowResponse:
    """Calculate Needed Fire Flow per ISO/NFPA methodology."""
    f = _CONSTRUCTION_FACTORS.get(request.construction_class)
    if f is None:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid construction class: {request.construction_class}. Must be 1-6.",
        )

    import math

    # Base NFF = 18 × F × sqrt(Area)
    base_flow = 18.0 * f * math.sqrt(request.area_sqft)

    # Apply occupancy and exposure adjustment factors
    adjustment = 1.0
    if request.occupancy_factor is not None:
        adjustment += request.occupancy_factor
    if request.exposure_factor is not None:
        adjustment += request.exposure_factor

    adjusted_flow = base_flow * adjustment

    # Cap between 500 and 12,000 GPM
    nff = max(500.0, min(12000.0, adjusted_flow))

    # Round to nearest 250 GPM (ISO standard rounding)
    nff = round(nff / 250.0) * 250.0

    # Duration based on final NFF
    if nff < 2500:
        duration = 2
    elif nff <= 3500:
        duration = 3
    else:
        duration = 4

    return NeededFireFlowResponse(
        needed_fire_flow_gpm=nff,
        base_flow_gpm=round(base_flow, 1),
        adjusted_flow_gpm=round(adjusted_flow, 1),
        duration_hours=duration,
    )


# ---------------------------------------------------------------------------
# 5. GET /iso-grading — ISO FSRS grading structure and weights
# ---------------------------------------------------------------------------
@router.get(
    "/iso-grading",
    response_model=ISOGradingResponse,
    summary="ISO Fire Suppression Rating Schedule (FSRS) grading structure",
    description=(
        "Return the ISO FSRS grading categories and their percentage weights. "
        "The standard schedule allocates 50% to Fire Department, 40% to Water "
        "Supply, 10% to Emergency Communications, plus a 5.5% Community Risk "
        "Reduction bonus — totaling 105.5 possible points."
    ),
    operation_id="get_iso_grading",
)
async def get_iso_grading() -> ISOGradingResponse:
    """Return ISO FSRS grading structure."""
    categories = [
        ISOGradingCategory(
            category="Fire Department",
            max_points=50.0,
            percentage_of_total=50.0,
        ),
        ISOGradingCategory(
            category="Water Supply",
            max_points=40.0,
            percentage_of_total=40.0,
        ),
        ISOGradingCategory(
            category="Emergency Communications",
            max_points=10.0,
            percentage_of_total=10.0,
        ),
        ISOGradingCategory(
            category="Community Risk Reduction (Bonus)",
            max_points=5.5,
            percentage_of_total=5.5,
        ),
    ]
    return ISOGradingResponse(
        categories=categories,
        total_possible=105.5,
    )


# ---------------------------------------------------------------------------
# 6. GET /neris-codes — NERIS incident type codes
# ---------------------------------------------------------------------------
_NERIS_CODES: list[dict[str, str]] = [
    {"code": "111", "description": "Structure Fire", "category": "Fire"},
    {"code": "112", "description": "Fires in Structure — Not a Building", "category": "Fire"},
    {"code": "113", "description": "Cooking Fire (Confined)", "category": "Fire"},
    {"code": "120", "description": "Mobile Property Fire", "category": "Fire"},
    {"code": "131", "description": "Passenger Vehicle Fire", "category": "Fire"},
    {"code": "140", "description": "Brush / Grass / Wildland Fire", "category": "Fire"},
    {"code": "300", "description": "Rescue & Emergency Medical Service", "category": "EMS"},
    {"code": "311", "description": "Medical Assist", "category": "EMS"},
    {"code": "322", "description": "Motor Vehicle Accident (with injuries)", "category": "EMS"},
    {"code": "400", "description": "Hazardous Condition / Hazmat", "category": "Hazmat"},
    {"code": "500", "description": "Service Call", "category": "Service Call"},
    {"code": "510", "description": "Lock-out", "category": "Service Call"},
    {"code": "550", "description": "Public Assist / Other", "category": "Service Call"},
    {"code": "600", "description": "Good Intent Call", "category": "Good Intent"},
    {"code": "700", "description": "False Alarm & False Call", "category": "False Alarm"},
    {"code": "710", "description": "Malicious False Alarm", "category": "False Alarm"},
    {"code": "730", "description": "System Malfunction", "category": "False Alarm"},
    {"code": "733", "description": "Smoke Detector Malfunction", "category": "False Alarm"},
]


@router.get(
    "/neris-codes",
    response_model=list[NERISCodeResponse],
    summary="NERIS incident type codes",
    description=(
        "Return a list of common NERIS (National Emergency Response Information System) "
        "incident type codes with descriptions and category groupings."
    ),
    operation_id="get_neris_codes",
)
async def get_neris_codes() -> list[NERISCodeResponse]:
    """Return NERIS incident type codes."""
    return [NERISCodeResponse(**code) for code in _NERIS_CODES]


# ---------------------------------------------------------------------------
# 7. GET /info — Module description
# ---------------------------------------------------------------------------
@router.get(
    "/info",
    summary="Fire Protection module information",
    description="Returns a description of the Fire Protection Engineering module and its available endpoints.",
    operation_id="get_fire_info",
)
async def get_info() -> dict:
    """Return module description and available endpoints."""
    return {
        "module": "Fire — Protection Engineering",
        "description": (
            "Fire protection engineering calculations including hydrant flow testing, "
            "Hazen-Williams friction loss, engine pump discharge pressure, ISO Needed "
            "Fire Flow, FSRS grading structure, and NERIS incident type codes."
        ),
        "standards": ["NFPA 291", "NFPA 1142", "ISO FSRS", "NERIS/NFIRS"],
        "endpoints": [
            {
                "path": "/v1/fire/hydrant-flow",
                "method": "POST",
                "summary": "Calculate available fire flow from hydrant test data.",
            },
            {
                "path": "/v1/fire/friction-loss",
                "method": "POST",
                "summary": "Hazen-Williams friction loss calculation.",
            },
            {
                "path": "/v1/fire/pump-pressure",
                "method": "POST",
                "summary": "Engine pump discharge pressure (PDP).",
            },
            {
                "path": "/v1/fire/needed-fire-flow",
                "method": "POST",
                "summary": "ISO/NFPA Needed Fire Flow calculation.",
            },
            {
                "path": "/v1/fire/iso-grading",
                "method": "GET",
                "summary": "ISO FSRS grading structure and weights.",
            },
            {
                "path": "/v1/fire/neris-codes",
                "method": "GET",
                "summary": "NERIS incident type codes with descriptions.",
            },
            {
                "path": "/v1/fire/info",
                "method": "GET",
                "summary": "This endpoint — module description and endpoint listing.",
            },
        ],
    }
