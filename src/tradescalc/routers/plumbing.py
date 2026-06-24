"""
TradesCalc — Plumbing Calculations Router.

Water supply pipe sizing, DWV pipe sizing, fixture unit calculations,
water heater sizing, Hazen-Williams friction loss, gas pipe sizing,
and plumbing reference tables.
"""

import math

from fastapi import APIRouter, HTTPException

from tradescalc.models.plumbing import (
    DWVSizingRequest,
    DWVSizingResponse,
    FixtureDetail,
    FixtureUnitsRequest,
    FixtureUnitsResponse,
    FixtureUnitTableEntry,
    GasPipeSizingRequest,
    GasPipeSizingResponse,
    PipeMaterialEntry,
    PipeSizingRequest,
    PipeSizingResponse,
    PlumbingFrictionLossRequest,
    PlumbingFrictionLossResponse,
    WaterHeaterRequest,
    WaterHeaterResponse,
)

router = APIRouter()


# ---------------------------------------------------------------------------
# Pipe inside diameter tables (inches) — nominal size → actual ID
# Ref: UPC Table 610.3, ASTM B88 (copper Type L), ASTM F876 (PEX)
# ---------------------------------------------------------------------------
_PIPE_ID_TABLES: dict[str, list[tuple[str, float]]] = {
    "copper": [
        ('1/2"', 0.545),
        ('3/4"', 0.785),
        ('1"', 1.025),
        ('1-1/4"', 1.265),
        ('1-1/2"', 1.505),
        ('2"', 1.985),
    ],
    "pex": [
        ('3/8"', 0.360),
        ('1/2"', 0.475),
        ('3/4"', 0.680),
        ('1"', 0.862),
    ],
    "cpvc": [
        ('1/2"', 0.536),
        ('3/4"', 0.721),
        ('1"', 0.924),
        ('1-1/4"', 1.188),
        ('1-1/2"', 1.378),
        ('2"', 1.846),
    ],
    "galvanized": [
        ('1/2"', 0.622),
        ('3/4"', 0.824),
        ('1"', 1.049),
        ('1-1/4"', 1.380),
        ('1-1/2"', 1.610),
        ('2"', 2.067),
    ],
}


# ---------------------------------------------------------------------------
# DWV DFU capacity tables — pipe size → max DFU
# Ref: UPC Table 703.2 / IPC Table 710.1
# ---------------------------------------------------------------------------
_DWV_TABLES: dict[str, list[tuple[str, float, str]]] = {
    # (nominal_size, max_dfu, slope)
    "building_drain": [
        ('1-1/4"', 1, '1/4"/ft'),
        ('1-1/2"', 3, '1/4"/ft'),
        ('2"', 21, '1/4"/ft'),
        ('3"', 42, '1/4"/ft'),
        ('4"', 216, '1/8"/ft'),
        ('6"', 720, '1/8"/ft'),
    ],
    "branch": [
        ('1-1/4"', 1, '1/4"/ft'),
        ('1-1/2"', 3, '1/4"/ft'),
        ('2"', 6, '1/4"/ft'),
        ('3"', 20, '1/8"/ft'),
        ('4"', 160, '1/8"/ft'),
    ],
    "vent_stack": [
        ('1-1/4"', 8, "N/A"),
        ('1-1/2"', 24, "N/A"),
        ('2"', 48, "N/A"),
        ('3"', 240, "N/A"),
        ('4"', 500, "N/A"),
    ],
    "building_sewer": [
        ('3"', 42, '1/4"/ft'),
        ('4"', 216, '1/8"/ft'),
        ('6"', 720, '1/8"/ft'),
    ],
}


# ---------------------------------------------------------------------------
# Fixture unit values — WSFU and DFU per fixture
# Ref: UPC Table 702.1 (DFU) / UPC Table 610.3 (WSFU)
# ---------------------------------------------------------------------------
_FIXTURE_UNITS: dict[str, dict] = {
    "toilet_flush_tank": {"display": "Toilet (flush tank)", "wsfu": 2.5, "dfu": 4},
    "lavatory": {"display": "Lavatory", "wsfu": 1.0, "dfu": 1},
    "bathtub": {"display": "Bathtub", "wsfu": 4.0, "dfu": 2},
    "kitchen_sink": {"display": "Kitchen Sink", "wsfu": 1.5, "dfu": 2},
    "dishwasher": {"display": "Dishwasher", "wsfu": 1.5, "dfu": 2},
    "washing_machine": {"display": "Washing Machine", "wsfu": 4.0, "dfu": 3},
    "shower": {"display": "Shower", "wsfu": 2.0, "dfu": 2},
    "hose_bibb": {"display": "Hose Bibb", "wsfu": 2.5, "dfu": 0},
}


