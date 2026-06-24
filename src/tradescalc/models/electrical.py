"""
Pydantic models for TradesCalc Electrical API endpoints.

All request/response models for NEC-compliant electrical calculations
including wire sizing, voltage drop, conduit fill, ampacity, derating,
breaker sizing, service entrance, box fill, and transformer sizing.

Uses Pydantic v2 with Field() validators, Literal types for constrained
choices, and comprehensive docstrings for OpenAPI documentation.
"""

from typing import Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Shared Types
# ---------------------------------------------------------------------------
MaterialType = Literal["copper", "aluminum"]
PhaseType = Literal["single", "three"]
ConduitType = Literal["emt", "pvc", "rigid"]
TempRatingType = Literal["60", "75", "90"]


# ---------------------------------------------------------------------------
# Ampacity Lookup — POST /ampacity
# ---------------------------------------------------------------------------
class AmpacityRequest(BaseModel):
    """Request model for NEC Table 310.16 ampacity lookup."""

    wire_size: str = Field(
        ...,
        description="AWG or kcmil conductor size (e.g., '12', '4/0', '250').",
        examples=["12", "4/0", "250"],
    )
    material: MaterialType = Field(
        default="copper",
        description="Conductor material: 'copper' or 'aluminum'.",
        examples=["copper"],
    )
    temp_rating: TempRatingType = Field(
        default="75",
        description="Insulation temperature rating in °C: '60', '75', or '90'.",
        examples=["75"],
    )


class AmpacityResponse(BaseModel):
    """Response model for NEC Table 310.16 ampacity lookup."""

    wire_size: str = Field(description="Conductor size queried.")
    material: str = Field(description="Conductor material.")
    temp_rating: str = Field(description="Temperature rating in °C.")
    ampacity: int = Field(description="Ampacity in amperes per NEC Table 310.16.")
    nec_reference: str = Field(
        default="NEC 2023 Table 310.16",
        description="NEC code reference for this calculation.",
    )


# ---------------------------------------------------------------------------
# Wire Sizing — POST /wire-size
# ---------------------------------------------------------------------------
class WireSizeRequest(BaseModel):
    """Request model for minimum wire size calculation.

    Finds the smallest NEC-compliant conductor that meets both
    ampacity requirements and the 3% voltage drop recommendation.
    """

    load_amps: float = Field(
        ...,
        gt=0,
        description="Load current in amperes.",
        examples=[40.0],
    )
    distance_ft: float = Field(
        ...,
        gt=0,
        description="One-way conductor length in feet.",
        examples=[150.0],
    )
    voltage: float = Field(
        ...,
        gt=0,
        description="System voltage (e.g., 120, 208, 240, 277, 480).",
        examples=[240.0],
    )
    phase: PhaseType = Field(
        default="single",
        description="Phase configuration: 'single' or 'three'.",
        examples=["single"],
    )
    material: MaterialType = Field(
        default="copper",
        description="Conductor material: 'copper' or 'aluminum'.",
        examples=["copper"],
    )
    temp_rating: TempRatingType = Field(
        default="75",
        description="Insulation temperature rating in °C.",
        examples=["75"],
    )
    insulation_type: str = Field(
        default="THWN-2",
        description="Insulation type (e.g., 'THWN', 'THWN-2', 'XHHW').",
        examples=["THWN-2"],
    )


class WireSizeResponse(BaseModel):
    """Response model for minimum wire size calculation."""

    recommended_size: str = Field(
        description="Minimum recommended conductor size (AWG or kcmil)."
    )
    ampacity: int = Field(
        description="Ampacity of the recommended conductor in amperes."
    )
    voltage_drop_percent: float = Field(
        description="Voltage drop percentage at the specified distance."
    )
    voltage_drop_volts: float = Field(
        description="Voltage drop in volts at the specified distance."
    )
    passes_3_percent_rule: bool = Field(
        description="Whether the conductor meets the 3% VD recommendation."
    )
    load_amps: float = Field(description="Input load current in amperes.")
    distance_ft: float = Field(description="Input one-way distance in feet.")
    voltage: float = Field(description="Input system voltage.")
    phase: str = Field(description="Phase configuration used.")
    material: str = Field(description="Conductor material used.")
    nec_reference: str = Field(
        default="NEC 2023 Table 310.16, Chapter 9 Table 8",
        description="NEC code references for this calculation.",
    )


