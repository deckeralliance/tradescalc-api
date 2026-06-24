"""
Electrical Router — NEC-Compliant Calculation Endpoints.

All endpoints reference NEC 2023 tables and formulas.
Wire sizing, voltage drop, conduit fill, ampacity, derating,
breaker sizing, service entrance, box fill, and transformer sizing.

For estimation and planning purposes only.
Verify all calculations against the official NEC codebook.
"""

import math
from typing import Optional

from fastapi import APIRouter, HTTPException

from tradescalc.models.electrical import (
    AmpacityDeratedRequest,
    AmpacityDeratedResponse,
    AmpacityRequest,
    AmpacityResponse,
    BoxFillRequest,
    BoxFillResponse,
    BreakerSizeRequest,
    BreakerSizeResponse,
    ConduitFillRequest,
    ConduitFillResponse,
    NECTableResponse,
    ServiceEntranceRequest,
    ServiceEntranceResponse,
    SuggestedBox,
    TransformerSizingRequest,
    TransformerSizingResponse,
    VoltageDropRequest,
    VoltageDropResponse,
    WireSizeRequest,
    WireSizeResponse,
)
from tradescalc.services.nec_data import NECDataStore

router = APIRouter()


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
STANDARD_BREAKER_SIZES: list[int] = [
    15, 20, 25, 30, 35, 40, 45, 50, 60, 70, 80, 90,
    100, 110, 125, 150, 175, 200, 225, 250, 300, 350,
    400, 450, 500, 600,
]

STANDARD_TRANSFORMER_KVA: list[float] = [
    3, 5, 7.5, 10, 15, 25, 37.5, 50, 75, 100,
    150, 167, 200, 250, 300, 500, 750, 1000,
]

# NEC 314.16(B) — Volume allowance per conductor in cubic inches
BOX_FILL_VOLUMES: dict[str, float] = {
    "14": 2.00,
    "12": 2.25,
    "10": 2.50,
    "8": 3.00,
    "6": 5.00,
}

# Standard box sizes for suggestions (type, volume in³)
STANDARD_BOX_SIZES: list[tuple[str, float]] = [
    ("4x1-1/4 square", 18.0),
    ("4x1-1/2 square", 21.0),
    ("4x2-1/8 square", 30.3),
    ("4-11/16x1-1/2 square", 29.5),
    ("4-11/16x2-1/8 square", 42.0),
    ("3x2x2 device box", 10.0),
    ("3x2x2-1/2 device box", 12.5),
    ("3x2x2-3/4 device box", 14.0),
    ("3x2x3-1/2 device box", 18.0),
]

# Temperature correction factors for 75°C-rated conductors — NEC 310.15(B)(1)
# Keyed by (lower_bound_c, upper_bound_c): correction_factor
TEMP_CORRECTION_75C: list[tuple[int, int, float]] = [
    (10, 15, 1.20),
    (16, 20, 1.15),
    (21, 25, 1.04),
    (26, 30, 1.00),
    (31, 35, 0.94),
    (36, 40, 0.87),
    (41, 45, 0.82),
    (46, 50, 0.75),
    (51, 55, 0.67),
    (56, 60, 0.58),
]

# Temperature correction factors for 60°C-rated conductors
TEMP_CORRECTION_60C: list[tuple[int, int, float]] = [
    (10, 15, 1.29),
    (16, 20, 1.22),
    (21, 25, 1.15),
    (26, 30, 1.00),
    (31, 35, 0.91),
    (36, 40, 0.82),
    (41, 45, 0.71),
    (46, 50, 0.58),
    (51, 55, 0.41),
]

# Temperature correction factors for 90°C-rated conductors
TEMP_CORRECTION_90C: list[tuple[int, int, float]] = [
    (10, 15, 1.15),
    (16, 20, 1.12),
    (21, 25, 1.08),
    (26, 30, 1.00),
    (31, 35, 0.96),
    (36, 40, 0.91),
    (41, 45, 0.87),
    (46, 50, 0.82),
    (51, 55, 0.76),
    (56, 60, 0.71),
    (61, 65, 0.65),
    (66, 70, 0.58),
    (71, 75, 0.50),
    (76, 80, 0.41),
]