# ---------------------------------------------------------------------------
# Gas pipe capacity table — IFGC Table 402.4(1)
# Low-pressure natural gas (< 2 psi), 0.5" WC drop, 0.60 SG
# Format: nominal_size → list of (max_length_ft, capacity_btuh)
# Interpolated from IFGC Table 402.4(1) for Schedule 40 steel pipe
# ---------------------------------------------------------------------------
_GAS_PIPE_TABLE: list[tuple[str, list[tuple[int, int]]]] = [
    (
        '1/2"',
        [
            (10, 175_000),
            (20, 120_000),
            (30, 97_000),
            (40, 83_000),
            (50, 73_000),
            (60, 66_000),
            (80, 57_000),
            (100, 50_000),
            (150, 40_000),
            (200, 34_000),
        ],
    ),
    (
        '3/4"',
        [
            (10, 360_000),
            (20, 247_000),
            (30, 199_000),
            (40, 170_000),
            (50, 151_000),
            (60, 137_000),
            (80, 118_000),
            (100, 104_000),
            (150, 84_000),
            (200, 72_000),
        ],
    ),
    (
        '1"',
        [
            (10, 680_000),
            (20, 465_000),
            (30, 375_000),
            (40, 320_000),
            (50, 285_000),
            (60, 257_000),
            (80, 220_000),
            (100, 195_000),
            (150, 157_000),
            (200, 135_000),
        ],
    ),
    (
        '1-1/4"',
        [
            (10, 1_400_000),
            (20, 950_000),
            (30, 770_000),
            (40, 660_000),
            (50, 580_000),
            (60, 530_000),
            (80, 450_000),
            (100, 400_000),
            (150, 320_000),
            (200, 275_000),
        ],
    ),
    (
        '1-1/2"',
        [
            (10, 2_100_000),
            (20, 1_460_000),
            (30, 1_180_000),
            (40, 1_010_000),
            (50, 895_000),
            (60, 810_000),
            (80, 690_000),
            (100, 615_000),
            (150, 490_000),
            (200, 425_000),
        ],
    ),
    (
        '2"',
        [
            (10, 3_950_000),
            (20, 2_750_000),
            (30, 2_200_000),
            (40, 1_900_000),
            (50, 1_680_000),
            (60, 1_520_000),
            (80, 1_300_000),
            (100, 1_150_000),
            (150, 930_000),
            (200, 800_000),
        ],
    ),
]


# ---------------------------------------------------------------------------
# Pipe material properties for reference endpoint
# ---------------------------------------------------------------------------
_PIPE_MATERIALS: list[dict] = [
    {
        "material": "copper",
        "display_name": "Copper (Type L)",
        "c_factor": 150,
        "max_temp_f": 400,
        "max_pressure_psi": 150,
        "common_uses": "Hot and cold water supply, hydronic heating",
    },
    {
        "material": "pex",
        "display_name": "PEX (Cross-linked Polyethylene)",
        "c_factor": 150,
        "max_temp_f": 200,
        "max_pressure_psi": 100,
        "common_uses": "Residential hot and cold water supply, radiant floor heating",
    },
    {
        "material": "cpvc",
        "display_name": "CPVC (Chlorinated PVC)",
        "c_factor": 150,
        "max_temp_f": 200,
        "max_pressure_psi": 100,
        "common_uses": "Hot and cold water supply, residential and commercial",
    },
    {
        "material": "galvanized",
        "display_name": "Galvanized Steel",
        "c_factor": 120,
        "max_temp_f": 400,
        "max_pressure_psi": 150,
        "common_uses": "Water mains, sprinkler systems, older building supply lines",
    },
    {
        "material": "cast_iron",
        "display_name": "Cast Iron",
        "c_factor": 100,
        "max_temp_f": 500,
        "max_pressure_psi": 200,
        "common_uses": "DWV drain lines, sewer mains, commercial drainage",
    },
]


