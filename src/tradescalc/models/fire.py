"""
TradesCalc — Fire Protection Engineering Models.

Pydantic v2 models for hydrant flow testing, friction loss,
pump discharge pressure, needed fire flow, ISO grading, and NERIS codes.
"""

from pydantic import BaseModel, Field
from typing import Optional


# ---------------------------------------------------------------------------
# Hydrant Flow Testing
# ---------------------------------------------------------------------------
class HydrantFlowRequest(BaseModel):
    """Input for calculating available fire flow from a hydrant flow test."""

    static_pressure_psi: float = Field(
        ...,
        gt=0,
        description="Static (no-flow) pressure reading in psi.",
        json_schema_extra={"examples": [65.0]},
    )
    residual_pressure_psi: float = Field(
        ...,
        gt=0,
        description="Residual pressure reading while flowing in psi.",
        json_schema_extra={"examples": [40.0]},
    )
    flow_at_residual_gpm: float = Field(
        ...,
        gt=0,
        description="Measured flow rate at residual pressure in GPM.",
        json_schema_extra={"examples": [880.0]},
    )


class HydrantFlowResponse(BaseModel):
    """Calculated available fire flow at 20 psi residual pressure."""

    available_flow_at_20psi_gpm: float = Field(
        ...,
        description="Estimated available flow at 20 psi residual pressure (GPM).",
    )
    flow_coefficient: float = Field(
        ...,
        description="Computed flow coefficient used in the calculation.",
    )
    static_psi: float = Field(..., description="Static pressure echoed back (psi).")
    residual_psi: float = Field(..., description="Residual pressure echoed back (psi).")


# ---------------------------------------------------------------------------
# Friction Loss (Hazen-Williams)
# ---------------------------------------------------------------------------
class FrictionLossRequest(BaseModel):
    """Input for Hazen-Williams friction loss calculation."""

    flow_gpm: float = Field(
        ...,
        gt=0,
        description="Flow rate through the hose/pipe in GPM.",
        json_schema_extra={"examples": [250.0]},
    )
    hose_diameter_inches: float = Field(
        ...,
        gt=0,
        description="Internal diameter of the hose or pipe in inches.",
        json_schema_extra={"examples": [2.5]},
    )
    length_ft: float = Field(
        ...,
        gt=0,
        description="Total length of the hose/pipe run in feet.",
        json_schema_extra={"examples": [400.0]},
    )
    c_factor: float = Field(
        default=120.0,
        gt=0,
        description=(
            "Hazen-Williams roughness coefficient. "
            "Common values: 120 (lined cast iron/rubber-lined hose), "
            "140 (new copper/PVC), 100 (old unlined cast iron)."
        ),
    )


class FrictionLossResponse(BaseModel):
    """Calculated friction loss through a hose or pipe."""

    friction_loss_psi: float = Field(
        ...,
        description="Total friction loss over the full length in psi.",
    )
    friction_loss_per_100ft: float = Field(
        ...,
        description="Friction loss per 100 feet of hose/pipe in psi.",
    )
    formula_used: str = Field(
        default="Hazen-Williams",
        description="Hydraulic formula used for the calculation.",
    )


# ---------------------------------------------------------------------------
# Pump Discharge Pressure
# ---------------------------------------------------------------------------
class PumpPressureRequest(BaseModel):
    """Input for engine pump discharge pressure calculation."""

    nozzle_pressure_psi: float = Field(
        ...,
        gt=0,
        description="Required nozzle pressure in psi.",
        json_schema_extra={"examples": [100.0]},
    )
    friction_loss_psi: float = Field(
        ...,
        ge=0,
        description="Total friction loss in the hose layout in psi.",
        json_schema_extra={"examples": [32.0]},
    )
    elevation_ft: float = Field(
        ...,
        description=(
            "Elevation change in feet (positive = uphill from pump, "
            "negative = downhill). Converts at 0.434 psi per foot of head."
        ),
        json_schema_extra={"examples": [30.0]},
    )
    appliance_loss_psi: float = Field(
        default=0.0,
        ge=0,
        description="Friction loss through appliances (standpipes, wyes, etc.) in psi.",
    )