# Bundling adjustment factors — NEC 310.15(C)(1)
ADJUSTMENT_FACTORS: list[tuple[int, int, float]] = [
    (1, 3, 1.00),
    (4, 6, 0.80),
    (7, 9, 0.70),
    (10, 20, 0.50),
    (21, 30, 0.45),
    (31, 40, 0.40),
    (41, 999, 0.35),
]

# Rooftop temperature adders — NEC 310.15(B)(3)(c)
# (lower_mm, upper_mm, adder_celsius)
ROOFTOP_ADDERS_MM: list[tuple[float, float, float]] = [
    (0, 13, 33.0),
    (13, 90, 22.0),
    (90, 300, 17.0),
    (300, 900, 14.0),
]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def _get_temp_correction_factor(ambient_c: float, temp_rating: str) -> float:
    """Get temperature correction factor based on ambient temp and rating."""
    table = {
        "60": TEMP_CORRECTION_60C,
        "75": TEMP_CORRECTION_75C,
        "90": TEMP_CORRECTION_90C,
    }.get(temp_rating, TEMP_CORRECTION_75C)

    for lower, upper, factor in table:
        if lower <= ambient_c <= upper:
            return factor

    # Outside defined range — extrapolate conservatively
    if ambient_c < table[0][0]:
        return table[0][2]  # Use highest correction factor
    return 0.0  # Too hot — conductor cannot be used


def _get_adjustment_factor(num_conductors: int) -> float:
    """Get bundling adjustment factor per NEC 310.15(C)(1)."""
    for lower, upper, factor in ADJUSTMENT_FACTORS:
        if lower <= num_conductors <= upper:
            return factor
    return 0.35  # 41+ conductors


def _get_rooftop_adder(distance_inches: Optional[float]) -> float:
    """Get rooftop temperature adder in °C based on distance above roof."""
    if distance_inches is None:
        return 0.0
    distance_mm = distance_inches * 25.4
    for lower_mm, upper_mm, adder in ROOFTOP_ADDERS_MM:
        if lower_mm <= distance_mm < upper_mm:
            return adder
    if distance_mm >= 900:
        return 0.0  # Above 900mm, no adder needed
    return 33.0  # Default to worst case


def _calculate_voltage_drop(
    load_amps: float,
    distance_ft: float,
    resistance_per_1000ft: float,
    voltage: float,
    phase: str,
) -> tuple[float, float]:
    """Calculate voltage drop in volts and as a percentage.

    Single-phase: Vd = (2 × R × I × D) / 1000
    Three-phase:  Vd = (√3 × R × I × D) / 1000

    Args:
        load_amps: Load current in amperes.
        distance_ft: One-way conductor length in feet.
        resistance_per_1000ft: DC resistance in ohms per 1000 ft.
        voltage: System voltage.
        phase: 'single' or 'three'.

    Returns:
        Tuple of (drop_volts, drop_percent).
    """
    if phase == "three":
        multiplier = math.sqrt(3)
    else:
        multiplier = 2.0

    drop_volts = (multiplier * resistance_per_1000ft * load_amps * distance_ft) / 1000.0
    drop_percent = (drop_volts / voltage) * 100.0
    return round(drop_volts, 2), round(drop_percent, 2)


def _next_standard_breaker(amps: float) -> int:
    """Find the next standard breaker size >= given amps."""
    for size in STANDARD_BREAKER_SIZES:
        if size >= amps:
            return size
    return STANDARD_BREAKER_SIZES[-1]


def _next_standard_transformer_kva(min_kva: float) -> float:
    """Find the next standard transformer kVA rating >= min_kva."""
    for size in STANDARD_TRANSFORMER_KVA:
        if size >= min_kva:
            return size
    return STANDARD_TRANSFORMER_KVA[-1]


# ---------------------------------------------------------------------------
# 1. POST /ampacity — NEC Table 310.16 Lookup
# ---------------------------------------------------------------------------
@router.post(
    "/ampacity",
    response_model=AmpacityResponse,
    operation_id="lookup_ampacity",
    summary="Lookup conductor ampacity",
    description=(
        "Returns the allowable ampacity for a conductor from NEC 2023 Table 310.16. "
        "Based on not more than 3 current-carrying conductors in a raceway, cable, "
        "or directly buried, at an ambient temperature of 30°C (86°F)."
    ),
)
async def lookup_ampacity(request: AmpacityRequest) -> AmpacityResponse:
    """Look up ampacity from NEC Table 310.16."""
    ampacity = NECDataStore.get_ampacity(
        wire_size=request.wire_size,
        material=request.material,
        temp_rating=request.temp_rating,
    )
    if ampacity is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No ampacity data found for {request.material} "
                f"{request.wire_size} AWG/kcmil at {request.temp_rating}°C. "
                f"Check wire size and material. Valid sizes: 14-1000 for copper, "
                f"12-1000 for aluminum."
            ),
        )
    return AmpacityResponse(
        wire_size=request.wire_size,
        material=request.material,
        temp_rating=request.temp_rating,
        ampacity=ampacity,
    )