# ---------------------------------------------------------------------------
# 1. POST /pipe-sizing — Water supply pipe sizing (velocity method)
# ---------------------------------------------------------------------------
@router.post(
    "/pipe-sizing",
    response_model=PipeSizingResponse,
    summary="Size a water supply pipe by velocity method",
    description=(
        "Select the smallest pipe where water velocity stays ≤ max_velocity_fps. "
        "Uses Q = A × V where A = π/4 × d². Supports copper (Type L), PEX, CPVC, "
        "and galvanized pipe. Ref: UPC Section 610.10 / IPC Section 903.3."
    ),
    operation_id="calculate_pipe_sizing",
)
async def calculate_pipe_sizing(request: PipeSizingRequest) -> PipeSizingResponse:
    """Size a water supply pipe using the velocity method: Q = A × V."""
    material = request.pipe_material.lower()
    if material not in _PIPE_ID_TABLES:
        raise HTTPException(
            status_code=400,
            detail=(
                f"Unknown pipe material: '{request.pipe_material}'. Supported: {', '.join(_PIPE_ID_TABLES.keys())}."
            ),
        )

    # Q (ft³/s) = GPM × 0.002228
    q_cfs = request.flow_gpm * 0.002228

    pipe_sizes = _PIPE_ID_TABLES[material]
    for nominal, inside_dia in pipe_sizes:
        # A = π/4 × d² (convert inches to feet: d/12)
        area_sqft = (math.pi / 4.0) * (inside_dia / 12.0) ** 2
        velocity = q_cfs / area_sqft
        if velocity <= request.max_velocity_fps:
            return PipeSizingResponse(
                recommended_pipe_size=nominal,
                actual_velocity_fps=round(velocity, 2),
                inside_diameter_in=inside_dia,
                pipe_material=material,
            )

    # Flow exceeds capacity of largest available pipe
    largest_nom, largest_id = pipe_sizes[-1]
    largest_area = (math.pi / 4.0) * (largest_id / 12.0) ** 2
    largest_velocity = q_cfs / largest_area
    raise HTTPException(
        status_code=400,
        detail=(
            f"Flow of {request.flow_gpm} GPM exceeds capacity of largest "
            f"{material} pipe ({largest_nom}). Velocity would be "
            f"{round(largest_velocity, 1)} fps. Consider parallel runs or "
            f"a larger pipe material."
        ),
    )


# ---------------------------------------------------------------------------
# 2. POST /dwv-sizing — Drain/Waste/Vent pipe sizing
# ---------------------------------------------------------------------------
@router.post(
    "/dwv-sizing",
    response_model=DWVSizingResponse,
    summary="Size a DWV (drain/waste/vent) pipe by fixture units",
    description=(
        "Determine the minimum DWV pipe size based on total drainage fixture "
        "units (DFU) and pipe type. Uses UPC Table 703.2 / IPC Table 710.1."
    ),
    operation_id="calculate_dwv_sizing",
)
async def calculate_dwv_sizing(request: DWVSizingRequest) -> DWVSizingResponse:
    """Size a DWV pipe based on drainage fixture unit load."""
    pipe_type = request.pipe_type.lower()
    if pipe_type not in _DWV_TABLES:
        raise HTTPException(
            status_code=400,
            detail=(f"Unknown pipe type: '{request.pipe_type}'. Supported: {', '.join(_DWV_TABLES.keys())}."),
        )

    table = _DWV_TABLES[pipe_type]
    for nominal, max_dfu, slope in table:
        if request.total_dfu <= max_dfu:
            return DWVSizingResponse(
                minimum_pipe_size=nominal,
                total_dfu=request.total_dfu,
                pipe_type=pipe_type,
                slope_per_foot=slope,
            )

    # DFU exceeds table capacity
    largest_nom, largest_dfu, _ = table[-1]
    raise HTTPException(
        status_code=400,
        detail=(
            f"{request.total_dfu} DFU exceeds capacity of largest "
            f"{pipe_type} pipe ({largest_nom} at {largest_dfu} DFU). "
            f"Consult an engineer for larger sizing."
        ),
    )