class PressureBreakdown(BaseModel):
    """Component breakdown of the pump discharge pressure."""

    nozzle_pressure_psi: float = Field(..., description="Required nozzle pressure.")
    friction_loss_psi: float = Field(..., description="Total friction loss.")
    elevation_pressure_psi: float = Field(
        ...,
        description="Pressure gain/loss due to elevation (0.434 psi/ft).",
    )
    appliance_loss_psi: float = Field(..., description="Friction loss through appliances.")


class PumpPressureResponse(BaseModel):
    """Calculated engine pump discharge pressure (PDP)."""

    engine_pressure_psi: float = Field(
        ...,
        description="Required engine pump discharge pressure in psi.",
    )
    breakdown: PressureBreakdown = Field(
        ...,
        description="Component breakdown of the pump discharge pressure.",
    )


# ---------------------------------------------------------------------------
# Needed Fire Flow (ISO / NFPA simplified)
# ---------------------------------------------------------------------------
class NeededFireFlowRequest(BaseModel):
    """Input for ISO/NFPA Needed Fire Flow calculation."""

    area_sqft: float = Field(
        ...,
        gt=0,
        description="Effective area of the largest floor of the building in square feet.",
        json_schema_extra={"examples": [5000.0]},
    )
    construction_class: int = Field(
        ...,
        ge=1,
        le=6,
        description=(
            "ISO construction class (1-6). "
            "1 = Frame, 2 = Joisted Masonry, 3 = Heavy Timber, "
            "4 = Non-Combustible, 5 = Modified Fire Resistive, "
            "6 = Fire Resistive."
        ),
        json_schema_extra={"examples": [3]},
    )
    occupancy_factor: Optional[float] = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description=(
            "Occupancy adjustment factor (-0.25 to +0.25 typical). "
            "Positive increases NFF for high-hazard occupancies, negative decreases. "
            "If omitted, no adjustment is applied."
        ),
    )
    exposure_factor: Optional[float] = Field(
        default=None,
        ge=-1.0,
        le=1.0,
        description=(
            "Exposure/communication adjustment factor (-0.25 to +0.25 typical). "
            "Accounts for adjacent structures. If omitted, no adjustment is applied."
        ),
    )


class NeededFireFlowResponse(BaseModel):
    """Calculated Needed Fire Flow per ISO/NFPA methodology."""

    needed_fire_flow_gpm: float = Field(
        ...,
        description="Final Needed Fire Flow after adjustments and capping (GPM).",
    )
    base_flow_gpm: float = Field(
        ...,
        description="Base NFF before occupancy and exposure adjustments (GPM).",
    )
    adjusted_flow_gpm: float = Field(
        ...,
        description="NFF after occupancy/exposure adjustments, before capping (GPM).",
    )
    duration_hours: int = Field(
        ...,
        description="Required flow duration in hours based on final NFF.",
    )


# ---------------------------------------------------------------------------
# ISO FSRS Grading Structure
# ---------------------------------------------------------------------------
class ISOGradingCategory(BaseModel):
    """A single category in the ISO Fire Suppression Rating Schedule."""

    category: str = Field(..., description="Name of the grading category.")
    max_points: float = Field(..., description="Maximum points available.")
    percentage_of_total: float = Field(
        ...,
        description="Percentage weight toward total possible score.",
    )


class ISOGradingResponse(BaseModel):
    """ISO Fire Suppression Rating Schedule (FSRS) grading structure and weights."""

    categories: list[ISOGradingCategory] = Field(
        ...,
        description="Grading categories with their weights.",
    )
    total_possible: float = Field(
        ...,
        description="Total possible points (including CRR bonus).",
    )


# ---------------------------------------------------------------------------
# NERIS Incident Type Codes
# ---------------------------------------------------------------------------
class NERISCodeResponse(BaseModel):
    """A single NERIS incident type code."""

    code: str = Field(..., description="NERIS incident type code (e.g. '111').")
    description: str = Field(..., description="Human-readable description of the code.")
    category: str = Field(..., description="Broad category grouping (e.g. 'Fire', 'EMS', 'Service Call').")
