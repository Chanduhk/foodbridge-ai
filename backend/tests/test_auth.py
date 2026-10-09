import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.models.user import User, UserRole

def test_register_user_success(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "newuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "New User",
            "role": "donor",
        }
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "newuser@example.com"
    assert data["full_name"] == "New User"
    assert data["role"] == "donor"
    assert "hashed_password" not in data
    assert "password" not in data

def test_register_duplicate_email(client: TestClient):
    payload = {
        "email": "duplicate@example.com",
        "password": "SecurePassword123!",
        "full_name": "Duplicate User",
        "role": "donor",
    }
    # First registration
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    # Second registration should fail
    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 409
    assert res2.json()["detail"] == "A user with this email already exists"

def test_register_admin_forbidden(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "admin-wannabe@example.com",
            "password": "SecurePassword123!",
            "full_name": "Admin Wannabe",
            "role": "admin",
        }
    )
    assert response.status_code == 422 # Schema validation fails first

def test_register_weak_password(client: TestClient):
    response = client.post(
        "/api/auth/register",
        json={
            "email": "weakpass@example.com",
            "password": "weak",
            "full_name": "Weak Pass",
            "role": "donor",
        }
    )
    assert response.status_code == 422

def test_login_success(client: TestClient):
    # Register
    client.post(
        "/api/auth/register",
        json={
            "email": "loginuser@example.com",
            "password": "SecurePassword123!",
            "full_name": "Login User",
            "role": "donor",
        }
    )
    
    # Login
    response = client.post(
        "/api/auth/login",
        json={
            "email": "loginuser@example.com",
            "password": "SecurePassword123!"
        }
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

def test_login_invalid_password(client: TestClient):
    client.post(
        "/api/auth/register",
        json={
            "email": "wrongpass@example.com",
            "password": "SecurePassword123!",
            "full_name": "Wrong Pass",
            "role": "donor",
        }
    )
    
    response = client.post(
        "/api/auth/login",
        json={
            "email": "wrongpass@example.com",
            "password": "WrongPassword123!"
        }
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid email or password"

def test_get_me_success(client: TestClient):
    client.post(
        "/api/auth/register",
        json={
            "email": "me@example.com",
            "password": "SecurePassword123!",
            "full_name": "Me User",
            "role": "donor",
        }
    )
    
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "me@example.com",
            "password": "SecurePassword123!"
        }
    )
    token = login_res.json()["access_token"]
    
    me_res = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "me@example.com"

def test_admin_check_forbidden(client: TestClient):
    client.post(
        "/api/auth/register",
        json={
            "email": "notadmin@example.com",
            "password": "SecurePassword123!",
            "full_name": "Not Admin",
            "role": "donor",
        }
    )
    
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "notadmin@example.com",
            "password": "SecurePassword123!"
        }
    )
    token = login_res.json()["access_token"]
    
    admin_res = client.get(
        "/api/auth/admin-check",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert admin_res.status_code == 403

def test_admin_check_success(client: TestClient, db_session: Session):
    # Manually create admin user via DB since self-registration as admin is forbidden
    from app.utils.security import hash_password
    admin_user = User(
        email="realadmin@example.com",
        hashed_password=hash_password("SecurePassword123!"),
        full_name="Real Admin",
        role=UserRole.ADMIN
    )
    db_session.add(admin_user)
    db_session.commit()
    
    login_res = client.post(
        "/api/auth/login",
        json={
            "email": "realadmin@example.com",
            "password": "SecurePassword123!"
        }
    )
    token = login_res.json()["access_token"]
    
    admin_res = client.get(
        "/api/auth/admin-check",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert admin_res.status_code == 200
    assert admin_res.json()["role"] == "admin"