# ---------------------------------------------------------------------------
# 2. POST /wire-size — Minimum Wire Size for a Load
# ---------------------------------------------------------------------------
@router.post(
    "/wire-size",
    response_model=WireSizeResponse,
    operation_id="calculate_wire_size",
    summary="Calculate minimum wire size",
    description=(
        "Finds the smallest NEC-compliant conductor that satisfies both the "
        "ampacity requirement (Table 310.16) and the 3% voltage drop recommendation "
        "(NEC 210.19(A) Informational Note No. 4). Iterates through standard wire "
        "sizes from smallest to largest."
    ),
)
async def calculate_wire_size(request: WireSizeRequest) -> WireSizeResponse:
    """Calculate minimum wire size for a given load, distance, and voltage."""
    wire_sizes = NECDataStore.get_standard_wire_sizes()
    if not wire_sizes:
        raise HTTPException(
            status_code=500,
            detail="NEC wire size data not loaded. Contact support.",
        )

    best_size: Optional[str] = None
    best_ampacity: int = 0
    best_vd_volts: float = 0.0
    best_vd_percent: float = 0.0
    best_passes_3pct: bool = False

    for size in wire_sizes:
        # Check ampacity
        ampacity = NECDataStore.get_ampacity(
            wire_size=size,
            material=request.material,
            temp_rating=request.temp_rating,
        )
        if ampacity is None or ampacity < request.load_amps:
            continue

        # Check voltage drop
        resistance = NECDataStore.get_conductor_resistance(
            wire_size=size, material=request.material
        )
        if resistance is None:
            continue

        vd_volts, vd_percent = _calculate_voltage_drop(
            load_amps=request.load_amps,
            distance_ft=request.distance_ft,
            resistance_per_1000ft=resistance,
            voltage=request.voltage,
            phase=request.phase,
        )

        if vd_percent <= 3.0:
            # Found a wire that passes both ampacity AND voltage drop
            return WireSizeResponse(
                recommended_size=size,
                ampacity=ampacity,
                voltage_drop_percent=vd_percent,
                voltage_drop_volts=vd_volts,
                passes_3_percent_rule=True,
                load_amps=request.load_amps,
                distance_ft=request.distance_ft,
                voltage=request.voltage,
                phase=request.phase,
                material=request.material,
            )

        # Track the first size that meets ampacity (even if VD fails)
        if best_size is None:
            best_size = size
            best_ampacity = ampacity
            best_vd_volts = vd_volts
            best_vd_percent = vd_percent
            best_passes_3pct = vd_percent <= 3.0

    # If we found a wire that meets ampacity but not VD, return it with a warning
    if best_size is not None:
        return WireSizeResponse(
            recommended_size=best_size,
            ampacity=best_ampacity,
            voltage_drop_percent=best_vd_percent,
            voltage_drop_volts=best_vd_volts,
            passes_3_percent_rule=best_passes_3pct,
            load_amps=request.load_amps,
            distance_ft=request.distance_ft,
            voltage=request.voltage,
            phase=request.phase,
            material=request.material,
        )

    raise HTTPException(
        status_code=400,
        detail=(
            f"No suitable wire size found for {request.load_amps}A "
            f"{request.material} at {request.temp_rating}°C. "
            f"Load may exceed maximum conductor capacity in NEC Table 310.16."
        ),
    )