# ---------------------------------------------------------------------------
# Voltage Drop — POST /voltage-drop
# ---------------------------------------------------------------------------
class VoltageDropRequest(BaseModel):
    """Request model for voltage drop calculation.

    Uses Vd = (2 × R × I × D) / 1000 for single-phase,
    with √3/2 multiplier for three-phase circuits.
    R values from NEC Chapter 9, Table 8.
    """

    load_amps: float = Field(
        ...,
        gt=0,
        description="Load current in amperes.",
        examples=[30.0],
    )
    distance_ft: float = Field(
        ...,
        gt=0,
        description="One-way conductor length in feet.",
        examples=[200.0],
    )
    wire_size: str = Field(
        ...,
        description="Conductor size (AWG or kcmil).",
        examples=["10"],
    )
    voltage: float = Field(
        ...,
        gt=0,
        description="System voltage.",
        examples=[240.0],
    )
    phase: PhaseType = Field(
        default="single",
        description="Phase configuration: 'single' or 'three'.",
        examples=["single"],
    )
    material: MaterialType = Field(
        default="copper",
        description="Conductor material: 'copper' or 'aluminum'.",
        examples=["copper"],
    )


class VoltageDropResponse(BaseModel):
    """Response model for voltage drop calculation."""

    drop_volts: float = Field(description="Voltage drop in volts.")
    drop_percent: float = Field(description="Voltage drop as a percentage of system voltage.")
    passes_3_percent_rule: bool = Field(
        description="True if VD ≤ 3% (NEC 210.19(A) Informational Note No. 4 — branch circuits)."
    )
    passes_5_percent_rule: bool = Field(
        description="True if VD ≤ 5% (NEC 210.19(A) Informational Note No. 4 — feeder + branch total)."
    )
    wire_size: str = Field(description="Conductor size used in calculation.")
    load_amps: float = Field(description="Load current used.")
    distance_ft: float = Field(description="One-way distance used.")
    voltage: float = Field(description="System voltage used.")
    phase: str = Field(description="Phase configuration used.")
    material: str = Field(description="Conductor material used.")
    resistance_per_1000ft: float = Field(
        description="Conductor DC resistance in Ω/1000ft at 75°C (from Chapter 9 Table 8)."
    )
    nec_reference: str = Field(
        default="NEC 2023 Chapter 9 Table 8, 210.19(A) Informational Note No. 4",
        description="NEC code references for this calculation.",
    )


# ---------------------------------------------------------------------------
# Conduit Fill — POST /conduit-fill
# ---------------------------------------------------------------------------
class ConductorEntry(BaseModel):
    """A group of conductors of the same size and insulation type."""

    wire_size: str = Field(
        ...,
        description="Conductor size (AWG or kcmil).",
        examples=["12"],
    )
    count: int = Field(
        ...,
        gt=0,
        description="Number of conductors of this size.",
        examples=[4],
    )
    insulation_type: str = Field(
        default="THHN",
        description="Insulation type (areas are for THHN/THWN-2).",
        examples=["THHN"],
    )


class ConduitFillRequest(BaseModel):
    """Request model for NEC conduit fill calculation.

    Determines the minimum conduit trade size based on
    the total cross-sectional area of all conductors and
    NEC Chapter 9, Table 1 fill percentage rules.
    """

    conductors: list[ConductorEntry] = Field(
        ...,
        min_length=1,
        description="List of conductor groups with size, count, and insulation type.",
    )
    conduit_type: ConduitType = Field(
        default="emt",
        description="Conduit type: 'emt', 'pvc', or 'rigid'.",
        examples=["emt"],
    )


class ConduitFillResponse(BaseModel):
    """Response model for conduit fill calculation."""

    min_conduit_size: str = Field(
        description="Minimum conduit trade size that meets fill requirements."
    )
    fill_percent: float = Field(
        description="Actual fill percentage with the selected conduit size."
    )
    fill_area_in2: float = Field(
        description="Total cross-sectional area of all conductors in square inches."
    )
    max_fill_area_in2: float = Field(
        description="Maximum allowable fill area for the selected conduit in square inches."
    )
    conduit_area_in2: float = Field(
        description="Internal cross-sectional area of the selected conduit in square inches."
    )
    max_fill_percent: float = Field(
        description="Maximum allowable fill percentage per NEC Chapter 9, Table 1."
    )
    total_conductors: int = Field(
        description="Total number of individual conductors."
    )
    conduit_type: str = Field(description="Conduit type used.")
    nec_reference: str = Field(
        default="NEC 2023 Chapter 9, Tables 1, 4, and 5",
        description="NEC code references for this calculation.",
    )


