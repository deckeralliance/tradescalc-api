"""
Tests for the Plumbing Calculations API endpoints.
"""


class TestPipeSizing:
    """Test water supply pipe sizing (velocity method)."""

    def test_copper_10gpm(self, client):
        """10 GPM through copper pipe at max 8 fps.
        Q = 10 GPM × 0.002228 = 0.02228 cfs
        3/4" copper ID = 0.785" → A = π/4 × (0.785/12)² = 0.003357 ft²
        V = 0.02228 / 0.003357 = 6.64 fps → ≤ 8 fps ✓
        Should select 3/4" copper.
        """
        response = client.post(
            "/v1/plumbing/pipe-sizing",
            json={"flow_gpm": 10, "pipe_material": "copper", "max_velocity_fps": 8},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_pipe_size"] == '3/4"'
        assert data["pipe_material"] == "copper"
        assert data["actual_velocity_fps"] <= 8.0
        assert data["inside_diameter_in"] == 0.785

    def test_copper_high_flow(self, client):
        """25 GPM through copper requires at least 1" pipe.
        Q = 25 × 0.002228 = 0.0557 cfs
        1" copper ID = 1.025" → A = π/4 × (1.025/12)² = 0.005731 ft²
        V = 0.0557 / 0.005731 = 9.72 fps → > 8 fps ✗
        1-1/4" ID = 1.265" → A = 0.008726 ft² → V = 6.38 fps → ≤ 8 ✓
        Should select 1-1/4".
        """
        response = client.post(
            "/v1/plumbing/pipe-sizing",
            json={"flow_gpm": 25, "pipe_material": "copper", "max_velocity_fps": 8},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_pipe_size"] == '1-1/4"'
        assert data["actual_velocity_fps"] <= 8.0

    def test_pex_small_flow(self, client):
        """3 GPM through PEX pipe at max 8 fps.
        Q = 3 × 0.002228 = 0.006684 cfs
        1/2" PEX ID = 0.475" → A = π/4 × (0.475/12)² = 0.001230 ft²
        V = 0.006684 / 0.001230 = 5.43 fps → ≤ 8 fps ✓
        Should select 1/2" PEX.
        """
        response = client.post(
            "/v1/plumbing/pipe-sizing",
            json={"flow_gpm": 3, "pipe_material": "pex", "max_velocity_fps": 8},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_pipe_size"] == '1/2"'
        assert data["actual_velocity_fps"] <= 8.0

    def test_hot_water_velocity_limit(self, client):
        """5 fps limit for hot water upsizes the pipe.
        10 GPM at 5 fps max → 3/4" copper at 6.64 fps is too fast.
        Should select 1" copper.
        """
        response = client.post(
            "/v1/plumbing/pipe-sizing",
            json={"flow_gpm": 10, "pipe_material": "copper", "max_velocity_fps": 5},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_pipe_size"] == '1"'
        assert data["actual_velocity_fps"] <= 5.0

    def test_invalid_material(self, client):
        """Invalid pipe material returns 400."""
        response = client.post(
            "/v1/plumbing/pipe-sizing",
            json={"flow_gpm": 10, "pipe_material": "plastic", "max_velocity_fps": 8},
        )
        assert response.status_code == 400

    def test_negative_flow_returns_422(self, client):
        """Negative flow_gpm should fail validation."""
        response = client.post(
            "/v1/plumbing/pipe-sizing",
            json={"flow_gpm": -5, "pipe_material": "copper"},
        )
        assert response.status_code == 422


class TestDWVSizing:
    """Test DWV (drain/waste/vent) pipe sizing."""

    def test_building_drain_30_dfu(self, client):
        """30 DFU on building drain → 2" handles up to 21 DFU (too small),
        3" handles up to 42 DFU ✓. Should select 3".
        Ref: UPC Table 703.2
        """
        response = client.post(
            "/v1/plumbing/dwv-sizing",
            json={"total_dfu": 30, "pipe_type": "building_drain"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["minimum_pipe_size"] == '3"'
        assert data["total_dfu"] == 30
        assert data["pipe_type"] == "building_drain"

    def test_building_sewer_100_dfu(self, client):
        """100 DFU on building sewer → 3" handles 42 (too small),
        4" handles 216 ✓. Should select 4".
        """
        response = client.post(
            "/v1/plumbing/dwv-sizing",
            json={"total_dfu": 100, "pipe_type": "building_sewer"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["minimum_pipe_size"] == '4"'

    def test_vent_stack_small(self, client):
        """5 DFU on vent stack → 1-1/4" handles up to 8 DFU ✓."""
        response = client.post(
            "/v1/plumbing/dwv-sizing",
            json={"total_dfu": 5, "pipe_type": "vent_stack"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["minimum_pipe_size"] == '1-1/4"'
        assert data["slope_per_foot"] == "N/A"

    def test_branch_small(self, client):
        """2 DFU on branch → 1-1/4" handles 1 (too small),
        1-1/2" handles 3 ✓. Should select 1-1/2".
        """
        response = client.post(
            "/v1/plumbing/dwv-sizing",
            json={"total_dfu": 2, "pipe_type": "branch"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["minimum_pipe_size"] == '1-1/2"'

    def test_invalid_pipe_type(self, client):
        """Invalid pipe type returns 400."""
        response = client.post(
            "/v1/plumbing/dwv-sizing",
            json={"total_dfu": 10, "pipe_type": "storm_drain"},
        )
        assert response.status_code == 400

    def test_exceeds_capacity(self, client):
        """1000 DFU exceeds building sewer 6" capacity (720 DFU) → 400."""
        response = client.post(
            "/v1/plumbing/dwv-sizing",
            json={"total_dfu": 1000, "pipe_type": "building_sewer"},
        )
        assert response.status_code == 400


class TestFixtureUnits:
    """Test fixture unit calculations."""

    def test_typical_residential(self, client):
        """Typical 3 bed / 2 bath home fixture load.
        2 toilets: 2 × 2.5 WSFU = 5.0, 2 × 4 DFU = 8
        2 lavatories: 2 × 1.0 = 2.0 WSFU, 2 × 1 = 2 DFU
        1 bathtub: 4.0 WSFU, 2 DFU
        1 kitchen sink: 1.5 WSFU, 2 DFU
        1 dishwasher: 1.5 WSFU, 2 DFU
        1 washing machine: 4.0 WSFU, 3 DFU
        Total WSFU = 18.0, Total DFU = 19.0
        """
        response = client.post(
            "/v1/plumbing/fixture-units",
            json={
                "fixtures": [
                    {"type": "toilet_flush_tank", "count": 2},
                    {"type": "lavatory", "count": 2},
                    {"type": "bathtub", "count": 1},
                    {"type": "kitchen_sink", "count": 1},
                    {"type": "dishwasher", "count": 1},
                    {"type": "washing_machine", "count": 1},
                ]
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_wsfu"] == 18.0
        assert data["total_dfu"] == 19.0
        assert len(data["fixtures_detail"]) == 6

    def test_single_fixture(self, client):
        """Single toilet: 2.5 WSFU, 4 DFU."""
        response = client.post(
            "/v1/plumbing/fixture-units",
            json={"fixtures": [{"type": "toilet_flush_tank", "count": 1}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_wsfu"] == 2.5
        assert data["total_dfu"] == 4.0

    def test_hose_bibb_no_dfu(self, client):
        """Hose bibb contributes WSFU but 0 DFU (not connected to DWV)."""
        response = client.post(
            "/v1/plumbing/fixture-units",
            json={"fixtures": [{"type": "hose_bibb", "count": 2}]},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total_wsfu"] == 5.0
        assert data["total_dfu"] == 0.0

    def test_invalid_fixture_type(self, client):
        """Unknown fixture type returns 400."""
        response = client.post(
            "/v1/plumbing/fixture-units",
            json={"fixtures": [{"type": "hot_tub", "count": 1}]},
        )
        assert response.status_code == 400

    def test_empty_fixtures_returns_422(self, client):
        """Empty fixtures list should fail validation (min_length=1)."""
        response = client.post(
            "/v1/plumbing/fixture-units",
            json={"fixtures": []},
        )
        assert response.status_code == 422


class TestWaterHeaterSizing:
    """Test water heater sizing."""

    def test_3bed_2bath_gas(self, client):
        """3 bedroom / 2 bath gas → 50 gallon tank.
        Recovery: gas = 40 GPH. First hour = 50 + 40 = 90 GPH.
        """
        response = client.post(
            "/v1/plumbing/water-heater-sizing",
            json={"num_bedrooms": 3, "num_bathrooms": 2, "fuel_type": "gas"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_tank_gallons"] == 50
        assert data["first_hour_rating_gph"] == 90
        assert data["recovery_rate_gph"] == 40
        assert data["fuel_type"] == "gas"

    def test_1bed_1bath_electric(self, client):
        """1 bedroom / 1 bath electric → 30 gallon tank.
        Recovery: electric = 21 GPH. First hour = 30 + 21 = 51 GPH.
        """
        response = client.post(
            "/v1/plumbing/water-heater-sizing",
            json={"num_bedrooms": 1, "num_bathrooms": 1, "fuel_type": "electric"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_tank_gallons"] == 30
        assert data["first_hour_rating_gph"] == 51
        assert data["recovery_rate_gph"] == 21

    def test_5bed_3bath_heat_pump(self, client):
        """5 bedroom / 3 bath heat pump → 66 gallon tank.
        Recovery: heat_pump = 10 GPH. First hour = 66 + 10 = 76 GPH.
        """
        response = client.post(
            "/v1/plumbing/water-heater-sizing",
            json={"num_bedrooms": 5, "num_bathrooms": 3, "fuel_type": "heat_pump"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["recommended_tank_gallons"] == 66
        assert data["first_hour_rating_gph"] == 76

    def test_invalid_fuel_type(self, client):
        """Invalid fuel type returns 400."""
        response = client.post(
            "/v1/plumbing/water-heater-sizing",
            json={"num_bedrooms": 3, "num_bathrooms": 2, "fuel_type": "propane"},
        )
        assert response.status_code == 400

    def test_zero_bedrooms_returns_422(self, client):
        """0 bedrooms should fail validation (ge=1)."""
        response = client.post(
            "/v1/plumbing/water-heater-sizing",
            json={"num_bedrooms": 0, "num_bathrooms": 1, "fuel_type": "gas"},
        )
        assert response.status_code == 422


class TestPlumbingFrictionLoss:
    """Test Hazen-Williams friction loss for plumbing pipe."""

    def test_copper_3_4_inch(self, client):
        """10 GPM through 3/4" copper (ID=0.785"), 100 ft, C=150.
        hf/ft = 4.52 × 10^1.85 / (150^1.85 × 0.785^4.87) = known value
        Velocity = 0.02228 / (π/4 × (0.785/12)²) = ~6.64 fps
        Result should be positive and reasonable.
        """
        response = client.post(
            "/v1/plumbing/friction-loss",
            json={
                "flow_gpm": 10,
                "pipe_diameter_in": 0.785,
                "pipe_length_ft": 100,
                "c_factor": 150,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["friction_loss_psi"] > 0
        assert data["friction_loss_psi_per_100ft"] > 0
        assert 5.0 < data["velocity_fps"] < 8.0  # ~6.64 fps expected
        assert data["flow_gpm"] == 10

    def test_galvanized_higher_loss(self, client):
        """Lower C-factor (galvanized=120) should produce higher friction loss
        than copper (C=150) for the same flow and diameter.
        """
        resp_copper = client.post(
            "/v1/plumbing/friction-loss",
            json={"flow_gpm": 10, "pipe_diameter_in": 0.785, "pipe_length_ft": 100, "c_factor": 150},
        )
        resp_galv = client.post(
            "/v1/plumbing/friction-loss",
            json={"flow_gpm": 10, "pipe_diameter_in": 0.785, "pipe_length_ft": 100, "c_factor": 120},
        )
        assert resp_copper.status_code == 200
        assert resp_galv.status_code == 200
        assert resp_galv.json()["friction_loss_psi"] > resp_copper.json()["friction_loss_psi"]

    def test_longer_pipe_more_loss(self, client):
        """200 ft should have exactly 2× the friction loss of 100 ft."""
        resp_100 = client.post(
            "/v1/plumbing/friction-loss",
            json={"flow_gpm": 10, "pipe_diameter_in": 0.785, "pipe_length_ft": 100, "c_factor": 150},
        )
        resp_200 = client.post(
            "/v1/plumbing/friction-loss",
            json={"flow_gpm": 10, "pipe_diameter_in": 0.785, "pipe_length_ft": 200, "c_factor": 150},
        )
        assert resp_100.status_code == 200
        assert resp_200.status_code == 200
        loss_100 = resp_100.json()["friction_loss_psi"]
        loss_200 = resp_200.json()["friction_loss_psi"]
        assert abs(loss_200 - 2 * loss_100) < 0.01


class TestGasPipeSizing:
    """Test natural gas pipe sizing."""

    def test_furnace_100k_30ft(self, client):
        """100,000 BTU/hr furnace, 30 ft run.
        IFGC Table 402.4: 1/2" at 30ft = 97,000 BTU/hr (not enough).
        3/4" at 30ft = 199,000 BTU/hr ✓. Should select 3/4".
        """
        response = client.post(
            "/v1/plumbing/gas-pipe-sizing",
            json={"total_btuh": 100000, "pipe_length_ft": 30},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["minimum_pipe_size"] == '3/4"'
        assert data["capacity_btuh"] >= 100000

    def test_small_load_short_run(self, client):
        """30,000 BTU/hr water heater, 10 ft run.
        1/2" at 10ft = 175,000 BTU/hr ✓. Should select 1/2".
        """
        response = client.post(
            "/v1/plumbing/gas-pipe-sizing",
            json={"total_btuh": 30000, "pipe_length_ft": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["minimum_pipe_size"] == '1/2"'

    def test_large_load_long_run(self, client):
        """500,000 BTU/hr total load, 100 ft run.
        1" at 100ft = 195,000 (too small).
        1-1/4" at 100ft = 400,000 (too small).
        1-1/2" at 100ft = 615,000 ✓. Should select 1-1/2".
        """
        response = client.post(
            "/v1/plumbing/gas-pipe-sizing",
            json={"total_btuh": 500000, "pipe_length_ft": 100},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["minimum_pipe_size"] == '1-1/2"'
        assert data["capacity_btuh"] >= 500000

    def test_200k_60ft(self, client):
        """200,000 BTU/hr, 60 ft run.
        3/4" at 60ft = 137,000 (not enough).
        1" at 60ft = 257,000 ✓. Should select 1".
        """
        response = client.post(
            "/v1/plumbing/gas-pipe-sizing",
            json={"total_btuh": 200000, "pipe_length_ft": 60},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["minimum_pipe_size"] == '1"'
        assert data["capacity_btuh"] >= 200000


class TestFixtureUnitTable:
    """Test fixture unit reference table."""

    def test_get_table(self, client):
        """Should return all 8 fixture types."""
        response = client.get("/v1/plumbing/fixture-unit-table")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 8
        # Verify toilet values — UPC Table 702.1
        types_dict = {entry["fixture_type"]: entry for entry in data}
        assert "toilet_flush_tank" in types_dict
        assert types_dict["toilet_flush_tank"]["wsfu"] == 2.5
        assert types_dict["toilet_flush_tank"]["dfu"] == 4


class TestPipeMaterials:
    """Test pipe materials reference table."""

    def test_get_materials(self, client):
        """Should return 5 pipe materials with properties."""
        response = client.get("/v1/plumbing/pipe-materials")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 5
        # Verify copper C-factor
        mats_dict = {entry["material"]: entry for entry in data}
        assert mats_dict["copper"]["c_factor"] == 150
        assert mats_dict["galvanized"]["c_factor"] == 120
        assert mats_dict["cast_iron"]["c_factor"] == 100


class TestPlumbingInfo:
    """Test plumbing module info endpoint."""

    def test_get_info(self, client):
        """Should return module metadata and endpoint listing."""
        response = client.get("/v1/plumbing/info")
        assert response.status_code == 200
        data = response.json()
        assert data["module"] == "Plumbing — Calculations"
        assert "UPC" in str(data["standards"])
        assert len(data["endpoints"]) == 9
