import pytest
from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
import concurrent.futures

def get_auth_headers(client: TestClient, email: str, role: str) -> dict:
    client.post("/api/auth/register", json={
        "email": email, "password": "SecurePassword123!", "full_name": f"Test {role}", "role": role
    })
    res = client.post("/api/auth/login", json={"email": email, "password": "SecurePassword123!"})
    return {"Authorization": f"Bearer {res.json()['access_token']}"}

def create_admin(db: Session):
    from app.utils.security import hash_password
    if not db.query(User).filter(User.email == "admin_deliv@example.com").first():
        admin = User(email="admin_deliv@example.com", hashed_password=hash_password("SecurePassword123!"), full_name="Admin", role=UserRole.ADMIN)
        db.add(admin)
        db.commit()

@pytest.fixture
def setup_delivery_flow(client: TestClient, db_session: Session):
    create_admin(db_session)
    admin_login = client.post("/api/auth/login", json={"email": "admin_deliv@example.com", "password": "SecurePassword123!"})
    admin_headers = {"Authorization": f"Bearer {admin_login.json()['access_token']}"}
    
    donor_headers = get_auth_headers(client, "donor_deliv@example.com", "donor")
    rec1_headers = get_auth_headers(client, "rec1_deliv@example.com", "recipient")
    vol1_headers = get_auth_headers(client, "vol1_deliv@example.com", "volunteer")
    vol2_headers = get_auth_headers(client, "vol2_deliv@example.com", "volunteer")
    
    # Verify Recipient 1
    r1 = client.post("/api/recipients/profile", headers=rec1_headers, json={
        "organization_name": "R1", "capacity_kg": 100, "food_categories_accepted": ["Produce"]
    }).json()
    client.post(f"/api/recipients/{r1['user_id']}/verify", headers=admin_headers)
    
    # Create Eligible Donation
    future = (datetime.now(timezone.utc) + timedelta(days=2)).isoformat()
    don = client.post("/api/donations", headers=donor_headers, json={
        "food_type": "Produce", "description": "100kg Apples", "quantity_kg": 100, 
        "expires_at": future, "latitude": 40.71, "longitude": -74.00, "pickup_address": "Orchard"
    }).json()
    
    client.post(f"/api/donations/{don['id']}/screen", headers=donor_headers)
    
    # Create Allocation
    alloc = client.post("/api/allocations", headers=donor_headers, json={
        "donation_id": don["id"], "recipient_id": r1["id"], "quantity_kg": 40
    }).json()
    
    return {
        "donor_h": donor_headers,
        "rec1_h": rec1_headers,
        "vol1_h": vol1_headers,
        "vol2_h": vol2_headers,
        "admin_h": admin_headers,
        "don_id": don["id"],
        "r1_id": r1["id"],
        "alloc_id": alloc["id"]
    }

def test_delivery_creation_requires_accepted_allocation(client: TestClient, setup_delivery_flow):
    f = setup_delivery_flow
    
    # Allocation is currently PROPOSED. Delivery creation should fail.
    res_fail = client.post("/api/deliveries", headers=f["donor_h"], json={
        "allocation_id": f["alloc_id"], "scheduled_pickup": datetime.now(timezone.utc).isoformat()
    })
    assert res_fail.status_code == 400
    assert "Cannot create delivery for allocation in status AllocationStatus.PROPOSED" in res_fail.json()["detail"]
    
    # Accept allocation
    client.post(f"/api/allocations/{f['alloc_id']}/accept", headers=f["rec1_h"])
    
    # Delivery creation should succeed now
    res_succ = client.post("/api/deliveries", headers=f["donor_h"], json={
        "allocation_id": f["alloc_id"], "scheduled_pickup": datetime.now(timezone.utc).isoformat()
    })
    assert res_succ.status_code == 201
    assert res_succ.json()["status"] == "scheduled"

