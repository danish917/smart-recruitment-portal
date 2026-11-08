"""Comprehensive tests for Authentication, JWT, and Role-Based Access Control."""

import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.main import app
from app.models.user import User, UserRole

client = TestClient(app)

# Use dynamic unique emails for test runs to prevent collision across test runs
timestamp = int(time.time())
CANDIDATE_EMAIL = f"candidate_{timestamp}@example.com"
RECRUITER_EMAIL = f"recruiter_{timestamp}@example.com"
TEST_PASSWORD = "StrongPassword123!"


def test_register_candidate():
    """Verify candidate registration succeeds with 201 Created."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": CANDIDATE_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Alice Candidate",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == CANDIDATE_EMAIL.lower()
    assert data["full_name"] == "Alice Candidate"
    assert data["role"] == "CANDIDATE"
    assert data["is_active"] is True
    assert "id" in data
    assert "hashed_password" not in data


def test_register_recruiter():
    """Verify recruiter registration succeeds with 201 Created."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": RECRUITER_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Bob Recruiter",
            "role": "RECRUITER",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == RECRUITER_EMAIL.lower()
    assert data["full_name"] == "Bob Recruiter"
    assert data["role"] == "RECRUITER"


def test_duplicate_email_registration_fails():
    """Verify registering an existing email returns 400 Bad Request."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": CANDIDATE_EMAIL,
            "password": "AnotherPassword456!",
            "full_name": "Imposter Alice",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data["detail"].lower()


def test_short_password_validation():
    """Verify passwords shorter than 8 characters are rejected with 422."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": f"short_{timestamp}@example.com",
            "password": "short",
            "full_name": "Short Pass User",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 422


def test_invalid_email_validation():
    """Verify malformed email formats are rejected with 422."""
    response = client.post(
        "/api/auth/register",
        json={
            "email": "not-an-email",
            "password": TEST_PASSWORD,
            "full_name": "Invalid Email User",
            "role": "CANDIDATE",
        },
    )
    assert response.status_code == 422


def test_login_success():
    """Verify login returns JWT access token and user info."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": CANDIDATE_EMAIL,
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert len(data["access_token"]) > 20
    assert data["user"]["email"] == CANDIDATE_EMAIL.lower()
    assert data["user"]["role"] == "CANDIDATE"


def test_login_invalid_password():
    """Verify wrong password returns 401 Unauthorized."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": CANDIDATE_EMAIL,
            "password": "WrongPassword999!",
        },
    )
    assert response.status_code == 401
    assert "invalid email or password" in response.json()["detail"].lower()


def test_login_nonexistent_user():
    """Verify unregistered email returns 401 Unauthorized."""
    response = client.post(
        "/api/auth/login",
        json={
            "email": f"nonexistent_{timestamp}@example.com",
            "password": TEST_PASSWORD,
        },
    )
    assert response.status_code == 401


def test_protected_me_endpoint():
    """Verify /api/auth/me returns profile for authenticated user."""
    # Obtain token
    login_res = client.post(
        "/api/auth/login",
        json={"email": CANDIDATE_EMAIL, "password": TEST_PASSWORD},
    )
    token = login_res.json()["access_token"]

    # Request /api/auth/me
    response = client.get(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == CANDIDATE_EMAIL.lower()
    assert data["full_name"] == "Alice Candidate"
    assert data["role"] == "CANDIDATE"


def test_protected_me_endpoint_unauthorized():
    """Verify /api/auth/me rejects requests without valid token with 401."""
    # No token
    res_no_token = client.get("/api/auth/me")
    assert res_no_token.status_code == 401

    # Malformed token
    res_bad_token = client.get(
        "/api/auth/me",
        headers={"Authorization": "Bearer bad-token-xyz"},
    )
    assert res_bad_token.status_code == 401


def test_role_based_access_control():
    """Verify role-based access permissions: candidate vs recruiter vs admin."""
    # Candidate Token
    candidate_login = client.post(
        "/api/auth/login",
        json={"email": CANDIDATE_EMAIL, "password": TEST_PASSWORD},
    )
    candidate_token = candidate_login.json()["access_token"]

    # Recruiter Token
    recruiter_login = client.post(
        "/api/auth/login",
        json={"email": RECRUITER_EMAIL, "password": TEST_PASSWORD},
    )
    recruiter_token = recruiter_login.json()["access_token"]

    # 1. Candidate accessing Candidate Dashboard -> 200 OK
    res1 = client.get(
        "/api/auth/candidate-dashboard",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert res1.status_code == 200

    # 2. Candidate accessing Recruiter Dashboard -> 403 Forbidden!
    res2 = client.get(
        "/api/auth/recruiter-dashboard",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert res2.status_code == 403
    assert "access denied" in res2.json()["detail"].lower()

    # 3. Candidate accessing Admin Panel -> 403 Forbidden!
    res3 = client.get(
        "/api/auth/admin-panel",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert res3.status_code == 403

    # 4. Recruiter accessing Recruiter Dashboard -> 200 OK
    res4 = client.get(
        "/api/auth/recruiter-dashboard",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert res4.status_code == 200

    # 5. Recruiter accessing Admin Panel -> 403 Forbidden!
    res5 = client.get(
        "/api/auth/admin-panel",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert res5.status_code == 403


def test_logout_endpoint():
    """Verify logout endpoint returns successful message."""
    response = client.post("/api/auth/logout")
    assert response.status_code == 200
    assert "logged out" in response.json()["message"].lower()


def test_database_persistence_and_password_hashing():
    """Directly inspect Neon PostgreSQL to verify row persistence and bcrypt hashing."""
    db: Session = SessionLocal()
    try:
        user = db.query(User).filter(User.email == CANDIDATE_EMAIL.lower()).first()
        assert user is not None
        assert user.id is not None
        assert user.role == UserRole.CANDIDATE
        # Verify password is NOT stored in plain text and is valid bcrypt ($2b$ or $2a$)
        assert user.hashed_password != TEST_PASSWORD
        assert user.hashed_password.startswith("$2")
        assert len(user.hashed_password) >= 50
    finally:
        db.close()
