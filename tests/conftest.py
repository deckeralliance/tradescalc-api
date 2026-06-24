"""
Shared test fixtures for TradesCalc API test suite.
"""

import pytest
from fastapi.testclient import TestClient

from tradescalc.main import app
from tradescalc.services.nec_data import NECDataStore


@pytest.fixture(scope="session", autouse=True)
def load_nec_data():
    """Load NEC data tables before any tests run."""
    NECDataStore.load_all()


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)