# ---------------------------------------------------------------------------
# Ampacity Derated — POST /ampacity-derated
# ---------------------------------------------------------------------------
class AmpacityDeratedRequest(BaseModel):
    """Request model for derated ampacity calculation per NEC 310.15.

    Applies temperature correction factors (ambient temperature)
    and adjustment factors (conductor bundling) to the base
    Table 310.16 ampacity. Optionally applies rooftop temperature
    adder per NEC 310.15(B)(3)(c).
    """

    wire_size: str = Field(
        ...,
        description="AWG or kcmil conductor size.",
        examples=["6"],
    )
    material: MaterialType = Field(
        default="copper",
        description="Conductor material.",
        examples=["copper"],
    )
    temp_rating: TempRatingType = Field(
        default="75",
        description="Insulation temperature rating in °C.",
        examples=["75"],
    )
    ambient_temp_c: float = Field(
        default=30.0,
        ge=-40,
        le=80,
        description="Ambient temperature in °C. Default is 30°C (NEC baseline).",
        examples=[35.0],
    )
    num_current_carrying: int = Field(
        default=3,
        ge=1,
        description="Number of current-carrying conductors in the raceway. 1-3 = no adjustment.",
        examples=[6],
    )
    rooftop_distance_inches: Optional[float] = Field(
        default=None,
        ge=0,
        description=(
            "Distance above rooftop in inches. If provided, applies rooftop "
            "temperature adder per NEC 310.15(B)(3)(c). Set to None if not on rooftop."
        ),
        examples=[6.0],
    )


class AmpacityDeratedResponse(BaseModel):
    """Response model for derated ampacity calculation."""

    base_ampacity: int = Field(
        description="Base ampacity from Table 310.16 before any derating."
    )
    temp_correction_factor: float = Field(
        description="Temperature correction factor applied."
    )
    adjustment_factor: float = Field(
        description="Bundling adjustment factor applied."
    )
    combined_derating_factor: float = Field(
        description="Combined derating factor (temp_correction × adjustment)."
    )
    derated_ampacity: float = Field(
        description="Final derated ampacity in amperes."
    )
    effective_ambient_temp_c: float = Field(
        description="Effective ambient temperature (includes rooftop adder if applicable)."
    )
    rooftop_adder_c: float = Field(
        default=0.0,
        description="Temperature adder for rooftop installations in °C."
    )
    wire_size: str = Field(description="Conductor size used.")
    material: str = Field(description="Conductor material used.")
    temp_rating: str = Field(description="Temperature rating used.")
    nec_reference: str = Field(
        default="NEC 2023 310.15, Table 310.16",
        description="NEC code references for this calculation.",
    )


# ---------------------------------------------------------------------------
# Breaker Sizing — POST /breaker-size
# ---------------------------------------------------------------------------
class BreakerSizeRequest(BaseModel):
    """Request model for breaker sizing per NEC 240.

    Applies 125% continuous load factor when the load is continuous
    (operates for 3+ hours) and rounds up to the next standard
    breaker size.
    """

    load_amps: float = Field(
        ...,
        gt=0,
        description="Load current in amperes.",
        examples=[38.0],
    )
    continuous: bool = Field(
        default=True,
        description="Whether the load is continuous (3+ hours). Applies 125% factor.",
        examples=[True],
    )


class BreakerSizeResponse(BaseModel):
    """Response model for breaker sizing calculation."""

    min_breaker_amps: float = Field(
        description="Minimum breaker amperage (raw, before rounding to standard size)."
    )
    standard_breaker_amps: int = Field(
        description="Next standard breaker size in amperes."
    )
    continuous_load_factor: float = Field(
        description="Load multiplier applied (1.25 for continuous, 1.0 for non-continuous)."
    )
    load_amps: float = Field(description="Input load current.")
    continuous: bool = Field(description="Whether continuous load factor was applied.")
    nec_reference: str = Field(
        default="NEC 2023 210.20(A), 240.6(A)",
        description="NEC code references for this calculation.",
    )


# ---------------------------------------------------------------------------
# Service Entrance — POST /service-entrance
# ---------------------------------------------------------------------------
class ServiceEntranceRequest(BaseModel):
    """Request model for service entrance sizing per NEC Article 230.

    Determines minimum conductor size, conduit size, and
    main breaker rating for a service entrance.
    """

    total_load_amps: float = Field(
        ...,
        gt=0,
        description="Total calculated service load in amperes.",
        examples=[185.0],
    )
    voltage: float = Field(
        ...,
        gt=0,
        description="Service voltage (e.g., 120/240, 208, 480).",
        examples=[240.0],
    )
    phase: PhaseType = Field(
        default="single",
        description="Phase configuration: 'single' or 'three'.",
        examples=["single"],
    )
    material: MaterialType = Field(
        default="copper",
        description="Conductor material.",
        examples=["copper"],
    )