# ---------------------------------------------------------------------------
# 3. POST /fixture-units — Calculate total fixture units
# ---------------------------------------------------------------------------
@router.post(
    "/fixture-units",
    response_model=FixtureUnitsResponse,
    summary="Calculate total fixture units for a building",
    description=(
        "Compute total water supply fixture units (WSFU) and drainage fixture "
        "units (DFU) from a list of plumbing fixtures. "
        "Ref: UPC Table 702.1 / IPC Table 709.1."
    ),
    operation_id="calculate_fixture_units",
)
async def calculate_fixture_units(request: FixtureUnitsRequest) -> FixtureUnitsResponse:
    """Calculate total WSFU and DFU from a list of fixtures."""
    total_wsfu = 0.0
    total_dfu = 0.0
    details: list[FixtureDetail] = []

    for fixture in request.fixtures:
        fixture_type = fixture.type.lower()
        if fixture_type not in _FIXTURE_UNITS:
            raise HTTPException(
                status_code=400,
                detail=(f"Unknown fixture type: '{fixture.type}'. Supported: {', '.join(_FIXTURE_UNITS.keys())}."),
            )
        fu = _FIXTURE_UNITS[fixture_type]
        wsfu_total = fu["wsfu"] * fixture.count
        dfu_total = fu["dfu"] * fixture.count
        total_wsfu += wsfu_total
        total_dfu += dfu_total
        details.append(
            FixtureDetail(
                type=fixture_type,
                count=fixture.count,
                wsfu_each=fu["wsfu"],
                dfu_each=fu["dfu"],
                wsfu_total=wsfu_total,
                dfu_total=dfu_total,
            )
        )

    return FixtureUnitsResponse(
        total_wsfu=round(total_wsfu, 1),
        total_dfu=round(total_dfu, 1),
        fixtures_detail=details,
    )


# ---------------------------------------------------------------------------
# 4. POST /water-heater-sizing — Size a water heater
# ---------------------------------------------------------------------------
_WATER_HEATER_TABLE: list[tuple[tuple[int, int], tuple[float, float], int]] = [
    # ((min_bedrooms, max_bedrooms), (min_bathrooms, max_bathrooms), tank_gallons)
    ((1, 2), (1.0, 1.0), 30),
    ((2, 3), (1.0, 1.5), 40),
    ((3, 4), (1.5, 2.5), 50),
    ((4, 5), (2.5, 3.5), 66),
    ((5, 10), (3.5, 10.0), 80),
]

_RECOVERY_RATES: dict[str, int] = {
    "gas": 40,  # ~40 GPH typical gas recovery
    "electric": 21,  # ~21 GPH typical electric recovery
    "heat_pump": 10,  # ~10 GPH typical heat pump recovery (efficient but slow)
}


@router.post(
    "/water-heater-sizing",
    response_model=WaterHeaterResponse,
    summary="Size a residential water heater",
    description=(
        "Recommend a water heater tank size based on number of bedrooms, "
        "bathrooms, and fuel type. Includes estimated first hour rating and "
        "recovery rate. Ref: UPC Section 507.2 / IRC P2801."
    ),
    operation_id="calculate_water_heater_sizing",
)
async def calculate_water_heater_sizing(request: WaterHeaterRequest) -> WaterHeaterResponse:
    """Size a residential water heater based on bedrooms and bathrooms."""
    fuel = request.fuel_type.lower()
    if fuel not in _RECOVERY_RATES:
        raise HTTPException(
            status_code=400,
            detail=(f"Unknown fuel type: '{request.fuel_type}'. Supported: {', '.join(_RECOVERY_RATES.keys())}."),
        )

    # Find recommended tank size from table
    tank_gallons = 30  # default minimum
    for (min_bed, max_bed), (min_bath, max_bath), gallons in _WATER_HEATER_TABLE:
        if min_bed <= request.num_bedrooms <= max_bed and min_bath <= request.num_bathrooms <= max_bath:
            tank_gallons = gallons
            break
    else:
        # If no exact match, size by bedroom count alone
        if request.num_bedrooms <= 2:
            tank_gallons = 30
        elif request.num_bedrooms <= 3:
            tank_gallons = 40
        elif request.num_bedrooms <= 4:
            tank_gallons = 50
        elif request.num_bedrooms <= 5:
            tank_gallons = 66
        else:
            tank_gallons = 80

    recovery = _RECOVERY_RATES[fuel]
    # First hour rating ≈ tank capacity + recovery rate
    first_hour = tank_gallons + recovery

    return WaterHeaterResponse(
        recommended_tank_gallons=tank_gallons,
        first_hour_rating_gph=first_hour,
        recovery_rate_gph=recovery,
        fuel_type=fuel,
    )


