"""
TradesCalc — Plumbing Calculations Models.

Pydantic v2 models for water supply pipe sizing, DWV pipe sizing,
fixture unit calculations, water heater sizing, Hazen-Williams friction
loss, gas pipe sizing, and plumbing reference tables.
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Pipe Sizing (Water Supply)
# ---------------------------------------------------------------------------
class PipeSizingRequest(BaseModel):
    """Input for water supply pipe sizing per UPC/IPC velocity method."""

    flow_gpm: float = Field(
        ...,
        gt=0,
        description="Required flow rate in gallons per minute (GPM).",
        json_schema_extra={"examples": [10.0]},
    )
    pipe_material: str = Field(
        ...,
        description=(
            "Pipe material: 'copper' (Type L), 'pex', 'cpvc', or 'galvanized'. "
            "Determines available inside diameters per UPC Table 610.3."
        ),
        json_schema_extra={"examples": ["copper"]},
    )
    max_velocity_fps: float = Field(
        default=8.0,
        gt=0,
        le=15.0,
        description=(
            "Maximum allowable water velocity in feet per second. "
            "UPC/IPC recommends ≤8 fps for cold water, ≤5 fps for hot water. "
            "Ref: UPC Section 610.10."
        ),
        json_schema_extra={"examples": [8.0]},
    )


class PipeSizingResponse(BaseModel):
    """Recommended water supply pipe size based on velocity method."""

    recommended_pipe_size: str = Field(
        ...,
        description="Recommended nominal pipe size (e.g., '3/4\"').",
    )
    actual_velocity_fps: float = Field(
        ...,
        description="Actual water velocity in the recommended pipe (fps).",
    )
    inside_diameter_in: float = Field(
        ...,
        description="Inside diameter of the recommended pipe in inches.",
    )
    pipe_material: str = Field(
        ...,
        description="Pipe material echoed back.",
    )
    reference: str = Field(
        default="UPC Section 610.10 / IPC Section 903.3 — Velocity method: Q = A × V",
        description="Code reference for the calculation method.",
    )


# ---------------------------------------------------------------------------
# DWV Pipe Sizing (Drain/Waste/Vent)
# ---------------------------------------------------------------------------
class DWVSizingRequest(BaseModel):
    """Input for drain/waste/vent pipe sizing per UPC/IPC DFU tables."""

    total_dfu: float = Field(
        ...,
        gt=0,
        description="Total drainage fixture units (DFU) connected to the pipe.",
        json_schema_extra={"examples": [30.0]},
    )
    pipe_type: str = Field(
        ...,
        description=(
            "Type of drain pipe: 'building_drain', 'branch', "
            "'vent_stack', or 'building_sewer'. "
            "Ref: UPC Table 703.2 / IPC Table 710.1."
        ),
        json_schema_extra={"examples": ["building_drain"]},
    )


class DWVSizingResponse(BaseModel):
    """Minimum DWV pipe size for the given fixture unit load."""

    minimum_pipe_size: str = Field(
        ...,
        description="Minimum nominal pipe size (e.g., '3\"').",
    )
    total_dfu: float = Field(
        ...,
        description="Total drainage fixture units echoed back.",
    )
    pipe_type: str = Field(
        ...,
        description="Pipe type echoed back.",
    )
    slope_per_foot: str = Field(
        ...,
        description="Required slope per foot (e.g., '1/4\"/ft' for pipes 3\" and larger).",
    )
    reference: str = Field(
        default="UPC Table 703.2 / IPC Table 710.1 — DFU capacity by pipe size",
        description="Code reference for the sizing table.",
    )


# ---------------------------------------------------------------------------
# Fixture Units
# ---------------------------------------------------------------------------
class FixtureInput(BaseModel):
    """A single fixture type and count for fixture unit calculation."""

    type: str = Field(
        ...,
        description=(
            "Fixture type: 'toilet_flush_tank', 'lavatory', 'bathtub', "
            "'kitchen_sink', 'dishwasher', 'washing_machine', 'shower', "
            "or 'hose_bibb'. Ref: UPC Table 702.1 / IPC Table 709.1."
        ),
        json_schema_extra={"examples": ["toilet_flush_tank"]},
    )
    count: int = Field(
        ...,
        gt=0,
        description="Number of this fixture type.",
        json_schema_extra={"examples": [2]},
    )
    is_public: bool = Field(
        default=False,
        description="Whether fixtures are in a public (commercial) setting. Currently informational.",
    )


class FixtureDetail(BaseModel):
    """Breakdown of fixture units for a single fixture type."""

    type: str = Field(..., description="Fixture type.")
    count: int = Field(..., description="Number of fixtures.")
    wsfu_each: float = Field(..., description="Water supply fixture units per fixture.")
    dfu_each: float = Field(..., description="Drainage fixture units per fixture.")
    wsfu_total: float = Field(..., description="Total WSFU for this fixture type.")
    dfu_total: float = Field(..., description="Total DFU for this fixture type.")


class FixtureUnitsRequest(BaseModel):
    """Input for calculating total fixture units for a building."""

    fixtures: list[FixtureInput] = Field(
        ...,
        min_length=1,
        description="List of fixtures with type and count.",
    )


class FixtureUnitsResponse(BaseModel):
    """Total water supply and drainage fixture units for a building."""

    total_wsfu: float = Field(
        ...,
        description="Total water supply fixture units (WSFU). Ref: UPC Table 610.3.",
    )
    total_dfu: float = Field(
        ...,
        description="Total drainage fixture units (DFU). Ref: UPC Table 702.1.",
    )
    fixtures_detail: list[FixtureDetail] = Field(
        ...,
        description="Breakdown of fixture units by fixture type.",
    )


# ---------------------------------------------------------------------------
# Water Heater Sizing
# ---------------------------------------------------------------------------
class WaterHeaterRequest(BaseModel):
    """Input for residential water heater sizing."""

    num_bedrooms: int = Field(
        ...,
        ge=1,
        le=10,
        description="Number of bedrooms in the dwelling unit.",
        json_schema_extra={"examples": [3]},
    )
    num_bathrooms: float = Field(
        ...,
        gt=0,
        le=10,
        description="Number of bathrooms (supports half baths as 0.5 increments).",
        json_schema_extra={"examples": [2.0]},
    )
    fuel_type: str = Field(
        ...,
        description="Fuel type: 'gas', 'electric', or 'heat_pump'. Affects recovery rate.",
        json_schema_extra={"examples": ["gas"]},
    )


class WaterHeaterResponse(BaseModel):
    """Recommended water heater sizing for a residential dwelling."""

    recommended_tank_gallons: int = Field(
        ...,
        description="Recommended tank capacity in gallons.",
    )
    first_hour_rating_gph: int = Field(
        ...,
        description=(
            "Estimated first hour rating in gallons per hour. Ref: DOE test procedure 10 CFR 430 Subpart B App E."
        ),
    )
    recovery_rate_gph: int = Field(
        ...,
        description="Estimated recovery rate in gallons per hour based on fuel type.",
    )
    fuel_type: str = Field(
        ...,
        description="Fuel type echoed back.",
    )
    reference: str = Field(
        default="UPC Section 507.2 / IRC P2801 — Water heater sizing",
        description="Code reference for the sizing methodology.",
    )


# ---------------------------------------------------------------------------
# Friction Loss (Hazen-Williams for Plumbing Pipe)
# ---------------------------------------------------------------------------
class PlumbingFrictionLossRequest(BaseModel):
    """Input for Hazen-Williams friction loss in plumbing pipe."""

    flow_gpm: float = Field(
        ...,
        gt=0,
        description="Flow rate in gallons per minute (GPM).",
        json_schema_extra={"examples": [10.0]},
    )
    pipe_diameter_in: float = Field(
        ...,
        gt=0,
        description="Inside diameter of the pipe in inches.",
        json_schema_extra={"examples": [0.785]},
    )
    pipe_length_ft: float = Field(
        ...,
        gt=0,
        description="Total equivalent pipe length in feet (include fittings).",
        json_schema_extra={"examples": [100.0]},
    )
    c_factor: float = Field(
        default=150.0,
        gt=0,
        description=(
            "Hazen-Williams roughness coefficient. "
            "Common values: 150 (copper/PEX/CPVC), 120 (galvanized), "
            "100 (cast iron). Ref: IPC Table E103.3(2)."
        ),
        json_schema_extra={"examples": [150.0]},
    )


class PlumbingFrictionLossResponse(BaseModel):
    """Calculated friction loss through a plumbing pipe."""

    friction_loss_psi: float = Field(
        ...,
        description="Total friction loss over the full pipe length in psi.",
    )
    friction_loss_psi_per_100ft: float = Field(
        ...,
        description="Friction loss per 100 feet of pipe in psi.",
    )
    velocity_fps: float = Field(
        ...,
        description="Water velocity in the pipe in feet per second.",
    )
    flow_gpm: float = Field(
        ...,
        description="Flow rate echoed back (GPM).",
    )
    formula_used: str = Field(
        default="Hazen-Williams",
        description="Hydraulic formula used for the calculation.",
    )


# ---------------------------------------------------------------------------
# Gas Pipe Sizing
# ---------------------------------------------------------------------------
class GasPipeSizingRequest(BaseModel):
    """Input for natural gas pipe sizing per IFGC/IRC longest run method."""

    total_btuh: float = Field(
        ...,
        gt=0,
        description="Total connected BTU/hr load for the gas appliances.",
        json_schema_extra={"examples": [200000.0]},
    )
    pipe_length_ft: float = Field(
        ...,
        gt=0,
        description=(
            "Length of pipe run from the meter to the most remote appliance (ft). "
            "Ref: IFGC Section 402.4 — longest run method."
        ),
        json_schema_extra={"examples": [60.0]},
    )
    inlet_pressure_wc: float = Field(
        default=7.0,
        gt=0,
        description='Inlet gas pressure in inches of water column (WC). Typical: 7" WC.',
        json_schema_extra={"examples": [7.0]},
    )
    pressure_drop_wc: float = Field(
        default=0.5,
        gt=0,
        description='Maximum allowable pressure drop in inches WC. Typical: 0.5" WC.',
        json_schema_extra={"examples": [0.5]},
    )
    specific_gravity: float = Field(
        default=0.60,
        gt=0,
        le=2.0,
        description="Specific gravity of the gas. Natural gas: 0.60, propane: 1.52.",
        json_schema_extra={"examples": [0.60]},
    )


class GasPipeSizingResponse(BaseModel):
    """Recommended gas pipe size based on BTU/hr load and pipe length."""

    minimum_pipe_size: str = Field(
        ...,
        description="Minimum nominal pipe size (e.g., '1\"').",
    )
    capacity_btuh: int = Field(
        ...,
        description="BTU/hr capacity of the recommended pipe at the given length.",
    )
    pipe_length_ft: float = Field(
        ...,
        description="Pipe length echoed back (ft).",
    )
    reference: str = Field(
        default="IFGC Table 402.4 / IRC Table G2413.4 — Longest run method, low-pressure natural gas",
        description="Code reference for the gas pipe sizing table.",
    )


# ---------------------------------------------------------------------------
# Reference: Fixture Unit Table
# ---------------------------------------------------------------------------
class FixtureUnitTableEntry(BaseModel):
    """A single fixture type with its WSFU and DFU values."""

    fixture_type: str = Field(..., description="Fixture type identifier.")
    display_name: str = Field(..., description="Human-readable fixture name.")
    wsfu: float = Field(..., description="Water supply fixture units per fixture.")
    dfu: float = Field(..., description="Drainage fixture units per fixture.")


# ---------------------------------------------------------------------------
# Reference: Pipe Materials
# ---------------------------------------------------------------------------
class PipeMaterialEntry(BaseModel):
    """Properties of a plumbing pipe material."""

    material: str = Field(..., description="Pipe material identifier.")
    display_name: str = Field(..., description="Human-readable material name.")
    c_factor: int = Field(..., description="Hazen-Williams C-factor for friction loss calculations.")
    max_temp_f: int = Field(..., description="Maximum service temperature in °F.")
    max_pressure_psi: int = Field(..., description="Maximum working pressure in psi (typical).")
    common_uses: str = Field(..., description="Common applications for this material.")
