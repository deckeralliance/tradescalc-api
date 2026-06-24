"""
Tests for the Electrical API endpoints.

These tests validate NEC calculations against known correct values.
Cross-reference with your NEC codebook to verify.
"""


class TestHealthAndRoot:
    """Test system endpoints."""

    def test_health_check(self, client):
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_root(self, client):
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "modules" in data
        assert "electrical" in data["modules"]


class TestAmpacity:
    """Test ampacity lookups against NEC Table 310.16."""

    def test_copper_12awg_75c(self, client):
        """12 AWG copper at 75°C should be 20A."""
        response = client.post(
            "/v1/electrical/ampacity",
            json={"wire_size": "12", "material": "copper", "temp_rating": "75"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["ampacity"] == 20

    def test_copper_4awg_75c(self, client):
        """4 AWG copper at 75°C should be 85A."""
        response = client.post(
            "/v1/electrical/ampacity",
            json={"wire_size": "4", "material": "copper", "temp_rating": "75"},
        )
        assert response.status_code == 200
        assert response.json()["ampacity"] == 85

    def test_copper_2_0_90c(self, client):
        """2/0 AWG copper at 90°C should be 195A."""
        response = client.post(
            "/v1/electrical/ampacity",
            json={"wire_size": "2/0", "material": "copper", "temp_rating": "90"},
        )
        assert response.status_code == 200
        assert response.json()["ampacity"] == 195

    def test_aluminum_4_0_75c(self, client):
        """4/0 AWG aluminum at 75°C should be 180A."""
        response = client.post(
            "/v1/electrical/ampacity",
            json={"wire_size": "4/0", "material": "aluminum", "temp_rating": "75"},
        )
        assert response.status_code == 200
        assert response.json()["ampacity"] == 180

    def test_invalid_wire_size(self, client):
        """Invalid wire size should return 400 or appropriate error."""
        response = client.post(
            "/v1/electrical/ampacity",
            json={"wire_size": "99", "material": "copper", "temp_rating": "75"},
        )
        assert response.status_code in [400, 404, 422]


class TestVoltageDrop:
    """Test voltage drop calculations."""

    def test_basic_voltage_drop_120v(self, client):
        """20A load on 12 AWG copper, 100ft, 120V single phase.
        Expected: Vd = (2 * 1.98 * 20 * 100) / 1000 = 7.92V = 6.6%
        """
        response = client.post(
            "/v1/electrical/voltage-drop",
            json={
                "load_amps": 20,
                "distance_ft": 100,
                "wire_size": "12",
                "voltage": 120,
                "phase": "single",
                "material": "copper",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert 7.5 < data["drop_volts"] < 8.5  # ~7.92V
        assert 6.0 < data["drop_percent"] < 7.0  # ~6.6%
        assert data["passes_3_percent_rule"] is False

    def test_acceptable_voltage_drop(self, client):
        """10A load on 10 AWG copper, 50ft, 120V — should pass 3% rule.
        Vd = (2 * 1.24 * 10 * 50) / 1000 = 1.24V = 1.03%
        """
        response = client.post(
            "/v1/electrical/voltage-drop",
            json={
                "load_amps": 10,
                "distance_ft": 50,
                "wire_size": "10",
                "voltage": 120,
                "phase": "single",
                "material": "copper",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["passes_3_percent_rule"] is True

    def test_three_phase_voltage_drop(self, client):
        """Three-phase should use sqrt(3) multiplier instead of 2."""
        response = client.post(
            "/v1/electrical/voltage-drop",
            json={
                "load_amps": 50,
                "distance_ft": 200,
                "wire_size": "6",
                "voltage": 480,
                "phase": "three",
                "material": "copper",
            },
        )
        assert response.status_code == 200
        data = response.json()
        # Three-phase Vd = (sqrt(3) * 0.491 * 50 * 200) / 1000 = 8.51V = 1.77%
        assert data["passes_3_percent_rule"] is True


class TestConduitFill:
    """Test conduit fill calculations."""

    def test_three_12awg_in_emt(self, client):
        """Three 12 AWG THHN in EMT — should fit in 1/2" EMT.
        Area per conductor: 0.0133 in². Total: 0.0399 in²
        1/2" EMT area: 0.304 in². 40% fill = 0.1216 in². 0.0399 < 0.1216 ✓
        """
        response = client.post(
            "/v1/electrical/conduit-fill",
            json={"conductors": [{"wire_size": "12", "count": 3}], "conduit_type": "emt"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["min_conduit_size"] == "1/2"

    def test_many_conductors_larger_conduit(self, client):
        """Nine 10 AWG THHN should need at least 3/4" EMT.
        Area per conductor: 0.0211 in². Total: 0.1899 in²
        3/4" EMT: 0.533 in². 40% = 0.2132 in². 0.1899 < 0.2132 ✓
        """
        response = client.post(
            "/v1/electrical/conduit-fill",
            json={"conductors": [{"wire_size": "10", "count": 9}], "conduit_type": "emt"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["min_conduit_size"] in ["3/4", "1"]


class TestBreakerSize:
    """Test breaker sizing calculations."""

    def test_continuous_load(self, client):
        """40A continuous load → 40 * 1.25 = 50A → next standard = 50A breaker."""
        response = client.post("/v1/electrical/breaker-size", json={"load_amps": 40, "continuous": True})
        assert response.status_code == 200
        data = response.json()
        assert data["standard_breaker_amps"] == 50

    def test_non_continuous_load(self, client):
        """40A non-continuous → 40A → next standard = 40A breaker."""
        response = client.post("/v1/electrical/breaker-size", json={"load_amps": 40, "continuous": False})
        assert response.status_code == 200
        data = response.json()
        assert data["standard_breaker_amps"] == 40

    def test_odd_load_rounds_up(self, client):
        """33A non-continuous → next standard = 35A breaker."""
        response = client.post("/v1/electrical/breaker-size", json={"load_amps": 33, "continuous": False})
        assert response.status_code == 200
        data = response.json()
        assert data["standard_breaker_amps"] == 35


class TestTransformerSizing:
    """Test transformer sizing calculations."""

    def test_basic_transformer(self, client):
        """24,000 VA load → 24 kVA → next standard = 25 kVA."""
        response = client.post(
            "/v1/electrical/transformer-sizing",
            json={"load_va": 24000, "voltage_primary": 480, "voltage_secondary": 208},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["standard_kva"] == 25

    def test_small_transformer(self, client):
        """4,000 VA → 4 kVA → next standard = 5 kVA."""
        response = client.post(
            "/v1/electrical/transformer-sizing",
            json={"load_va": 4000, "voltage_primary": 480, "voltage_secondary": 120},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["standard_kva"] == 5


class TestNECTableLookup:
    """Test raw NEC table data retrieval."""

    def test_get_ampacity_table(self, client):
        response = client.get("/v1/electrical/nec-table/310.16")
        assert response.status_code == 200
        data = response.json()
        assert "copper" in data["data"]

    def test_get_conduit_table(self, client):
        response = client.get("/v1/electrical/nec-table/ch9-conduit-area")
        assert response.status_code == 200

    def test_invalid_table_id(self, client):
        response = client.get("/v1/electrical/nec-table/nonexistent")
        assert response.status_code == 404
