"""
TradesCalc — Roofing Calculations Router.

Roof pitch/slope, area from footprint, materials estimation,
rafter length, snow load (ASCE 7), and pitch reference tables.
"""

import math

from fastapi import APIRouter, HTTPException

from tradescalc.models.roofing import (
    AreaRequest,
    AreaResponse,
    MaterialsRequest,
    MaterialsResponse,
    PitchReferenceEntry,
    PitchReferenceResponse,
    PitchRequest,
    PitchResponse,
    RafterLengthRequest,
    RafterLengthResponse,
    SnowLoadRequest,
    SnowLoadResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Helper: compute pitch factor from rise per 12" run
# ---------------------------------------------------------------------------
def _pitch_factor(rise: float) -> float:
    """Return the rafter-length multiplier: sqrt(1 + (rise/12)^2)."""
    return math.sqrt(1.0 + (rise / 12.0) ** 2)


# ---------------------------------------------------------------------------
# 1. POST /pitch — Calculate roof pitch and slope
# ---------------------------------------------------------------------------
@router.post(
    "/pitch",
    response_model=PitchResponse,
    summary="Calculate roof pitch and slope",
    description=(
        "Compute roof pitch ratio, slope in degrees, slope percentage, and "
        "the pitch factor (rafter length multiplier). Provide either "
        "rise_inches (rise per 12 in. run) or rise_ft + run_ft."
    ),
    operation_id="calculate_roof_pitch",
)
async def calculate_pitch(request: PitchRequest) -> PitchResponse:
    """Calculate roof pitch, slope, and pitch factor."""
    # Determine rise per 12" run
    if request.rise_inches is not None:
        rise_per_12 = request.rise_inches
    elif request.rise_ft is not None and request.run_ft is not None:
        rise_per_12 = (request.rise_ft / request.run_ft) * 12.0
    else:
        raise HTTPException(
            status_code=400,
            detail=("Provide either rise_inches (rise per 12 in. run) or both rise_ft and run_ft."),
        )

    slope_rad = math.atan(rise_per_12 / 12.0)
    slope_deg = math.degrees(slope_rad)
    slope_pct = (rise_per_12 / 12.0) * 100.0
    pf = _pitch_factor(rise_per_12)

    # Format pitch ratio — use integer if whole number
    if rise_per_12 == int(rise_per_12):
        ratio_str = f"{int(rise_per_12)}:12"
    else:
        ratio_str = f"{rise_per_12:.1f}:12"

    return PitchResponse(
        pitch_ratio=ratio_str,
        slope_degrees=round(slope_deg, 2),
        slope_percent=round(slope_pct, 2),
        pitch_factor=round(pf, 3),
    )


# ---------------------------------------------------------------------------
# 2. POST /area — Calculate roof area from footprint
# ---------------------------------------------------------------------------
@router.post(
    "/area",
    response_model=AreaResponse,
    summary="Calculate roof area from building footprint",
    description=(
        "Compute actual roof surface area by applying the pitch factor to "
        "the building footprint area. Includes a configurable waste factor. "
        "Provide footprint_sqft directly or footprint_length_ft + footprint_width_ft."
    ),
    operation_id="calculate_roof_area",
)
async def calculate_area(request: AreaRequest) -> AreaResponse:
    """Calculate roof area from footprint and pitch."""
    # Determine footprint area
    if request.footprint_sqft is not None:
        footprint = request.footprint_sqft
    elif request.footprint_length_ft is not None and request.footprint_width_ft is not None:
        footprint = request.footprint_length_ft * request.footprint_width_ft
    else:
        raise HTTPException(
            status_code=400,
            detail=("Provide either footprint_sqft or both footprint_length_ft and footprint_width_ft."),
        )

    pf = _pitch_factor(request.pitch_rise)
    roof_area = footprint * pf
    waste_factor = 1.0 + request.waste_percent / 100.0
    total_with_waste = roof_area * waste_factor

    return AreaResponse(
        footprint_sqft=round(footprint, 2),
        pitch_factor=round(pf, 3),
        roof_area_sqft=round(roof_area, 2),
        waste_factor=round(waste_factor, 2),
        total_with_waste_sqft=round(total_with_waste, 2),
    )


# ---------------------------------------------------------------------------
# 3. POST /materials — Estimate roofing materials
# ---------------------------------------------------------------------------
# Bundles per square by material type
_BUNDLES_PER_SQUARE: dict[str, float] = {
    "asphalt_shingle": 3.0,
    "architectural_shingle": 3.0,
    "metal_panel": 1.0,  # panels, not bundles — 1 unit per square for estimation
    "tile": 1.0,  # sold by piece; 1 unit = ~100 sqft coverage equivalent
    "cedar_shake": 4.0,  # typically 4 bundles per square for shakes
}

_NAILS_LBS_PER_SQUARE: dict[str, float] = {
    "asphalt_shingle": 2.5,
    "architectural_shingle": 2.5,
    "metal_panel": 1.5,
    "tile": 2.0,
    "cedar_shake": 3.0,
}

_VALID_MATERIALS = set(_BUNDLES_PER_SQUARE.keys())


@router.post(
    "/materials",
    response_model=MaterialsResponse,
    summary="Estimate roofing materials needed",
    description=(
        "Estimate material quantities for a roofing project: squares, "
        "bundles, underlayment rolls, ridge cap, drip edge, starter strips, "
        "and nails. 1 square = 100 sq ft. Supports asphalt shingles, "
        "architectural shingles, metal panels, tile, and cedar shakes."
    ),
    operation_id="estimate_roofing_materials",
)
async def estimate_materials(request: MaterialsRequest) -> MaterialsResponse:
    """Estimate roofing materials from area and material type."""
    mat = request.material_type.lower().strip()
    if mat not in _VALID_MATERIALS:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Invalid material_type '{request.material_type}'. "
                f"Valid options: {', '.join(sorted(_VALID_MATERIALS))}."
            ),
        )

    area = request.roof_area_sqft
    waste_mult = 1.0 + request.waste_percent / 100.0
    squares = (area / 100.0) * waste_mult
    bundles = squares * _BUNDLES_PER_SQUARE[mat]
    nails = squares * _NAILS_LBS_PER_SQUARE[mat]

    # Underlayment: 1 roll = 4 squares (400 sqft), round up
    underlayment_rolls = math.ceil(squares / 4.0)

    # Ridge cap: user-supplied or rough estimate
    ridge = request.ridge_length_ft if request.ridge_length_ft > 0 else area / 50.0

    # Drip edge / eave perimeter: user-supplied or rough estimate
    drip = request.eave_length_ft if request.eave_length_ft > 0 else 4.0 * math.sqrt(area)

    return MaterialsResponse(
        material_type=mat,
        roof_area_sqft=round(area, 2),
        squares=round(squares, 2),
        bundles=round(bundles, 1),
        underlayment_rolls=underlayment_rolls,
        ridge_cap_lf=round(ridge, 1),
        drip_edge_lf=round(drip, 1),
        starter_strip_lf=round(drip, 1),  # starter strip runs along eaves
        nails_lbs=round(nails, 1),
        waste_percent=request.waste_percent,
    )


