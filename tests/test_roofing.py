"""
Tests for the Roofing Calculations API endpoints.
"""

import math


class TestPitch:
    """Test roof pitch / slope calculations."""

    def test_standard_6_12_pitch(self, client):
        """6:12 pitch — most common steep residential.
        slope_deg = atan(6/12) × 180/π = 26.57°
        slope_pct = 6/12 × 100 = 50%
        pitch_factor = sqrt(1 + (6/12)^2) = sqrt(1.25) = 1.118
        """
        response = client.post("/v1/roofing/pitch", json={"rise_inches": 6})
        assert response.status_code == 200
        data = response.json()
        assert data["pitch_ratio"] == "6:12"
        assert data["slope_degrees"] == round(math.degrees(math.atan(6 / 12)), 2)  # 26.57
        assert data["slope_percent"] == 50.0
        assert data["pitch_factor"] == round(math.sqrt(1.25), 3)  # 1.118

    def test_4_12_standard_residential(self, client):
        """4:12 pitch — standard residential.
        pitch_factor = sqrt(1 + (4/12)^2) = sqrt(1 + 0.1111) = sqrt(1.1111) = 1.054
        """
        response = client.post("/v1/roofing/pitch", json={"rise_inches": 4})
        assert response.status_code == 200
        data = response.json()
        assert data["pitch_ratio"] == "4:12"
        assert data["pitch_factor"] == round(math.sqrt(1 + (4 / 12) ** 2), 3)  # 1.054

    def test_12_12_pitch(self, client):
        """12:12 pitch = 45 degrees.
        pitch_factor = sqrt(1 + 1) = sqrt(2) = 1.414
        """
        response = client.post("/v1/roofing/pitch", json={"rise_inches": 12})
        assert response.status_code == 200
        data = response.json()
        assert data["pitch_ratio"] == "12:12"
        assert data["slope_degrees"] == 45.0
        assert data["slope_percent"] == 100.0
        assert data["pitch_factor"] == round(math.sqrt(2), 3)  # 1.414

    def test_pitch_from_rise_run_ft(self, client):
        """8 ft rise over 16 ft run = 6:12 pitch.
        rise_per_12 = (8/16) × 12 = 6
        """
        response = client.post(
            "/v1/roofing/pitch",
            json={"rise_ft": 8, "run_ft": 16},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["pitch_ratio"] == "6:12"
        assert data["pitch_factor"] == round(math.sqrt(1.25), 3)

    def test_pitch_missing_inputs(self, client):
        """No rise_inches and no rise_ft+run_ft → 400."""
        response = client.post("/v1/roofing/pitch", json={"rise_ft": 8})
        assert response.status_code == 400

    def test_pitch_invalid_rise(self, client):
        """Negative rise → 422 validation error."""
        response = client.post("/v1/roofing/pitch", json={"rise_inches": -3})
        assert response.status_code == 422

    def test_3_12_pitch_factor(self, client):
        """3:12 pitch — minimum for shingles.
        pitch_factor = sqrt(1 + (3/12)^2) = sqrt(1.0625) = 1.031
        """
        response = client.post("/v1/roofing/pitch", json={"rise_inches": 3})
        assert response.status_code == 200
        data = response.json()
        assert data["pitch_factor"] == round(math.sqrt(1 + (3 / 12) ** 2), 3)  # 1.031


class TestArea:
    """Test roof area calculations."""

    def test_area_from_footprint_sqft(self, client):
        """2000 sqft footprint, 6:12 pitch, 10% waste.
        pitch_factor = 1.118
        roof_area = 2000 × 1.118 = 2236.0
        total_with_waste = 2236.0 × 1.10 = 2459.6
        """
        response = client.post(
            "/v1/roofing/area",
            json={"footprint_sqft": 2000, "pitch_rise": 6, "waste_percent": 10},
        )
        assert response.status_code == 200
        data = response.json()
        pf = round(math.sqrt(1.25), 3)
        assert data["pitch_factor"] == pf
        assert data["footprint_sqft"] == 2000.0
        # Router computes 2000 * sqrt(1.25) then rounds to 2 dp
        full_area = 2000.0 * math.sqrt(1.25)
        expected_area = round(full_area, 2)
        assert data["roof_area_sqft"] == expected_area
        assert data["waste_factor"] == 1.10
        # Router computes total_with_waste from the full-precision roof_area, then rounds
        assert data["total_with_waste_sqft"] == round(full_area * 1.10, 2)

    def test_area_from_length_width(self, client):
        """50 ft × 40 ft = 2000 sqft footprint, 4:12 pitch.
        pitch_factor = 1.054
        roof_area = 2000 × 1.054 = 2108.0
        """
        response = client.post(
            "/v1/roofing/area",
            json={"footprint_length_ft": 50, "footprint_width_ft": 40, "pitch_rise": 4},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["footprint_sqft"] == 2000.0
        pf = round(math.sqrt(1 + (4 / 12) ** 2), 3)
        assert data["pitch_factor"] == pf

    def test_area_missing_footprint(self, client):
        """No footprint_sqft and no length+width → 400."""
        response = client.post(
            "/v1/roofing/area",
            json={"pitch_rise": 6},
        )
        assert response.status_code == 400

    def test_area_zero_waste(self, client):
        """0% waste → waste_factor should be 1.0."""
        response = client.post(
            "/v1/roofing/area",
            json={"footprint_sqft": 1000, "pitch_rise": 4, "waste_percent": 0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["waste_factor"] == 1.0
        assert data["roof_area_sqft"] == data["total_with_waste_sqft"]


class TestMaterials:
    """Test roofing materials estimation."""

    def test_asphalt_shingle_basic(self, client):
        """2400 sqft area, asphalt shingle, 10% waste.
        squares = (2400/100) × 1.10 = 26.4
        bundles = 26.4 × 3 = 79.2
        underlayment_rolls = ceil(26.4 / 4) = 7
        nails = 26.4 × 2.5 = 66.0 lbs
        """
        response = client.post(
            "/v1/roofing/materials",
            json={"roof_area_sqft": 2400, "material_type": "asphalt_shingle"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["squares"] == 26.4
        assert data["bundles"] == 79.2
        assert data["underlayment_rolls"] == 7
        assert data["nails_lbs"] == 66.0

    def test_cedar_shake(self, client):
        """1500 sqft area, cedar shake, 10% waste.
        squares = (1500/100) × 1.10 = 16.5
        bundles = 16.5 × 4 = 66.0
        nails = 16.5 × 3.0 = 49.5 lbs
        """
        response = client.post(
            "/v1/roofing/materials",
            json={"roof_area_sqft": 1500, "material_type": "cedar_shake"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["squares"] == 16.5
        assert data["bundles"] == 66.0
        assert data["nails_lbs"] == 49.5

    def test_materials_with_custom_ridge_eave(self, client):
        """User-supplied ridge and eave lengths should be used directly."""
        response = client.post(
            "/v1/roofing/materials",
            json={
                "roof_area_sqft": 2000,
                "material_type": "architectural_shingle",
                "ridge_length_ft": 60,
                "eave_length_ft": 200,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ridge_cap_lf"] == 60.0
        assert data["drip_edge_lf"] == 200.0
        assert data["starter_strip_lf"] == 200.0

    def test_materials_invalid_type(self, client):
        """Invalid material type → 400."""
        response = client.post(
            "/v1/roofing/materials",
            json={"roof_area_sqft": 2000, "material_type": "rubber_membrane"},
        )
        assert response.status_code == 400

    def test_materials_zero_waste(self, client):
        """0% waste → squares = area / 100 exactly."""
        response = client.post(
            "/v1/roofing/materials",
            json={"roof_area_sqft": 3000, "material_type": "metal_panel", "waste_percent": 0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["squares"] == 30.0
        assert data["bundles"] == 30.0  # metal: 1 per square


class TestRafterLength:
    """Test rafter length calculations."""

    def test_rafter_6_12_pitch(self, client):
        """12 ft run, 6:12 pitch, 12" overhang.
        pitch_factor = 1.118
        theoretical = 12 × 1.118 = 13.42 ft
        overhang = (12/12) × 1.118 = 1.12 ft
        total = 13.42 + 1.12 = 14.54 ft
        """
        response = client.post(
            "/v1/roofing/rafter-length",
            json={"run_ft": 12, "pitch_rise": 6, "overhang_inches": 12},
        )
        assert response.status_code == 200
        data = response.json()
        pf = round(math.sqrt(1.25), 3)  # 1.118
        assert data["pitch_ratio"] == "6:12"
        assert data["pitch_factor"] == pf
        # Router uses full-precision pitch_factor internally, then rounds each result
        full_pf = math.sqrt(1.25)
        expected_theoretical = round(12 * full_pf, 2)
        expected_overhang = round(1.0 * full_pf, 2)
        assert data["theoretical_length_ft"] == expected_theoretical
        assert data["overhang_length_ft"] == expected_overhang
        assert data["total_length_ft"] == round(12 * full_pf + 1.0 * full_pf, 2)

    def test_rafter_no_overhang(self, client):
        """12 ft run, 4:12 pitch, 0" overhang.
        theoretical = total (no overhang contribution).
        """
        response = client.post(
            "/v1/roofing/rafter-length",
            json={"run_ft": 12, "pitch_rise": 4, "overhang_inches": 0},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["overhang_length_ft"] == 0.0
        assert data["theoretical_length_ft"] == data["total_length_ft"]

    def test_rafter_12_12_pitch(self, client):
        """10 ft run, 12:12 pitch (45°), 18" overhang.
        pitch_factor = sqrt(2) = 1.414
        theoretical = 10 × 1.414 = 14.14 ft
        overhang = (18/12) × 1.414 = 2.12 ft
        total = 16.26 ft
        """
        response = client.post(
            "/v1/roofing/rafter-length",
            json={"run_ft": 10, "pitch_rise": 12, "overhang_inches": 18},
        )
        assert response.status_code == 200
        data = response.json()
        pf = round(math.sqrt(2), 3)  # 1.414
        assert data["pitch_factor"] == pf
        expected_theoretical = round(10 * pf, 2)
        expected_overhang = round(1.5 * pf, 2)
        assert data["total_length_ft"] == round(expected_theoretical + expected_overhang, 2)


class TestSnowLoad:
    """Test ASCE 7 snow load calculations."""

    def test_flat_roof_default_factors(self, client):
        """40 psf ground snow load, all factors = 1.0, flat roof (0°).
        pf = 0.7 × 1.0 × 1.0 × 1.0 × 40 = 28.0 psf
        Cs = 1.0 (slope ≤ 30°)
        ps = 1.0 × 28.0 = 28.0 psf
        Source: ASCE 7-22 §7.3, Eq. 7.3-1
        """
        response = client.post(
            "/v1/roofing/snow-load",
            json={"ground_snow_load_psf": 40},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["flat_roof_snow_load_psf"] == 28.0
        assert data["cs_factor"] == 1.0
        assert data["sloped_roof_snow_load_psf"] == 28.0

    def test_snow_load_with_factors(self, client):
        """50 psf, Ce=0.9, Ct=1.1, Is=1.2, flat.
        pf = 0.7 × 0.9 × 1.1 × 1.2 × 50 = 0.7 × 0.9 × 1.1 × 1.2 × 50
           = 0.7 × 59.4 = 41.58 psf
        """
        response = client.post(
            "/v1/roofing/snow-load",
            json={
                "ground_snow_load_psf": 50,
                "exposure_factor": 0.9,
                "thermal_factor": 1.1,
                "importance_factor": 1.2,
            },
        )
        assert response.status_code == 200
        data = response.json()
        expected = round(0.7 * 0.9 * 1.1 * 1.2 * 50, 2)
        assert data["flat_roof_snow_load_psf"] == expected

    def test_snow_load_slope_30_degrees(self, client):
        """Slope = 30° → Cs = 1.0 (boundary, no reduction).
        Source: ASCE 7-22 §7.4
        """
        response = client.post(
            "/v1/roofing/snow-load",
            json={"ground_snow_load_psf": 40, "slope_degrees": 30},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cs_factor"] == 1.0
        assert data["sloped_roof_snow_load_psf"] == 28.0

    def test_snow_load_slope_50_degrees(self, client):
        """Slope = 50° → Cs = 1.0 - (50-30)/40 = 1.0 - 0.5 = 0.5.
        ps = 0.5 × 28.0 = 14.0 psf
        Source: ASCE 7-22 §7.4
        """
        response = client.post(
            "/v1/roofing/snow-load",
            json={"ground_snow_load_psf": 40, "slope_degrees": 50},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cs_factor"] == 0.5
        assert data["sloped_roof_snow_load_psf"] == 14.0

    def test_snow_load_slope_70_degrees(self, client):
        """Slope = 70° → Cs = 1.0 - (70-30)/40 = 0.0.
        ps = 0 psf — snow slides off.
        """
        response = client.post(
            "/v1/roofing/snow-load",
            json={"ground_snow_load_psf": 40, "slope_degrees": 70},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cs_factor"] == 0.0
        assert data["sloped_roof_snow_load_psf"] == 0.0

    def test_snow_load_slope_over_70(self, client):
        """Slope > 70° → Cs = 0, no snow retention."""
        response = client.post(
            "/v1/roofing/snow-load",
            json={"ground_snow_load_psf": 40, "slope_degrees": 80},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["cs_factor"] == 0.0
        assert data["sloped_roof_snow_load_psf"] == 0.0


class TestPitchReference:
    """Test pitch reference table endpoint."""

    def test_get_pitch_reference(self, client):
        """Verify reference table returns all standard pitches."""
        response = client.get("/v1/roofing/pitch-reference")
        assert response.status_code == 200
        data = response.json()
        pitches = {p["pitch_ratio"]: p for p in data["pitches"]}
        # Verify known values
        assert "4:12" in pitches
        assert "6:12" in pitches
        assert "12:12" in pitches
        # 12:12 should be 45 degrees
        assert pitches["12:12"]["slope_degrees"] == 45.0
        # 4:12 pitch factor = 1.054
        assert pitches["4:12"]["pitch_factor"] == round(math.sqrt(1 + (4 / 12) ** 2), 3)

    def test_pitch_reference_count(self, client):
        """Table should include 11 standard pitches (1:12 through 10:12, then 12:12)."""
        response = client.get("/v1/roofing/pitch-reference")
        assert response.status_code == 200
        data = response.json()
        assert len(data["pitches"]) == 11

    def test_pitch_reference_has_suitability(self, client):
        """Each pitch entry should have a suitability note."""
        response = client.get("/v1/roofing/pitch-reference")
        assert response.status_code == 200
        data = response.json()
        for pitch in data["pitches"]:
            assert "suitability" in pitch
            assert len(pitch["suitability"]) > 0


class TestRoofingInfo:
    """Test roofing module info endpoint."""

    def test_get_info(self, client):
        """Info endpoint should return module name and endpoints list."""
        response = client.get("/v1/roofing/info")
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "Roofing — Calculations"
        assert "ASCE 7-22" in data["standards"]
        assert len(data["endpoints"]) == 7

    def test_info_endpoints_have_paths(self, client):
        """Each endpoint entry should have path, method, and summary."""
        response = client.get("/v1/roofing/info")
        assert response.status_code == 200
        data = response.json()
        for ep in data["endpoints"]:
            assert "path" in ep
            assert "method" in ep
            assert "summary" in ep
