from fastapi.testclient import TestClient


def test_root_endpoint(client: TestClient):
    """Test the root endpoint returns 200 and greeting."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "FoodBridge AI" in data["message"]
    assert data["health_check"] == "/api/health"


def test_health_endpoint_healthy(client: TestClient):
    """Test GET /api/health returns 200 with connected DB and healthy status."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["project"] == "FoodBridge AI"
    assert data["database"] == "connected"
    assert "details" in data
