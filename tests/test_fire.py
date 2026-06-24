"""
Tests for the Fire Protection API endpoints.
"""


class TestHydrantFlow:
    """Test hydrant flow calculations."""

    def test_basic_hydrant_flow(self, client):
        """Standard flow test: 60 psi static, 40 psi residual, 800 GPM measured.
        Available at 20 psi = 800 * ((60-20)/(60-40))^0.54
        = 800 * (40/20)^0.54 = 800 * 2^0.54 = 800 * 1.454 ≈ 1163 GPM
        """
        response = client.post(
            "/v1/fire/hydrant-flow",
            json={
                "static_pressure_psi": 60,
                "residual_pressure_psi": 40,
                "flow_at_residual_gpm": 800,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert 1100 < data["available_flow_at_20psi_gpm"] < 1250

    def test_low_pressure_hydrant(self, client):
        """Low pressure scenario: 35 psi static, 25 psi residual, 500 GPM.
        Available at 20 psi = 500 * ((35-20)/(35-25))^0.54 ≈ 500 * 1.277 ≈ 638 GPM
        """
        response = client.post(
            "/v1/fire/hydrant-flow",
            json={
                "static_pressure_psi": 35,
                "residual_pressure_psi": 25,
                "flow_at_residual_gpm": 500,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert 600 < data["available_flow_at_20psi_gpm"] < 700


class TestFrictionLoss:
    """Test friction loss calculations."""

    def test_2_5_inch_hose(self, client):
        """Friction loss through 2.5" hose at 250 GPM, 200ft, C=120."""
        response = client.post(
            "/v1/fire/friction-loss",
            json={"flow_gpm": 250, "hose_diameter_inches": 2.5, "length_ft": 200, "c_factor": 120},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["friction_loss_psi"] > 0
        assert data["friction_loss_per_100ft"] > 0


class TestPumpPressure:
    """Test pump pressure calculations."""

    def test_basic_pump_pressure(self, client):
        """NP=100, FL=30, Elevation=20ft (8.68 psi), no appliance.
        PDP = 100 + 30 + 8.68 + 0 = 138.68 psi
        """
        response = client.post(
            "/v1/fire/pump-pressure",
            json={
                "nozzle_pressure_psi": 100,
                "friction_loss_psi": 30,
                "elevation_ft": 20,
                "appliance_loss_psi": 0,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert 135 < data["engine_pressure_psi"] < 142


class TestNeededFireFlow:
    """Test needed fire flow calculations."""

    def test_small_commercial(self, client):
        """5,000 sqft Class 3 (ordinary) building.
        NFF = 18 * 1.0 * sqrt(5000) = 18 * 70.71 = 1272.8 GPM
        """
        response = client.post("/v1/fire/needed-fire-flow", json={"area_sqft": 5000, "construction_class": 3})
        assert response.status_code == 200
        data = response.json()
        assert 1200 < data["needed_fire_flow_gpm"] < 1400

    def test_minimum_cap(self, client):
        """Very small building should cap at minimum 500 GPM."""
        response = client.post("/v1/fire/needed-fire-flow", json={"area_sqft": 100, "construction_class": 6})
        assert response.status_code == 200
        data = response.json()
        assert data["needed_fire_flow_gpm"] >= 500


class TestNERISCodes:
    """Test NERIS code lookup."""

    def test_get_neris_codes(self, client):
        response = client.get("/v1/fire/neris-codes")
        assert response.status_code == 200
        data = response.json()
        assert len(data) > 0
        # Check that structure fire code exists
        codes_dict = {c["code"]: c for c in data}
        assert "111" in codes_dict


class TestISOGrading:
    """Test ISO grading factors."""

    def test_get_iso_grading(self, client):
        response = client.get("/v1/fire/iso-grading")
        assert response.status_code == 200
        data = response.json()
        # Categories is a list of objects with category, max_points, percentage_of_total
        categories = {c["category"]: c for c in data["categories"]}
        assert categories["Fire Department"]["percentage_of_total"] == 50
        assert categories["Water Supply"]["percentage_of_total"] == 40
        assert data["total_possible"] == 105.5