def test_delivery_logistics_agent(client: TestClient, setup_delivery_flow):
    f = setup_delivery_flow
    
    # Accept allocation
    client.post(f"/api/allocations/{f['alloc_id']}/accept", headers=f["rec1_h"])
    
    rec = client.get(f"/api/deliveries/allocation/{f['alloc_id']}/recommend", headers=f["admin_h"])
    assert rec.status_code == 200
    assert "distance_km" in rec.json()
    assert "estimated_duration_min" in rec.json()
    assert "recommended_volunteer_ids" in rec.json()
    # vol1 and vol2 should be in there since they are active volunteers
    assert len(rec.json()["recommended_volunteer_ids"]) >= 2

def test_volunteer_claim_and_transitions(client: TestClient, setup_delivery_flow):
    f = setup_delivery_flow
    client.post(f"/api/allocations/{f['alloc_id']}/accept", headers=f["rec1_h"])
    deliv = client.post("/api/deliveries", headers=f["donor_h"], json={"allocation_id": f["alloc_id"]}).json()
    deliv_id = deliv["id"]
    
    # Volunteer claims
    claim = client.post(f"/api/deliveries/{deliv_id}/claim", headers=f["vol1_h"])
    assert claim.status_code == 200
    assert claim.json()["status"] == "claimed"
    
    # Another volunteer cannot claim
    claim2 = client.post(f"/api/deliveries/{deliv_id}/claim", headers=f["vol2_h"])
    assert claim2.status_code == 400 or claim2.status_code == 409
    
    # Valid transitions
    trans1 = client.patch(f"/api/deliveries/{deliv_id}/status", headers=f["vol1_h"], json={"status": "picked_up"})
    assert trans1.status_code == 200
    assert trans1.json()["actual_pickup"] is not None
    
    trans2 = client.patch(f"/api/deliveries/{deliv_id}/status", headers=f["vol1_h"], json={"status": "in_transit"})
    assert trans2.status_code == 200
    
    trans3 = client.patch(f"/api/deliveries/{deliv_id}/status", headers=f["vol1_h"], json={"status": "delivered"})
    assert trans3.status_code == 200
    assert trans3.json()["actual_delivery"] is not None
    
    # Check allocation synced to completed
    alloc = client.get(f"/api/allocations/{f['alloc_id']}", headers=f["donor_h"])
    assert alloc.json()["status"] == "completed"

def test_invalid_state_transition(client: TestClient, setup_delivery_flow):
    f = setup_delivery_flow
    client.post(f"/api/allocations/{f['alloc_id']}/accept", headers=f["rec1_h"])
    deliv = client.post("/api/deliveries", headers=f["donor_h"], json={"allocation_id": f["alloc_id"]}).json()
    deliv_id = deliv["id"]
    
    client.post(f"/api/deliveries/{deliv_id}/claim", headers=f["vol1_h"])
    
    # Try invalid transition (CLAIMED -> DELIVERED)
    trans = client.patch(f"/api/deliveries/{deliv_id}/status", headers=f["vol1_h"], json={"status": "delivered"})
    assert trans.status_code == 400

def test_concurrent_volunteer_claim_race(client: TestClient, setup_delivery_flow):
    f = setup_delivery_flow
    client.post(f"/api/allocations/{f['alloc_id']}/accept", headers=f["rec1_h"])
    deliv = client.post("/api/deliveries", headers=f["donor_h"], json={"allocation_id": f["alloc_id"]}).json()
    deliv_id = deliv["id"]
    
    def attempt_claim(header):
        return client.post(f"/api/deliveries/{deliv_id}/claim", headers=header)
        
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        f1 = executor.submit(attempt_claim, f["vol1_h"])
        f2 = executor.submit(attempt_claim, f["vol2_h"])
        results = [f1.result(), f2.result()]
        
    successes = [r for r in results if r.status_code == 200]
    # OCC or validation will catch the second attempt
    assert len(successes) == 1
    
    d = client.get(f"/api/deliveries/{deliv_id}", headers=f["vol1_h"])
    assert d.json()["status"] == "claimed"
    # Ensure one specific volunteer got it
    vol_id = successes[0].json()["volunteer_id"]
    assert d.json()["volunteer_id"] == vol_id
