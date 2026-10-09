import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole

def get_auth_headers(client: TestClient, email: str, role: str) -> dict:
    client.post("/api/auth/register", json={
        "email": email, "password": "SecurePassword123!", "full_name": f"Test {role}", "role": role
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "SecurePassword123!"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def create_admin(db: Session):
    from app.utils.security import hash_password
    admin = User(email="admin_match@example.com", hashed_password=hash_password("SecurePassword123!"), full_name="Admin", role=UserRole.ADMIN)
    db.add(admin)
    db.commit()

def test_recipient_profile_and_demand(client: TestClient):
    headers = get_auth_headers(client, "rec1@example.com", "recipient")
    
    # 1. Create Profile
    prof_res = client.post("/api/recipients/profile", headers=headers, json={
        "organization_name": "Food Bank A",
        "capacity_kg": 500,
        "food_categories_accepted": ["Produce", "Bakery"]
    })
    assert prof_res.status_code == 201
    
    # 2. Get Profile
    get_prof = client.get("/api/recipients/profile", headers=headers)
    assert get_prof.status_code == 200
    
    # 3. Create Demand
    future_date = (datetime.now(timezone.utc) + timedelta(days=5)).isoformat()
    dem_res = client.post("/api/recipients/demands", headers=headers, json={
        "food_category": "Produce",
        "quantity_requested": 100,
        "needed_by": future_date
    })
    assert dem_res.status_code == 201
    
    # 4. List Demands
    list_dem = client.get("/api/recipients/demands", headers=headers)
    assert len(list_dem.json()) == 1

def test_matching_agent_logic(client: TestClient, db_session: Session):
    # Setup Admin
    create_admin(db_session)
    admin_headers = get_auth_headers(client, "admin_match@example.com", "admin")
    # Actually admin login already registers if we use get_auth_headers but it fails schema due to role admin, 
    # so we manually login:
    admin_login = client.post("/api/auth/login", json={"email": "admin_match@example.com", "password": "SecurePassword123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    
    # Setup Recipient 1 (Verified, High Capacity, Match)
    rec1_headers = get_auth_headers(client, "match_rec1@example.com", "recipient")
    # Set coordinates for recipient user directly via DB for distance testing
    rec1_user = db_session.query(User).filter(User.email == "match_rec1@example.com").first()
    rec1_user.latitude = 40.7128 # Same location as donation
    rec1_user.longitude = -74.0060
    db_session.commit()
    
    r1 = client.post("/api/recipients/profile", headers=rec1_headers, json={
        "organization_name": "Shelter 1", "capacity_kg": 200, "food_categories_accepted": ["Bakery"]
    }).json()
    
    # Verify R1
    client.post(f"/api/recipients/{r1['user_id']}/verify", headers=admin_headers)
    
    # Setup Recipient 2 (Verified, Low Capacity, Match)
    rec2_headers = get_auth_headers(client, "match_rec2@example.com", "recipient")
    rec2_user = db_session.query(User).filter(User.email == "match_rec2@example.com").first()
    rec2_user.latitude = 40.7500 # Slightly away
    rec2_user.longitude = -73.9800
    db_session.commit()
    
    r2 = client.post("/api/recipients/profile", headers=rec2_headers, json={
        "organization_name": "Shelter 2", "capacity_kg": 10, "food_categories_accepted": ["Bakery"]
    }).json()
    client.post(f"/api/recipients/{r2['user_id']}/verify", headers=admin_headers)
    
    # Setup Recipient 3 (Unverified - should be excluded)
    rec3_headers = get_auth_headers(client, "match_rec3@example.com", "recipient")
    client.post("/api/recipients/profile", headers=rec3_headers, json={
        "organization_name": "Shelter 3", "capacity_kg": 200, "food_categories_accepted": ["Bakery"]
    })
    
    # Setup Recipient 4 (Verified but Incompatible Food)
    rec4_headers = get_auth_headers(client, "match_rec4@example.com", "recipient")
    r4 = client.post("/api/recipients/profile", headers=rec4_headers, json={
        "organization_name": "Shelter 4", "capacity_kg": 200, "food_categories_accepted": ["Meat Only"]
    }).json()
    client.post(f"/api/recipients/{r4['user_id']}/verify", headers=admin_headers)
    
    # Setup Donor and Donation (50kg Bakery)
    donor_headers = get_auth_headers(client, "match_donor@example.com", "donor")
    future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    don_res = client.post("/api/donations", headers=donor_headers, json={
        "food_type": "Bakery",
        "description": "50kg of bread",
        "quantity_kg": 50,
        "expires_at": future,
        "latitude": 40.7128,
        "longitude": -74.0060,
        "pickup_address": "Bakery St"
    })
    donation_id = don_res.json()["id"]
    
    # Try matching before eligibility (Should return empty or fail hard constraint)
    match_res_pre = client.post(f"/api/matching/{donation_id}", headers=donor_headers)
    assert match_res_pre.status_code == 200
    assert len(match_res_pre.json()["matches"]) == 0 # because status is PENDING_REVIEW
    
    # Screen Donation -> ELIGIBLE
    client.post(f"/api/donations/{donation_id}/screen", headers=donor_headers)
    
    # Run Matching
    match_res = client.post(f"/api/matching/{donation_id}", headers=donor_headers)
    assert match_res.status_code == 200
    matches = match_res.json()["matches"]
    
    # R3 (unverified) and R4 (incompatible) should be filtered out.
    # R1 and R2 should remain.
    assert len(matches) == 2
    
    # R1 should be ranked higher (closer distance, full capacity fit)
    assert matches[0]["recipient_id"] == r1["id"]
    assert matches[0]["recommended_quantity_kg"] == 50.0 # Can take all 50
    assert matches[1]["recipient_id"] == r2["id"]
    assert matches[1]["recommended_quantity_kg"] == 10.0 # Can only take 10
    
    # Check score structure
    assert "factor_scores" in matches[0]
    assert "explanation" in matches[0]
    assert "warnings" in matches[1]
    assert any("can only accept 10.0kg" in w for w in matches[1]["warnings"])