# ---------------------------------------------------------------------------
# 5. POST /friction-loss — Hazen-Williams friction loss for plumbing pipe
# ---------------------------------------------------------------------------
@router.post(
    "/friction-loss",
    response_model=PlumbingFrictionLossResponse,
    summary="Calculate Hazen-Williams friction loss in a plumbing pipe",
    description=(
        "Compute friction loss through a water supply pipe using the Hazen-Williams "
        "formula: hf = (4.52 × Q^1.85) / (C^1.85 × d^4.87) ft of head per foot of pipe. "
        "Result is converted to PSI (1 ft head = 0.433 psi). "
        "Ref: IPC Table E103.3(2)."
    ),
    operation_id="calculate_plumbing_friction_loss",
)
async def calculate_plumbing_friction_loss(
    request: PlumbingFrictionLossRequest,
) -> PlumbingFrictionLossResponse:
    """Calculate Hazen-Williams friction loss in a plumbing pipe."""
    q = request.flow_gpm
    c = request.c_factor
    d = request.pipe_diameter_in
    length = request.pipe_length_ft

    # Hazen-Williams: hf (ft head per ft of pipe) = 4.52 × Q^1.85 / (C^1.85 × d^4.87)
    hf_per_ft = (4.52 * (q**1.85)) / ((c**1.85) * (d**4.87))
    hf_total_ft = hf_per_ft * length
    hf_per_100ft = hf_per_ft * 100.0

    # Convert ft of head to PSI: 1 ft head = 0.433 psi
    fl_psi = hf_total_ft * 0.433
    fl_psi_per_100 = hf_per_100ft * 0.433

    # Velocity: V = Q / (A × 448.83) where A = π/4 × (d/12)²
    # Simplified: V = 0.4085 × Q / d²
    area_sqft = (math.pi / 4.0) * (d / 12.0) ** 2
    q_cfs = q * 0.002228
    velocity = q_cfs / area_sqft

    return PlumbingFrictionLossResponse(
        friction_loss_psi=round(fl_psi, 3),
        friction_loss_psi_per_100ft=round(fl_psi_per_100, 3),
        velocity_fps=round(velocity, 2),
        flow_gpm=q,
    )


# ---------------------------------------------------------------------------
# 6. POST /gas-pipe-sizing — Natural gas pipe sizing
# ---------------------------------------------------------------------------
@router.post(
    "/gas-pipe-sizing",
    response_model=GasPipeSizingResponse,
    summary="Size a natural gas pipe by BTU/hr load",
    description=(
        "Determine the minimum gas pipe size for a given BTU/hr load and pipe "
        "length using the IFGC longest run method. Based on Schedule 40 steel "
        "pipe at low pressure (<2 psi). Ref: IFGC Table 402.4(1)."
    ),
    operation_id="calculate_gas_pipe_sizing",
)
async def calculate_gas_pipe_sizing(request: GasPipeSizingRequest) -> GasPipeSizingResponse:
    """Size a natural gas pipe using IFGC longest run method."""
    target_btuh = request.total_btuh
    run_length = request.pipe_length_ft

    for nominal, length_capacities in _GAS_PIPE_TABLE:
        # Find the applicable capacity for the given pipe length
        # Use the entry with the smallest length ≥ run_length
        capacity = None
        for max_length, cap in length_capacities:
            if run_length <= max_length:
                capacity = cap
                break

        # If run exceeds all lengths in table, use the longest entry
        if capacity is None:
            _, capacity = length_capacities[-1]

        if capacity >= target_btuh:
            return GasPipeSizingResponse(
                minimum_pipe_size=nominal,
                capacity_btuh=capacity,
                pipe_length_ft=run_length,
            )

    # Exceeds all pipe sizes
    largest_nom = _GAS_PIPE_TABLE[-1][0]
    raise HTTPException(
        status_code=400,
        detail=(
            f"Load of {target_btuh:,.0f} BTU/hr exceeds capacity of largest "
            f"pipe ({largest_nom}). Consider parallel runs or higher pressure system."
        ),
    )


