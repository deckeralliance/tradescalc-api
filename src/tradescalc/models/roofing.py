"""
TradesCalc — Roofing Calculations Models.

Pydantic v2 models for roof pitch, area, materials estimation,
rafter length, snow load (ASCE 7), and pitch reference tables.
"""

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Roof Pitch / Slope
# ---------------------------------------------------------------------------
class PitchRequest(BaseModel):
    """Input for calculating roof pitch and slope.

    Provide EITHER rise_inches (rise per 12 in. run) OR both rise_ft and
    run_ft for a custom rise/run ratio.
    """

    rise_inches: float | None = Field(
        default=None,
        gt=0,
        description=(
            "Vertical rise in inches per 12-inch horizontal run. Standard residential pitches range from 3 to 12."
        ),
        json_schema_extra={"examples": [6.0]},
    )
    rise_ft: float | None = Field(
        default=None,
        gt=0,
        description="Vertical rise in feet (used with run_ft for custom ratio).",
        json_schema_extra={"examples": [8.0]},
    )
    run_ft: float | None = Field(
        default=None,
        gt=0,
        description="Horizontal run in feet (used with rise_ft for custom ratio).",
        json_schema_extra={"examples": [16.0]},
    )


class PitchResponse(BaseModel):
    """Calculated roof pitch, slope, and rafter-length multiplier."""

    pitch_ratio: str = Field(
        ...,
        description="Roof pitch expressed as rise:12 (e.g. '6:12').",
    )
    slope_degrees: float = Field(
        ...,
        description="Slope angle in degrees.",
    )
    slope_percent: float = Field(
        ...,
        description="Slope expressed as a percentage (rise / run × 100).",
    )
    pitch_factor: float = Field(
        ...,
        description=(
            "Rafter length multiplier. Multiply horizontal run by this factor to get the rafter (hypotenuse) length."
        ),
    )


# ---------------------------------------------------------------------------
# Roof Area from Footprint
# ---------------------------------------------------------------------------
class AreaRequest(BaseModel):
    """Input for calculating roof area from building footprint.

    Provide EITHER footprint_sqft directly OR footprint_length_ft and
    footprint_width_ft. pitch_rise is always required.
    """

    footprint_sqft: float | None = Field(
        default=None,
        gt=0,
        description="Building footprint area in square feet.",
        json_schema_extra={"examples": [2000.0]},
    )
    footprint_length_ft: float | None = Field(
        default=None,
        gt=0,
        description="Footprint length in feet (used with width to compute area).",
        json_schema_extra={"examples": [50.0]},
    )
    footprint_width_ft: float | None = Field(
        default=None,
        gt=0,
        description="Footprint width in feet (used with length to compute area).",
        json_schema_extra={"examples": [40.0]},
    )
    pitch_rise: float = Field(
        ...,
        gt=0,
        le=24,
        description="Roof rise in inches per 12-inch horizontal run.",
        json_schema_extra={"examples": [6.0]},
    )
    waste_percent: float = Field(
        default=10.0,
        ge=0,
        le=50,
        description="Waste factor percentage to add for cuts, overlaps, and waste (default 10%).",
        json_schema_extra={"examples": [10.0]},
    )


class AreaResponse(BaseModel):
    """Calculated roof area with waste factor applied."""

    footprint_sqft: float = Field(
        ...,
        description="Building footprint area used in calculation (sq ft).",
    )
    pitch_factor: float = Field(
        ...,
        description="Pitch multiplier applied (sqrt(1 + (rise/12)^2)).",
    )
    roof_area_sqft: float = Field(
        ...,
        description="Actual roof surface area before waste (sq ft).",
    )
    waste_factor: float = Field(
        ...,
        description="Waste multiplier applied (e.g. 1.10 for 10% waste).",
    )
    total_with_waste_sqft: float = Field(
        ...,
        description="Total roof area including waste allowance (sq ft).",
    )


# ---------------------------------------------------------------------------
# Materials Estimation
# ---------------------------------------------------------------------------
class MaterialsRequest(BaseModel):
    """Input for estimating roofing materials needed."""

    roof_area_sqft: float = Field(
        ...,
        gt=0,
        description="Total roof area in square feet (include waste if desired).",
        json_schema_extra={"examples": [2400.0]},
    )
    material_type: str = Field(
        default="asphalt_shingle",
        description=(
            "Roofing material type. Options: asphalt_shingle, architectural_shingle, metal_panel, tile, cedar_shake."
        ),
        json_schema_extra={"examples": ["asphalt_shingle"]},
    )
    ridge_length_ft: float = Field(
        default=0.0,
        ge=0,
        description=(
            "Total ridge and hip length in linear feet. If 0, estimated as roof_area / 50 for a rough approximation."
        ),
        json_schema_extra={"examples": [50.0]},
    )
    eave_length_ft: float = Field(
        default=0.0,
        ge=0,
        description=(
            "Total eave (drip edge) perimeter in linear feet. "
            "If 0, estimated as 4 × sqrt(roof_area) for a rough approximation."
        ),
        json_schema_extra={"examples": [180.0]},
    )
    waste_percent: float = Field(
        default=10.0,
        ge=0,
        le=50,
        description="Waste factor percentage for material ordering (default 10%).",
        json_schema_extra={"examples": [10.0]},
    )