# ---------------------------------------------------------------------------
# 3. POST /voltage-drop — Voltage Drop Calculation
# ---------------------------------------------------------------------------
@router.post(
    "/voltage-drop",
    response_model=VoltageDropResponse,
    operation_id="calculate_voltage_drop",
    summary="Calculate voltage drop",
    description=(
        "Calculates voltage drop for a given conductor using "
        "Vd = (2 × R × I × D) / 1000 for single-phase, and "
        "Vd = (√3 × R × I × D) / 1000 for three-phase. "
        "Resistance values from NEC Chapter 9, Table 8 (DC at 75°C)."
    ),
)
async def calculate_voltage_drop(
    request: VoltageDropRequest,
) -> VoltageDropResponse:
    """Calculate voltage drop for a specified conductor and load."""
    resistance = NECDataStore.get_conductor_resistance(
        wire_size=request.wire_size, material=request.material
    )
    if resistance is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No resistance data found for {request.material} "
                f"{request.wire_size} AWG/kcmil. "
                f"Check wire size and material."
            ),
        )

    drop_volts, drop_percent = _calculate_voltage_drop(
        load_amps=request.load_amps,
        distance_ft=request.distance_ft,
        resistance_per_1000ft=resistance,
        voltage=request.voltage,
        phase=request.phase,
    )

    return VoltageDropResponse(
        drop_volts=drop_volts,
        drop_percent=drop_percent,
        passes_3_percent_rule=drop_percent <= 3.0,
        passes_5_percent_rule=drop_percent <= 5.0,
        wire_size=request.wire_size,
        load_amps=request.load_amps,
        distance_ft=request.distance_ft,
        voltage=request.voltage,
        phase=request.phase,
        material=request.material,
        resistance_per_1000ft=resistance,
    )


# ---------------------------------------------------------------------------
# 4. POST /conduit-fill — Conduit Fill Calculation
# ---------------------------------------------------------------------------
@router.post(
    "/conduit-fill",
    response_model=ConduitFillResponse,
    operation_id="calculate_conduit_fill",
    summary="Calculate conduit fill",
    description=(
        "Determines the minimum conduit trade size based on total conductor "
        "cross-sectional area and NEC Chapter 9, Table 1 fill percentage rules. "
        "Conductor areas are for THHN/THWN-2 insulation (Chapter 9, Table 5)."
    ),
)
async def calculate_conduit_fill(
    request: ConduitFillRequest,
) -> ConduitFillResponse:
    """Calculate minimum conduit size for a set of conductors."""
    # Sum total conductor area and count
    total_area = 0.0
    total_count = 0

    for conductor in request.conductors:
        area = NECDataStore.get_conductor_area(conductor.wire_size)
        if area is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No conductor area data for size {conductor.wire_size}. "
                    f"Valid sizes: 14, 12, 10, 8, 6, 4, 3, 2, 1, 1/0-4/0, 250-1000."
                ),
            )
        total_area += area * conductor.count
        total_count += conductor.count

    # Get fill percentage based on number of conductors
    max_fill_fraction = NECDataStore.get_fill_percentage(total_count)
    max_fill_pct = max_fill_fraction * 100.0

    # Find smallest conduit that fits
    conduit_sizes = NECDataStore.get_standard_conduit_sizes()
    for conduit_size in conduit_sizes:
        conduit_area = NECDataStore.get_conduit_area(
            conduit_size=conduit_size, conduit_type=request.conduit_type
        )
        if conduit_area is None:
            continue

        max_fill_area = conduit_area * max_fill_fraction
        if total_area <= max_fill_area:
            actual_fill_pct = (total_area / conduit_area) * 100.0
            return ConduitFillResponse(
                min_conduit_size=conduit_size,
                fill_percent=round(actual_fill_pct, 1),
                fill_area_in2=round(total_area, 4),
                max_fill_area_in2=round(max_fill_area, 4),
                conduit_area_in2=conduit_area,
                max_fill_percent=round(max_fill_pct, 1),
                total_conductors=total_count,
                conduit_type=request.conduit_type,
            )

    raise HTTPException(
        status_code=400,
        detail=(
            f"No standard conduit size can accommodate {total_count} conductors "
            f"with a total area of {total_area:.4f} in². "
            f"Consider splitting into parallel conduit runs."
        ),
    )


