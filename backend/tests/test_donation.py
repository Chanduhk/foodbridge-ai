import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

def get_auth_headers(client: TestClient, email: str = "donor1@example.com") -> dict:
    """Helper to register and login a user, returning auth headers."""
    # Attempt to register, ignore if already exists
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "SecurePassword123!",
            "full_name": "Test Donor",
            "role": "donor",
        }
    )
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": email,
            "password": "SecurePassword123!"
        }
    )
    token = login_res.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

def test_create_donation_success(client: TestClient):
    headers = get_auth_headers(client)
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    
    response = client.post(
        "/api/donations",
        headers=headers,
        json={
            "donor_type": "restaurant",
            "food_type": "Cooked Rice",
            "description": "Leftover from yesterday",
            "quantity_kg": 10.5,
            "expires_at": future_date,
            "storage_type": "ambient",
            "requires_vehicle": True,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "pickup_address": "123 Main St",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["food_type"] == "Cooked Rice"
    assert data["status"] == "pending_review"

def test_create_donation_unauthorized(client: TestClient):
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    response = client.post(
        "/api/donations",
        json={
            "food_type": "Cooked Rice",
            "description": "Leftover",
            "quantity_kg": 10.5,
            "expires_at": future_date,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "pickup_address": "123 Main St",
        }
    )
    assert response.status_code == 401

def test_create_donation_invalid_data(client: TestClient):
    headers = get_auth_headers(client)
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    
    response = client.post(
        "/api/donations",
        headers=headers,
        json={
            "food_type": "C", # Too short
            "description": "Lef", # Too short
            "quantity_kg": -5, # Invalid quantity
            "expires_at": future_date,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "pickup_address": "123", # Too short
        }
    )
    assert response.status_code == 422

def test_get_donation_and_ownership(client: TestClient):
    headers1 = get_auth_headers(client, "donorA@example.com")
    headers2 = get_auth_headers(client, "donorB@example.com")
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    
    create_res = client.post(
        "/api/donations",
        headers=headers1,
        json={
            "food_type": "Apples",
            "description": "Fresh apples",
            "quantity_kg": 5,
            "expires_at": future_date,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "pickup_address": "123 Main St",
        }
    )
    assert create_res.status_code == 201
    donation_id = create_res.json()["id"]
    
    # Owner can get
    get_res = client.get(f"/api/donations/{donation_id}", headers=headers1)
    assert get_res.status_code == 200
    
    # Other donor cannot get
    get_other = client.get(f"/api/donations/{donation_id}", headers=headers2)
    assert get_other.status_code == 403

def test_update_donation(client: TestClient):
    headers = get_auth_headers(client, "donor_update@example.com")
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    
    create_res = client.post(
        "/api/donations",
        headers=headers,
        json={
            "food_type": "Oranges",
            "description": "Fresh oranges",
            "quantity_kg": 5,
            "expires_at": future_date,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "pickup_address": "123 Main St",
        }
    )
    donation_id = create_res.json()["id"]
    
    # Update quantity
    update_res = client.patch(
        f"/api/donations/{donation_id}",
        headers=headers,
        json={"quantity_kg": 10.0}
    )
    assert update_res.status_code == 200
    assert update_res.json()["quantity_kg"] == 10.0

def test_eligibility_success(client: TestClient):
    headers = get_auth_headers(client, "donor_eligible@example.com")
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    
    create_res = client.post(
        "/api/donations",
        headers=headers,
        json={
            "food_type": "Bananas",
            "description": "A big bunch of bananas, very fresh.",
            "quantity_kg": 15,
            "expires_at": future_date,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "pickup_address": "456 Market St, City Center",
        }
    )
    donation_id = create_res.json()["id"]
    
    # Run screening
    screen_res = client.post(f"/api/donations/{donation_id}/screen", headers=headers)
    assert screen_res.status_code == 200
    data = screen_res.json()
    assert data["status"] == "eligible"
    assert data["eligibility_result"]["eligible"] is True
    assert data["eligibility_result"]["requires_human_review"] is False

def test_eligibility_review_required(client: TestClient):
    # Description missing/too short -> review required
    headers = get_auth_headers(client, "donor_review@example.com")
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    
    # Directly inserting a donation where a soft check fails
    # Wait, the creation schema requires description length >= 5. 
    # Let's see if we can create a donation and update it, or if our agent handles borderline cases.
    # We will make description exactly 5 chars. Our rule is > 5, so it should flag review.
    create_res = client.post(
        "/api/donations",
        headers=headers,
        json={
            "food_type": "Bananas",
            "description": "Short", # exactly 5 chars
            "quantity_kg": 15,
            "expires_at": future_date,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "pickup_address": "456 Market St",
        }
    )
    donation_id = create_res.json()["id"]
    
    screen_res = client.post(f"/api/donations/{donation_id}/screen", headers=headers)
    assert screen_res.status_code == 200
    data = screen_res.json()
    assert data["status"] == "review_required"
    assert data["eligibility_result"]["requires_human_review"] is True

def test_eligibility_rejected_expired(client: TestClient):
    headers = get_auth_headers(client, "donor_expired@example.com")
    # Date in the past. To test this, we need to bypass schema if the schema blocks it?
    # Schema doesn't block past dates on creation! The Agent blocks it.
    past_date = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
    
    create_res = client.post(
        "/api/donations",
        headers=headers,
        json={
            "food_type": "Milk",
            "description": "10 gallons of milk",
            "quantity_kg": 10,
            "expires_at": past_date,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "pickup_address": "456 Market St, City Center",
        }
    )
    donation_id = create_res.json()["id"]
    
    screen_res = client.post(f"/api/donations/{donation_id}/screen", headers=headers)
    assert screen_res.status_code == 200
    data = screen_res.json()
    assert data["status"] == "rejected"
    assert data["eligibility_result"]["eligible"] is False
    assert "The stated deadline has passed" in data["rejection_reason"]

def test_update_not_allowed_after_screen(client: TestClient):
    headers = get_auth_headers(client, "donor_update_block@example.com")
    future_date = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    
    create_res = client.post(
        "/api/donations",
        headers=headers,
        json={
            "food_type": "Bananas",
            "description": "A big bunch of bananas, very fresh.",
            "quantity_kg": 15,
            "expires_at": future_date,
            "latitude": 40.7128,
            "longitude": -74.0060,
            "pickup_address": "456 Market St, City Center",
        }
    )
    donation_id = create_res.json()["id"]
    
    # Run screening -> status becomes ELIGIBLE
    client.post(f"/api/donations/{donation_id}/screen", headers=headers)
    
    # Update should fail
    update_res = client.patch(
        f"/api/donations/{donation_id}",
        headers=headers,
        json={"quantity_kg": 10.0}
    )
    assert update_res.status_code == 400
    assert "Donation cannot be updated" in update_res.json()["detail"]