class ServiceEntranceResponse(BaseModel):
    """Response model for service entrance sizing."""

    min_wire_size: str = Field(
        description="Minimum conductor size for service entrance conductors."
    )
    wire_ampacity: int = Field(
        description="Ampacity of the selected conductor."
    )
    min_conduit_size: str = Field(
        description="Minimum conduit size for the service entrance conductors."
    )
    main_breaker_amps: int = Field(
        description="Recommended main breaker size in amperes."
    )
    total_load_amps: float = Field(description="Input service load.")
    voltage: float = Field(description="Service voltage.")
    phase: str = Field(description="Phase configuration.")
    material: str = Field(description="Conductor material.")
    nec_reference: str = Field(
        default="NEC 2023 Article 230, Table 310.16, 240.6(A)",
        description="NEC code references.",
    )


# ---------------------------------------------------------------------------
# Box Fill — POST /box-fill
# ---------------------------------------------------------------------------
class BoxFillConductorEntry(BaseModel):
    """A group of conductors for box fill calculation."""

    wire_size: str = Field(
        ...,
        description="Conductor size (AWG): '14', '12', '10', '8', or '6'.",
        examples=["12"],
    )
    count: int = Field(
        ...,
        gt=0,
        description="Number of conductors of this size.",
        examples=[4],
    )


class BoxFillRequest(BaseModel):
    """Request model for outlet/junction box fill calculation per NEC 314.16.

    Calculates minimum box volume based on conductors, devices,
    clamps, and equipment grounding conductors.
    """

    conductors: list[BoxFillConductorEntry] = Field(
        ...,
        min_length=1,
        description="List of conductor groups entering the box.",
    )
    devices: int = Field(
        default=0,
        ge=0,
        description="Number of device yokes (switches/receptacles). Each counts as 2× largest conductor volume.",
        examples=[2],
    )
    clamps: int = Field(
        default=0,
        ge=0,
        description="Number of internal cable clamps. All clamps count as 1× largest conductor volume total.",
        examples=[1],
    )
    grounds: int = Field(
        default=0,
        ge=0,
        description="Number of equipment grounding conductors. All grounds count as 1× largest conductor volume total.",
        examples=[2],
    )


class SuggestedBox(BaseModel):
    """A standard box size suggestion."""

    box_type: str = Field(description="Box type and dimensions.")
    volume_in3: float = Field(description="Box volume in cubic inches.")


class BoxFillResponse(BaseModel):
    """Response model for box fill calculation."""

    min_box_volume_in3: float = Field(
        description="Minimum required box volume in cubic inches."
    )
    conductor_volume_in3: float = Field(
        description="Volume required for conductors only."
    )
    device_volume_in3: float = Field(
        description="Volume allowance for devices."
    )
    clamp_volume_in3: float = Field(
        description="Volume allowance for internal clamps."
    )
    ground_volume_in3: float = Field(
        description="Volume allowance for grounding conductors."
    )
    suggested_box_sizes: list[SuggestedBox] = Field(
        description="Standard box sizes that meet the minimum volume requirement."
    )
    nec_reference: str = Field(
        default="NEC 2023 314.16",
        description="NEC code reference.",
    )


# ---------------------------------------------------------------------------
# Transformer Sizing — POST /transformer-sizing
# ---------------------------------------------------------------------------
class TransformerSizingRequest(BaseModel):
    """Request model for transformer sizing.

    Determines the minimum standard kVA transformer rating
    based on the connected load in VA.
    """

    load_va: float = Field(
        ...,
        gt=0,
        description="Total connected load in volt-amperes (VA).",
        examples=[45000.0],
    )
    voltage_primary: float = Field(
        ...,
        gt=0,
        description="Primary (supply) voltage.",
        examples=[480.0],
    )
    voltage_secondary: float = Field(
        ...,
        gt=0,
        description="Secondary (load) voltage.",
        examples=[208.0],
    )


class TransformerSizingResponse(BaseModel):
    """Response model for transformer sizing calculation."""

    min_kva: float = Field(
        description="Minimum required kVA (load_va / 1000)."
    )
    standard_kva: float = Field(
        description="Next standard transformer kVA rating."
    )
    load_va: float = Field(description="Input load in VA.")
    voltage_primary: float = Field(description="Primary voltage.")
    voltage_secondary: float = Field(description="Secondary voltage.")
    primary_fla: float = Field(
        description="Full-load amps on the primary side at the standard kVA rating."
    )
    secondary_fla: float = Field(
        description="Full-load amps on the secondary side at the standard kVA rating."
    )
    nec_reference: str = Field(
        default="NEC 2023 Article 450",
        description="NEC code reference.",
    )


# ---------------------------------------------------------------------------
# NEC Table Lookup — GET /nec-table/{table_id}
# ---------------------------------------------------------------------------
class NECTableResponse(BaseModel):
    """Response model for raw NEC table data lookup."""

    table_id: str = Field(description="NEC table identifier.")
    title: str = Field(description="Human-readable table title.")
    data: dict = Field(description="Raw table data as key-value pairs.")
    nec_reference: str = Field(
        default="NEC 2023",
        description="NEC code reference.",
    )
