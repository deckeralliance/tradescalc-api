"""
Tests for the Utility API endpoints (IEEE 1366 reliability indices).
"""

import math


class TestReliabilityIndices:
    """Test SAIDI, SAIFI, CAIDI calculations."""

    def test_basic_reliability(self, client):
        """Simple scenario: 2 outages, 10,000 customers served.
        Outage 1: 500 customers, 120 min
        Outage 2: 200 customers, 60 min
        SAIDI = (500*120 + 200*60) / 10000 = 72000/10000 = 7.2 min
        SAIFI = (500 + 200) / 10000 = 0.07
        CAIDI = 7.2 / 0.07 = 102.86 min
        """
        response = client.post("/v1/utility/reliability", json={
            "outage_events": [
                {"customers_affected": 500, "duration_minutes": 120},
                {"customers_affected": 200, "duration_minutes": 60},
            ],
            "total_customers_served": 10000
        })
        assert response.status_code == 200
        data = response.json()
        assert abs(data["saidi"] - 7.2) < 0.01
        assert abs(data["saifi"] - 0.07) < 0.001
        assert abs(data["caidi"] - 102.86) < 0.1

    def test_single_outage(self, client):
        """Single outage: 1000 customers, 60 min, 5000 served.
        SAIDI = 60000/5000 = 12.0
        SAIFI = 1000/5000 = 0.2
        CAIDI = 12.0/0.2 = 60.0
        """
        response = client.post("/v1/utility/reliability", json={
            "outage_events": [
                {"customers_affected": 1000, "duration_minutes": 60},
            ],
            "total_customers_served": 5000
        })
        assert response.status_code == 200
        data = response.json()
        assert data["saidi"] == 12.0
        assert data["saifi"] == 0.2
        assert data["caidi"] == 60.0


class TestOutageCost:
    """Test outage cost estimation."""

    def test_residential_outage_cost(self, client):
        """Pure residential outage: 1000 customers, 2 hours.
        Cost ≈ 1000 * 2 * $3.50 = $7,000
        """
        response = client.post("/v1/utility/outage-cost", json={
            "customers_affected": 1000,
            "duration_hours": 2.0,
            "customer_mix": {
                "residential_pct": 100,
                "commercial_pct": 0,
                "industrial_pct": 0
            }
        })
        assert response.status_code == 200
        data = response.json()
        assert 6000 < data["estimated_cost_usd"] < 8000

    def test_mixed_outage_cost(self, client):
        """Mixed customer base should cost more than pure residential."""
        response = client.post("/v1/utility/outage-cost", json={
            "customers_affected": 1000,
            "duration_hours": 2.0,
            "customer_mix": {
                "residential_pct": 70,
                "commercial_pct": 25,
                "industrial_pct": 5
            }
        })
        assert response.status_code == 200
        data = response.json()
        # Industrial at $3000/hr makes this much higher
        assert data["estimated_cost_usd"] > 10000


class TestBenchmark:
    """Test reliability benchmark data."""

    def test_get_benchmarks(self, client):
        response = client.get("/v1/utility/benchmark")
        assert response.status_code == 200
        data = response.json()
        # Benchmark returns with/without MED averages and by utility type
        assert "with_major_event_days" in data or "national_averages" in data
        assert "by_utility_type" in data