# ---------------------------------------------------------------------------
# 5. POST /ampacity-derated — Derated Ampacity per NEC 310.15
# ---------------------------------------------------------------------------
@router.post(
    "/ampacity-derated",
    response_model=AmpacityDeratedResponse,
    operation_id="calculate_derated_ampacity",
    summary="Calculate derated ampacity",
    description=(
        "Applies temperature correction and bundling adjustment factors "
        "to the base Table 310.16 ampacity per NEC 310.15. Optionally "
        "includes rooftop temperature adder per 310.15(B)(3)(c)."
    ),
)
async def calculate_derated_ampacity(
    request: AmpacityDeratedRequest,
) -> AmpacityDeratedResponse:
    """Calculate derated ampacity with temperature and bundling corrections."""
    # Base ampacity
    base_ampacity = NECDataStore.get_ampacity(
        wire_size=request.wire_size,
        material=request.material,
        temp_rating=request.temp_rating,
    )
    if base_ampacity is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No ampacity data found for {request.material} "
                f"{request.wire_size} AWG/kcmil at {request.temp_rating}°C."
            ),
        )

    # Rooftop adder
    rooftop_adder = _get_rooftop_adder(request.rooftop_distance_inches)
    effective_ambient = request.ambient_temp_c + rooftop_adder

    # Temperature correction factor
    temp_factor = _get_temp_correction_factor(effective_ambient, request.temp_rating)

    # Bundling adjustment factor
    adj_factor = _get_adjustment_factor(request.num_current_carrying)

    # Combined derating
    combined = round(temp_factor * adj_factor, 4)
    derated = round(base_ampacity * combined, 1)

    return AmpacityDeratedResponse(
        base_ampacity=base_ampacity,
        temp_correction_factor=temp_factor,
        adjustment_factor=adj_factor,
        combined_derating_factor=combined,
        derated_ampacity=derated,
        effective_ambient_temp_c=effective_ambient,
        rooftop_adder_c=rooftop_adder,
        wire_size=request.wire_size,
        material=request.material,
        temp_rating=request.temp_rating,
    )


# ---------------------------------------------------------------------------
# 6. POST /breaker-size — Breaker Sizing per NEC 240
# ---------------------------------------------------------------------------
@router.post(
    "/breaker-size",
    response_model=BreakerSizeResponse,
    operation_id="calculate_breaker_size",
    summary="Calculate breaker size",
    description=(
        "Determines the minimum standard breaker size for a given load. "
        "Applies 125% continuous load factor per NEC 210.20(A) when the "
        "load is continuous (3+ hours). Rounds up to the next standard "
        "breaker size per NEC 240.6(A)."
    ),
)
async def calculate_breaker_size(
    request: BreakerSizeRequest,
) -> BreakerSizeResponse:
    """Calculate minimum breaker size for a load."""
    factor = 1.25 if request.continuous else 1.0
    min_amps = request.load_amps * factor
    standard_amps = _next_standard_breaker(min_amps)

    return BreakerSizeResponse(
        min_breaker_amps=round(min_amps, 2),
        standard_breaker_amps=standard_amps,
        continuous_load_factor=factor,
        load_amps=request.load_amps,
        continuous=request.continuous,
    )