class MaterialsResponse(BaseModel):
    """Estimated roofing materials quantities."""

    material_type: str = Field(
        ...,
        description="Roofing material type used for estimation.",
    )
    roof_area_sqft: float = Field(
        ...,
        description="Roof area used in the calculation (sq ft).",
    )
    squares: float = Field(
        ...,
        description="Number of roofing squares (1 square = 100 sq ft).",
    )
    bundles: float = Field(
        ...,
        description="Number of bundles needed (3 per square for shingles, varies by material).",
    )
    underlayment_rolls: int = Field(
        ...,
        description="Number of underlayment rolls (1 roll covers ~4 squares / 400 sq ft).",
    )
    ridge_cap_lf: float = Field(
        ...,
        description="Ridge cap material in linear feet.",
    )
    drip_edge_lf: float = Field(
        ...,
        description="Drip edge material in linear feet.",
    )
    starter_strip_lf: float = Field(
        ...,
        description="Starter strip material in linear feet (same as eave perimeter).",
    )
    nails_lbs: float = Field(
        ...,
        description="Estimated roofing nails in pounds (~2.5 lbs per square for shingles).",
    )
    waste_percent: float = Field(
        ...,
        description="Waste factor percentage applied to material quantities.",
    )


# ---------------------------------------------------------------------------
# Rafter Length
# ---------------------------------------------------------------------------
class RafterLengthRequest(BaseModel):
    """Input for calculating rafter length from run and pitch."""

    run_ft: float = Field(
        ...,
        gt=0,
        description="Horizontal distance from wall plate to ridge board in feet.",
        json_schema_extra={"examples": [12.0]},
    )
    pitch_rise: float = Field(
        ...,
        gt=0,
        le=24,
        description="Roof rise in inches per 12-inch horizontal run.",
        json_schema_extra={"examples": [6.0]},
    )
    overhang_inches: float = Field(
        default=12.0,
        ge=0,
        le=48,
        description="Eave overhang (horizontal projection) in inches (default 12 in.).",
        json_schema_extra={"examples": [12.0]},
    )


class RafterLengthResponse(BaseModel):
    """Calculated rafter length with overhang."""

    pitch_ratio: str = Field(
        ...,
        description="Roof pitch expressed as rise:12.",
    )
    pitch_factor: float = Field(
        ...,
        description="Rafter length multiplier for the given pitch.",
    )
    theoretical_length_ft: float = Field(
        ...,
        description="Rafter length from wall plate to ridge, no overhang (ft).",
    )
    overhang_length_ft: float = Field(
        ...,
        description="Overhang rafter length along the slope (ft).",
    )
    total_length_ft: float = Field(
        ...,
        description="Total rafter length including overhang (ft).",
    )


# ---------------------------------------------------------------------------
# Snow Load (ASCE 7)
# ---------------------------------------------------------------------------
class SnowLoadRequest(BaseModel):
    """Input for ASCE 7 roof snow load calculation."""

    ground_snow_load_psf: float = Field(
        ...,
        gt=0,
        description="Ground snow load (pg) in pounds per square foot, per ASCE 7 Figure 7.2-1.",
        json_schema_extra={"examples": [40.0]},
    )
    exposure_factor: float = Field(
        default=1.0,
        gt=0,
        le=1.5,
        description=(
            "Exposure factor (Ce) per ASCE 7 Table 7.3-1. 0.7 (fully exposed, windy) to 1.2 (sheltered). Default 1.0."
        ),
        json_schema_extra={"examples": [1.0]},
    )
    thermal_factor: float = Field(
        default=1.0,
        gt=0,
        le=1.5,
        description=(
            "Thermal factor (Ct) per ASCE 7 Table 7.3-2. "
            "1.0 (heated), 1.1 (minimally heated), 1.2 (unheated/open). Default 1.0."
        ),
        json_schema_extra={"examples": [1.0]},
    )
    importance_factor: float = Field(
        default=1.0,
        gt=0,
        le=1.2,
        description=(
            "Importance/risk factor (Is) per ASCE 7 Table 1.5-2. "
            "0.8 (low risk) to 1.2 (essential facilities). Default 1.0."
        ),
        json_schema_extra={"examples": [1.0]},
    )
    slope_degrees: float = Field(
        default=0.0,
        ge=0,
        le=90,
        description="Roof slope in degrees for slope reduction factor Cs. Default 0 (flat).",
        json_schema_extra={"examples": [26.57]},
    )


class SnowLoadResponse(BaseModel):
    """Calculated roof snow loads per ASCE 7."""

    ground_snow_load_psf: float = Field(
        ...,
        description="Input ground snow load pg (psf).",
    )
    flat_roof_snow_load_psf: float = Field(
        ...,
        description="Flat roof snow load pf = 0.7 × Ce × Ct × Is × pg (psf).",
    )
    cs_factor: float = Field(
        ...,
        description=("Slope reduction factor Cs. 1.0 for slopes ≤ 30°, linearly reduced to 0 between 30° and 70°."),
    )
    sloped_roof_snow_load_psf: float = Field(
        ...,
        description="Sloped roof snow load ps = Cs × pf (psf).",
    )
    formula_reference: str = Field(
        default="ASCE 7-22 §7.3",
        description="Code reference for the formula used.",
    )


# ---------------------------------------------------------------------------
# Pitch Reference Table
# ---------------------------------------------------------------------------
class PitchReferenceEntry(BaseModel):
    """A single row in the pitch reference table."""

    pitch_ratio: str = Field(..., description="Roof pitch as rise:12.")
    slope_degrees: float = Field(..., description="Slope angle in degrees.")
    slope_percent: float = Field(..., description="Slope as a percentage.")
    pitch_factor: float = Field(..., description="Rafter length multiplier.")
    suitability: str = Field(
        ...,
        description="Typical suitability notes for this pitch.",
    )


class PitchReferenceResponse(BaseModel):
    """Reference table of common roof pitches with engineering data."""

    pitches: list[PitchReferenceEntry] = Field(
        ...,
        description="List of common roof pitches with slope, factor, and suitability notes.",
    )
