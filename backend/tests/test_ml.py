import pytest
from httpx import AsyncClient
from app.main import app

import uuid
def setup_user(client, role):
    email = f"test_{uuid.uuid4()}@example.com"
    password = "Password123!"
    reg_resp = client.post("/api/auth/register", json={
        "email": email,
        "password": password,
        "full_name": "Test User",
        "phone_number": "123456789"
    })
    assert reg_resp.status_code == 201, reg_resp.json()
    
    from app.models.user import User
    from tests.conftest import TestingSessionLocal
    db = TestingSessionLocal()
    user = db.query(User).filter(User.email == email).first()
    if user:
        user.role = role
        db.commit()
    db.close()
    
    resp = client.post("/api/auth/login", json={"email": email, "password": password})
    assert resp.status_code == 200, resp.json()
    token = resp.json()["access_token"]
    client.headers = {"Authorization": f"Bearer {token}"}
    return client

@pytest.fixture
def authenticated_admin_client(client):
    return setup_user(client, "ADMIN")

@pytest.fixture
def authenticated_donor_client(client):
    return setup_user(client, "DONOR")

def test_get_analytics(authenticated_admin_client):
    response = authenticated_admin_client.get("/api/analytics/metrics")
    assert response.status_code == 200
    data = response.json()
    assert "total_food_rescued_kg" in data
    assert "unmet_demand_kg" in data

def test_demand_forecast(authenticated_admin_client):
    payload = {
        "recipient_id": "1",
        "category": "Produce",
        "target_date": "2026-12-01T00:00:00Z"
    }
    response = authenticated_admin_client.post("/api/ml/demand-forecast", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "predicted_demand_kg" in data
    assert "is_synthetic_data" in data
    assert "model_version" in data
    # Ensure warning is included per requirements
    assert "advisory decision support only" in data.get("warning", "")

def test_demand_forecast_unauthorized(authenticated_donor_client):
    payload = {
        "recipient_id": "1",
        "category": "Produce",
        "target_date": "2026-12-01T00:00:00Z"
    }
    # Donors should not be able to forecast demand
    response = authenticated_donor_client.post("/api/ml/demand-forecast", json=payload)
    assert response.status_code == 403