# ---------------------------------------------------------------------------
# 7. POST /service-entrance — Service Entrance Sizing per Article 230
# ---------------------------------------------------------------------------
@router.post(
    "/service-entrance",
    response_model=ServiceEntranceResponse,
    operation_id="calculate_service_entrance",
    summary="Size service entrance",
    description=(
        "Determines minimum service entrance conductor size, conduit size, "
        "and main breaker rating per NEC Article 230. Uses 75°C column of "
        "Table 310.16 for service conductor sizing."
    ),
)
async def calculate_service_entrance(
    request: ServiceEntranceRequest,
) -> ServiceEntranceResponse:
    """Size service entrance conductors, conduit, and main breaker."""
    wire_sizes = NECDataStore.get_standard_wire_sizes()

    # Find minimum conductor — must have ampacity >= total_load_amps
    selected_size: Optional[str] = None
    selected_ampacity: int = 0

    for size in wire_sizes:
        ampacity = NECDataStore.get_ampacity(
            wire_size=size, material=request.material, temp_rating="75"
        )
        if ampacity is not None and ampacity >= request.total_load_amps:
            selected_size = size
            selected_ampacity = ampacity
            break

    if selected_size is None:
        raise HTTPException(
            status_code=400,
            detail=(
                f"No single conductor in Table 310.16 can handle "
                f"{request.total_load_amps}A for {request.material}. "
                f"Parallel conductors may be required."
            ),
        )

    # Size conduit for service entrance (minimum: 3 conductors for single-phase,
    # 4 for three-phase, plus 1 ground — we'll use 4 conductors for single-phase
    # as a conservative estimate: 2 hots + 1 neutral + 1 ground)
    if request.phase == "three":
        num_conductors = 4  # 3 phases + ground (neutral may be separate)
    else:
        num_conductors = 3  # 2 hots + neutral (ground can be in conduit or separate)

    conductor_area = NECDataStore.get_conductor_area(selected_size)
    if conductor_area is None:
        raise HTTPException(
            status_code=400,
            detail=f"No conductor area data for size {selected_size}.",
        )

    total_area = conductor_area * num_conductors
    fill_fraction = NECDataStore.get_fill_percentage(num_conductors)

    conduit_sizes = NECDataStore.get_standard_conduit_sizes()
    selected_conduit: str = conduit_sizes[-1]  # Default to largest

    for conduit_size in conduit_sizes:
        conduit_area_val = NECDataStore.get_conduit_area(
            conduit_size=conduit_size, conduit_type="pvc"  # PVC common for service
        )
        if conduit_area_val is not None and total_area <= conduit_area_val * fill_fraction:
            selected_conduit = conduit_size
            break

    # Main breaker size
    main_breaker = _next_standard_breaker(request.total_load_amps)

    return ServiceEntranceResponse(
        min_wire_size=selected_size,
        wire_ampacity=selected_ampacity,
        min_conduit_size=selected_conduit,
        main_breaker_amps=main_breaker,
        total_load_amps=request.total_load_amps,
        voltage=request.voltage,
        phase=request.phase,
        material=request.material,
    )


# ---------------------------------------------------------------------------
# 8. POST /motor-load — Placeholder (v1.1)
# ---------------------------------------------------------------------------
@router.post(
    "/motor-load",
    operation_id="calculate_motor_load",
    summary="Calculate motor branch circuit (coming soon)",
    description=(
        "Motor branch circuit sizing per NEC Article 430. "
        "This endpoint is planned for v1.1 and is not yet available."
    ),
    status_code=501,
)
async def calculate_motor_load() -> dict:
    """Placeholder for motor load calculations — coming in v1.1."""
    raise HTTPException(
        status_code=501,
        detail={
            "message": "Motor load calculations are coming in v1.1.",
            "nec_reference": "NEC 2023 Article 430",
            "status": "planned",
            "eta": "v1.1",
        },
    )


# ---------------------------------------------------------------------------
# 9. POST /demand-load — Placeholder (v1.1)
# ---------------------------------------------------------------------------
@router.post(
    "/demand-load",
    operation_id="calculate_demand_load",
    summary="Calculate demand load (coming soon)",
    description=(
        "Demand load calculation per NEC Article 220. "
        "This endpoint is planned for v1.1 and is not yet available."
    ),
    status_code=501,
)
async def calculate_demand_load() -> dict:
    """Placeholder for demand load calculations — coming in v1.1."""
    raise HTTPException(
        status_code=501,
        detail={
            "message": "Demand load calculations are coming in v1.1.",
            "nec_reference": "NEC 2023 Article 220",
            "status": "planned",
            "eta": "v1.1",
        },
    )