# ---------------------------------------------------------------------------
# 7. GET /fixture-unit-table — Reference: full fixture unit table
# ---------------------------------------------------------------------------
@router.get(
    "/fixture-unit-table",
    response_model=list[FixtureUnitTableEntry],
    summary="Plumbing fixture unit reference table",
    description=(
        "Return the complete fixture unit reference table with water supply "
        "fixture units (WSFU) and drainage fixture units (DFU) for all "
        "supported fixture types. Ref: UPC Table 702.1 / IPC Table 709.1."
    ),
    operation_id="get_fixture_unit_table",
)
async def get_fixture_unit_table() -> list[FixtureUnitTableEntry]:
    """Return the complete fixture unit reference table."""
    return [
        FixtureUnitTableEntry(
            fixture_type=key,
            display_name=val["display"],
            wsfu=val["wsfu"],
            dfu=val["dfu"],
        )
        for key, val in _FIXTURE_UNITS.items()
    ]


# ---------------------------------------------------------------------------
# 8. GET /pipe-materials — Reference: pipe material properties
# ---------------------------------------------------------------------------
@router.get(
    "/pipe-materials",
    response_model=list[PipeMaterialEntry],
    summary="Plumbing pipe material reference table",
    description=(
        "Return properties of common plumbing pipe materials including "
        "Hazen-Williams C-factor, temperature and pressure ratings, and "
        "typical applications."
    ),
    operation_id="get_pipe_materials",
)
async def get_pipe_materials() -> list[PipeMaterialEntry]:
    """Return pipe material properties reference table."""
    return [PipeMaterialEntry(**mat) for mat in _PIPE_MATERIALS]


# ---------------------------------------------------------------------------
# 9. GET /info — Module description
# ---------------------------------------------------------------------------
@router.get(
    "/info",
    summary="Plumbing module information",
    description="Returns a description of the Plumbing Calculations module and its available endpoints.",
    operation_id="get_plumbing_info",
)
async def get_info() -> dict:
    """Return module description and available endpoints."""
    return {
        "module": "Plumbing — Calculations",
        "description": (
            "Plumbing engineering calculations including water supply pipe sizing, "
            "DWV pipe sizing, fixture unit totals, water heater sizing, "
            "Hazen-Williams friction loss, natural gas pipe sizing, and "
            "reference tables for fixtures and pipe materials."
        ),
        "standards": ["UPC 2021", "IPC 2021", "IFGC 2021", "IRC 2021"],
        "endpoints": [
            {
                "path": "/v1/plumbing/pipe-sizing",
                "method": "POST",
                "summary": "Size a water supply pipe by velocity method.",
            },
            {
                "path": "/v1/plumbing/dwv-sizing",
                "method": "POST",
                "summary": "Size a DWV pipe by drainage fixture units.",
            },
            {
                "path": "/v1/plumbing/fixture-units",
                "method": "POST",
                "summary": "Calculate total WSFU and DFU for a building.",
            },
            {
                "path": "/v1/plumbing/water-heater-sizing",
                "method": "POST",
                "summary": "Size a residential water heater.",
            },
            {
                "path": "/v1/plumbing/friction-loss",
                "method": "POST",
                "summary": "Hazen-Williams friction loss in plumbing pipe.",
            },
            {
                "path": "/v1/plumbing/gas-pipe-sizing",
                "method": "POST",
                "summary": "Size a natural gas pipe by BTU/hr load.",
            },
            {
                "path": "/v1/plumbing/fixture-unit-table",
                "method": "GET",
                "summary": "Fixture unit reference table (WSFU/DFU).",
            },
            {
                "path": "/v1/plumbing/pipe-materials",
                "method": "GET",
                "summary": "Pipe material properties reference table.",
            },
            {
                "path": "/v1/plumbing/info",
                "method": "GET",
                "summary": "This endpoint — module description and endpoint listing.",
            },
        ],
    }
