"""
NEC Data Store — Loads and provides access to all NEC reference data.

Loads JSON data files at application startup and provides typed lookups
for ampacity, conduit fill, conductor resistance, and other NEC tables.
"""

import json
from pathlib import Path


class NECDataStore:
    """Singleton data store for NEC reference tables."""

    _ampacity_data: dict = {}
    _chapter9_data: dict = {}
    _loaded: bool = False

    @classmethod
    def load_all(cls) -> None:
        """Load all NEC data files into memory."""
        data_dir = Path(__file__).parent.parent / "data"

        with open(data_dir / "nec_310_16.json") as f:
            cls._ampacity_data = json.load(f)

        with open(data_dir / "nec_chapter9.json") as f:
            cls._chapter9_data = json.load(f)

        cls._loaded = True

    @classmethod
    def _ensure_loaded(cls) -> None:
        if not cls._loaded:
            cls.load_all()

    # -----------------------------------------------------------------------
    # Ampacity Lookups (Table 310.16)
    # -----------------------------------------------------------------------
    @classmethod
    def get_ampacity(cls, wire_size: str, material: str = "copper", temp_rating: str = "75") -> int | None:
        """Get ampacity for a given wire size, material, and temperature rating.

        Args:
            wire_size: AWG or kcmil size (e.g., '12', '4/0', '250')
            material: 'copper' or 'aluminum'
            temp_rating: '60', '75', or '90' (degrees Celsius)

        Returns:
            Ampacity in amps, or None if not found.
        """
        cls._ensure_loaded()
        material_data = cls._ampacity_data.get(material.lower(), {})
        size_data = material_data.get(str(wire_size), {})
        value = size_data.get(str(temp_rating))
        return int(value) if value is not None else None

    @classmethod
    def get_all_ampacities(cls, material: str = "copper") -> dict:
        """Get all ampacity data for a material."""
        cls._ensure_loaded()
        return cls._ampacity_data.get(material.lower(), {})

    # -----------------------------------------------------------------------
    # Conductor Properties (Chapter 9)
    # -----------------------------------------------------------------------
    @classmethod
    def get_conductor_area(cls, wire_size: str) -> float | None:
        """Get conductor area (with insulation) in square inches for THHN/THWN-2."""
        cls._ensure_loaded()
        return cls._chapter9_data.get("conductor_area_in2", {}).get(str(wire_size))

    @classmethod
    def get_conductor_resistance(cls, wire_size: str, material: str = "copper") -> float | None:
        """Get DC resistance in ohms per 1000 ft at 75°C."""
        cls._ensure_loaded()
        resistance_data = cls._chapter9_data.get("conductor_resistance_ohms_per_1000ft", {})
        return resistance_data.get(material.lower(), {}).get(str(wire_size))

    # -----------------------------------------------------------------------
    # Conduit Fill (Chapter 9 Tables 1 & 4)
    # -----------------------------------------------------------------------
    @classmethod
    def get_conduit_area(cls, conduit_size: str, conduit_type: str = "emt") -> float | None:
        """Get internal cross-sectional area of conduit in square inches.

        Args:
            conduit_size: Trade size (e.g., '1/2', '3/4', '1', '2')
            conduit_type: 'emt', 'pvc', or 'rigid'
        """
        cls._ensure_loaded()
        type_map = {
            "emt": "conduit_area_in2",
            "pvc": "conduit_area_pvc_sch40_in2",
            "rigid": "conduit_area_rigid_in2",
        }
        key = type_map.get(conduit_type.lower(), "conduit_area_in2")
        return cls._chapter9_data.get(key, {}).get(str(conduit_size))

    @classmethod
    def get_fill_percentage(cls, num_conductors: int) -> float:
        """Get maximum fill percentage for conduit based on number of conductors.

        NEC Chapter 9, Table 1:
        - 1 conductor: 53%
        - 2 conductors: 31%
        - 3 or more: 40%
        """
        cls._ensure_loaded()
        fill_data = cls._chapter9_data.get("fill_percentages", {})
        if num_conductors == 1:
            return fill_data.get("1_conductor", 53) / 100.0
        elif num_conductors == 2:
            return fill_data.get("2_conductors", 31) / 100.0
        else:
            return fill_data.get("3_or_more", 40) / 100.0

    @classmethod
    def get_standard_wire_sizes(cls) -> list[str]:
        """Get ordered list of standard wire sizes from 14 AWG to 1000 kcmil."""
        cls._ensure_loaded()
        return cls._chapter9_data.get("standard_wire_sizes_awg_kcmil", [])

    @classmethod
    def get_standard_conduit_sizes(cls) -> list[str]:
        """Get ordered list of standard conduit trade sizes."""
        cls._ensure_loaded()
        return cls._chapter9_data.get("standard_conduit_sizes", [])

    # -----------------------------------------------------------------------
    # Full Table Access (for /nec-table/{id} endpoint)
    # -----------------------------------------------------------------------
    @classmethod
    def get_table(cls, table_id: str) -> dict | None:
        """Get raw table data by ID for the NEC table lookup endpoint.

        Supported table IDs:
        - '310.16' — Ampacity table
        - 'ch9-conductor-area' — Conductor dimensions
        - 'ch9-conduit-area' — Conduit internal areas
        - 'ch9-resistance' — Conductor DC resistance
        - 'ch9-fill' — Fill percentage rules
        """
        cls._ensure_loaded()
        table_map = {
            "310.16": cls._ampacity_data,
            "ch9-conductor-area": {
                "data": cls._chapter9_data.get("conductor_area_in2", {}),
                "unit": "square inches",
                "insulation_type": "THHN/THWN-2",
            },
            "ch9-conduit-area": {
                "emt": cls._chapter9_data.get("conduit_area_in2", {}),
                "pvc_sch40": cls._chapter9_data.get("conduit_area_pvc_sch40_in2", {}),
                "rigid": cls._chapter9_data.get("conduit_area_rigid_in2", {}),
                "unit": "square inches",
            },
            "ch9-resistance": cls._chapter9_data.get("conductor_resistance_ohms_per_1000ft", {}),
            "ch9-fill": cls._chapter9_data.get("fill_percentages", {}),
        }
        return table_map.get(table_id)