# ---------------------------------------------------------------------------
# 4. POST /rafter-length — Calculate rafter length
# ---------------------------------------------------------------------------
@router.post(
    "/rafter-length",
    response_model=RafterLengthResponse,
    summary="Calculate rafter length",
    description=(
        "Compute rafter length from horizontal run and roof pitch, "
        "including eave overhang. Formula: rafter = run × pitch_factor; "
        "total = rafter + (overhang_in / 12) × pitch_factor."
    ),
    operation_id="calculate_rafter_length",
)
async def calculate_rafter_length(request: RafterLengthRequest) -> RafterLengthResponse:
    """Calculate rafter length including overhang."""
    pf = _pitch_factor(request.pitch_rise)
    theoretical = request.run_ft * pf
    overhang_run_ft = request.overhang_inches / 12.0
    overhang_length = overhang_run_ft * pf
    total = theoretical + overhang_length

    rise_per_12 = request.pitch_rise
    if rise_per_12 == int(rise_per_12):
        ratio_str = f"{int(rise_per_12)}:12"
    else:
        ratio_str = f"{rise_per_12:.1f}:12"

    return RafterLengthResponse(
        pitch_ratio=ratio_str,
        pitch_factor=round(pf, 3),
        theoretical_length_ft=round(theoretical, 2),
        overhang_length_ft=round(overhang_length, 2),
        total_length_ft=round(total, 2),
    )


# ---------------------------------------------------------------------------
# 5. POST /snow-load — ASCE 7 roof snow load
# ---------------------------------------------------------------------------
@router.post(
    "/snow-load",
    response_model=SnowLoadResponse,
    summary="Calculate roof snow load (ASCE 7)",
    description=(
        "Compute flat and sloped roof snow loads per ASCE 7-22 §7.3. "
        "Flat roof: pf = 0.7 × Ce × Ct × Is × pg. "
        "Slope reduction Cs = 1.0 for ≤ 30°, linearly decreasing to 0 "
        "at 70°, and 0 for > 70°. Sloped roof: ps = Cs × pf."
    ),
    operation_id="calculate_snow_load",
)
async def calculate_snow_load(request: SnowLoadRequest) -> SnowLoadResponse:
    """Calculate roof snow load per ASCE 7."""
    pg = request.ground_snow_load_psf
    ce = request.exposure_factor
    ct = request.thermal_factor
    i_s = request.importance_factor
    slope = request.slope_degrees

    # Flat roof snow load: pf = 0.7 × Ce × Ct × Is × pg
    pf = 0.7 * ce * ct * i_s * pg

    # Slope reduction factor Cs (ASCE 7 §7.4, warm roof, unobstructed)
    if slope <= 30.0:
        cs = 1.0
    elif slope <= 70.0:
        cs = 1.0 - (slope - 30.0) / 40.0
    else:
        cs = 0.0

    ps = cs * pf

    return SnowLoadResponse(
        ground_snow_load_psf=round(pg, 2),
        flat_roof_snow_load_psf=round(pf, 2),
        cs_factor=round(cs, 3),
        sloped_roof_snow_load_psf=round(ps, 2),
        formula_reference="ASCE 7-22 §7.3",
    )