# ---------------------------------------------------------------------------
# 10. POST /box-fill — Box Fill Calculation per NEC 314.16
# ---------------------------------------------------------------------------
@router.post(
    "/box-fill",
    response_model=BoxFillResponse,
    operation_id="calculate_box_fill",
    summary="Calculate box fill",
    description=(
        "Calculates minimum outlet/junction box volume per NEC 314.16. "
        "Accounts for conductors, device yokes, internal cable clamps, "
        "and equipment grounding conductors."
    ),
)
async def calculate_box_fill(request: BoxFillRequest) -> BoxFillResponse:
    """Calculate minimum box fill volume per NEC 314.16."""
    # Calculate conductor volume
    conductor_volume = 0.0
    largest_conductor_volume = 0.0

    for conductor in request.conductors:
        vol = BOX_FILL_VOLUMES.get(conductor.wire_size)
        if vol is None:
            raise HTTPException(
                status_code=400,
                detail=(
                    f"Box fill volumes only available for sizes 14, 12, 10, 8, 6 AWG. "
                    f"Got: {conductor.wire_size}. Larger conductors typically use "
                    f"pull boxes per NEC 314.28."
                ),
            )
        conductor_volume += vol * conductor.count
        if vol > largest_conductor_volume:
            largest_conductor_volume = vol

    # Device yokes: each counts as 2× largest conductor volume
    device_volume = request.devices * 2 * largest_conductor_volume

    # Internal cable clamps: all count as 1× largest conductor volume (total)
    clamp_volume = largest_conductor_volume if request.clamps > 0 else 0.0

    # Equipment grounding conductors: all count as 1× largest conductor volume (total)
    ground_volume = largest_conductor_volume if request.grounds > 0 else 0.0

    total_volume = conductor_volume + device_volume + clamp_volume + ground_volume
    total_volume = round(total_volume, 2)

    # Suggest standard box sizes that meet the requirement
    suggestions = [
        SuggestedBox(box_type=name, volume_in3=vol)
        for name, vol in sorted(STANDARD_BOX_SIZES, key=lambda x: x[1])
        if vol >= total_volume
    ]

    return BoxFillResponse(
        min_box_volume_in3=total_volume,
        conductor_volume_in3=round(conductor_volume, 2),
        device_volume_in3=round(device_volume, 2),
        clamp_volume_in3=round(clamp_volume, 2),
        ground_volume_in3=round(ground_volume, 2),
        suggested_box_sizes=suggestions,
    )


# ---------------------------------------------------------------------------
# 11. POST /transformer-sizing — Transformer Sizing
# ---------------------------------------------------------------------------
@router.post(
    "/transformer-sizing",
    response_model=TransformerSizingResponse,
    operation_id="calculate_transformer_size",
    summary="Size a transformer",
    description=(
        "Determines the minimum standard kVA transformer rating for a "
        "given load in VA. Calculates full-load amps on both primary "
        "and secondary sides. Standard sizes per NEC Article 450."
    ),
)
async def calculate_transformer_size(
    request: TransformerSizingRequest,
) -> TransformerSizingResponse:
    """Calculate minimum transformer size for a given load."""
    min_kva = request.load_va / 1000.0
    standard_kva = _next_standard_transformer_kva(min_kva)

    # Full-load amps: FLA = (kVA × 1000) / voltage
    primary_fla = round((standard_kva * 1000.0) / request.voltage_primary, 2)
    secondary_fla = round((standard_kva * 1000.0) / request.voltage_secondary, 2)

    return TransformerSizingResponse(
        min_kva=round(min_kva, 2),
        standard_kva=standard_kva,
        load_va=request.load_va,
        voltage_primary=request.voltage_primary,
        voltage_secondary=request.voltage_secondary,
        primary_fla=primary_fla,
        secondary_fla=secondary_fla,
    )


# ---------------------------------------------------------------------------
# 12. GET /nec-table/{table_id} — Raw NEC Table Data
# ---------------------------------------------------------------------------
TABLE_TITLES: dict[str, str] = {
    "310.16": "Ampacities of Insulated Conductors (Not More Than 3 Current-Carrying Conductors)",
    "ch9-conductor-area": "Chapter 9 Table 5 — Conductor Area (THHN/THWN-2)",
    "ch9-conduit-area": "Chapter 9 Table 4 — Conduit Internal Area (EMT, PVC, Rigid)",
    "ch9-resistance": "Chapter 9 Table 8 — DC Resistance at 75°C (Ω/1000ft)",
    "ch9-fill": "Chapter 9 Table 1 — Maximum Conduit Fill Percentages",
}


@router.get(
    "/nec-table/{table_id}",
    response_model=NECTableResponse,
    operation_id="get_nec_table",
    summary="Get raw NEC table data",
    description=(
        "Returns raw NEC table data by table ID. Available tables: "
        "'310.16' (ampacity), 'ch9-conductor-area', 'ch9-conduit-area', "
        "'ch9-resistance', 'ch9-fill'."
    ),
)
async def get_nec_table(table_id: str) -> NECTableResponse:
    """Return raw NEC table data for reference."""
    data = NECDataStore.get_table(table_id)
    if data is None:
        raise HTTPException(
            status_code=404,
            detail={
                "message": f"NEC table '{table_id}' not found.",
                "available_tables": list(TABLE_TITLES.keys()),
            },
        )

    title = TABLE_TITLES.get(table_id, f"NEC Table {table_id}")

    return NECTableResponse(
        table_id=table_id,
        title=title,
        data=data,
    )