# ---------------------------------------------------------------------------
# 6. GET /pitch-reference — Reference table of common pitches
# ---------------------------------------------------------------------------
_PITCH_REFERENCE: list[dict] = []


def _build_pitch_reference() -> list[dict]:
    """Build the pitch reference table on first access."""
    if _PITCH_REFERENCE:
        return _PITCH_REFERENCE

    suitability_notes: dict[int, str] = {
        1: "Very low slope — requires built-up/membrane roofing only.",
        2: "Minimum slope for asphalt shingles (with double underlayment).",
        3: "Low slope — acceptable for shingles with proper underlayment.",
        4: "Standard residential pitch — most common for shingle roofs.",
        5: "Moderate slope — good water shedding, walkable.",
        6: "Steep residential — excellent drainage, harder to walk.",
        7: "Steep slope — increased wind exposure, difficult to walk.",
        8: "Very steep — significant material and labor cost increase.",
        9: "Very steep — requires special staging and safety equipment.",
        10: "Extremely steep — common on dormers and accent features.",
        12: "45° slope — maximum common pitch, steep A-frame style.",
    }

    for rise in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 12]:
        slope_rad = math.atan(rise / 12.0)
        slope_deg = round(math.degrees(slope_rad), 2)
        slope_pct = round((rise / 12.0) * 100.0, 2)
        pf = round(_pitch_factor(rise), 3)
        note = suitability_notes.get(rise, "")
        _PITCH_REFERENCE.append(
            {
                "pitch_ratio": f"{rise}:12",
                "slope_degrees": slope_deg,
                "slope_percent": slope_pct,
                "pitch_factor": pf,
                "suitability": note,
            }
        )
    return _PITCH_REFERENCE


@router.get(
    "/pitch-reference",
    response_model=PitchReferenceResponse,
    summary="Reference table of common roof pitches",
    description=(
        "Return a reference table of common roof pitches (1:12 through 12:12) "
        "with slope in degrees, slope percentage, pitch factor (rafter "
        "multiplier), and suitability notes for each pitch."
    ),
    operation_id="get_pitch_reference",
)
async def get_pitch_reference() -> PitchReferenceResponse:
    """Return reference table of common roof pitches."""
    table = _build_pitch_reference()
    return PitchReferenceResponse(
        pitches=[PitchReferenceEntry(**row) for row in table],
    )


# ---------------------------------------------------------------------------
# 7. GET /info — Module info endpoint
# ---------------------------------------------------------------------------
@router.get(
    "/info",
    summary="Roofing module information",
    description="Returns a description of the Roofing Calculations module and its available endpoints.",
    operation_id="get_roofing_info",
)
async def get_info() -> dict:
    """Return module description and available endpoints."""
    return {
        "module": "Roofing — Calculations",
        "description": (
            "Roofing calculations including pitch/slope analysis, roof area from "
            "footprint, materials estimation, rafter length, ASCE 7 snow load, "
            "and a pitch reference table."
        ),
        "standards": ["ASCE 7-22", "IRC R905", "IBC Chapter 15"],
        "endpoints": [
            {
                "path": "/v1/roofing/pitch",
                "method": "POST",
                "summary": "Calculate roof pitch, slope, and pitch factor.",
            },
            {
                "path": "/v1/roofing/area",
                "method": "POST",
                "summary": "Calculate roof area from building footprint.",
            },
            {
                "path": "/v1/roofing/materials",
                "method": "POST",
                "summary": "Estimate roofing materials needed.",
            },
            {
                "path": "/v1/roofing/rafter-length",
                "method": "POST",
                "summary": "Calculate rafter length with overhang.",
            },
            {
                "path": "/v1/roofing/snow-load",
                "method": "POST",
                "summary": "Calculate roof snow load per ASCE 7.",
            },
            {
                "path": "/v1/roofing/pitch-reference",
                "method": "GET",
                "summary": "Reference table of common roof pitches.",
            },
            {
                "path": "/v1/roofing/info",
                "method": "GET",
                "summary": "This endpoint — module description and endpoint listing.",
            },
        ],
    }
