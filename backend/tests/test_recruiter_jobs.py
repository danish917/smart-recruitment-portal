"""Automated tests for Recruiter Module: Job Creation, Management, and Isolation."""

import time
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.main import app
from app.models.job import Job, JobStatus

client = TestClient(app)

# Generate unique emails for test isolation
timestamp = int(time.time())
RECRUITER_A_EMAIL = f"recruiter_a_{timestamp}@company.com"
RECRUITER_B_EMAIL = f"recruiter_b_{timestamp}@company.com"
CANDIDATE_EMAIL = f"candidate_test_{timestamp}@candidate.com"
PASSWORD = "SecurePassword123!"


def get_token_for(email: str, role: str) -> str:
    """Helper to register and login a user, returning their access token."""
    client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": PASSWORD,
            "full_name": f"User {role}",
            "role": role,
        },
    )
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": PASSWORD},
    )
    return login_res.json()["access_token"]


@pytest.fixture(scope="module")
def recruiter_a_token():
    return get_token_for(RECRUITER_A_EMAIL, "RECRUITER")


@pytest.fixture(scope="module")
def recruiter_b_token():
    return get_token_for(RECRUITER_B_EMAIL, "RECRUITER")


@pytest.fixture(scope="module")
def candidate_token():
    return get_token_for(CANDIDATE_EMAIL, "CANDIDATE")


def test_unauthenticated_cannot_access_recruiter_routes():
    """Verify unauthenticated access to /api/recruiter/* returns 401."""
    res1 = client.get("/api/recruiter/jobs")
    assert res1.status_code == 401

    res2 = client.post("/api/recruiter/jobs", json={})
    assert res2.status_code == 401

    res3 = client.get("/api/recruiter/dashboard/stats")
    assert res3.status_code == 401


def test_candidate_cannot_access_recruiter_routes(candidate_token):
    """Verify candidate cannot create or manage jobs (403 Forbidden)."""
    headers = {"Authorization": f"Bearer {candidate_token}"}

    res_get = client.get("/api/recruiter/jobs", headers=headers)
    assert res_get.status_code == 403

    res_post = client.post(
        "/api/recruiter/jobs",
        headers=headers,
        json={
            "title": "Unauthorized Job",
            "company_name": "Test Co",
            "description": "Candidate should not be allowed to post jobs.",
            "required_skills": "Python",
            "qualification": "BS",
            "experience_years": "2 years",
            "work_location": "Remote",
        },
    )
    assert res_post.status_code == 403
    assert "access denied" in res_post.json()["detail"].lower()


def test_recruiter_create_job(recruiter_a_token):
    """Verify recruiter can create a new job posting with default DRAFT status."""
    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    payload = {
        "title": "Senior Python Backend Engineer",
        "company_name": "Tech Innovations Inc.",
        "description": "Looking for an experienced FastAPI and PostgreSQL engineer to build scalable services.",
        "required_skills": "Python, FastAPI, PostgreSQL, Docker, Redis",
        "qualification": "Bachelor's degree in Computer Science or equivalent experience",
        "experience_years": "5+ years",
        "employment_type": "FULL_TIME",
        "work_location": "Remote - US / Global",
        "salary_min": 120000.0,
        "salary_max": 160000.0,
        "salary_currency": "USD",
        "status": "DRAFT",
    }
    response = client.post("/api/recruiter/jobs", headers=headers, json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["title"] == payload["title"]
    assert data["company_name"] == payload["company_name"]
    assert data["status"] == "DRAFT"
    assert data["employment_type"] == "FULL_TIME"
    assert "id" in data
    assert "recruiter_id" in data


def test_recruiter_list_own_jobs(recruiter_a_token):
    """Verify recruiter sees their created jobs."""
    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    response = client.get("/api/recruiter/jobs", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert any(j["title"] == "Senior Python Backend Engineer" for j in data)


def test_recruiter_update_job(recruiter_a_token):
    """Verify recruiter can edit their existing job posting."""
    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    # Create job
    create_res = client.post(
        "/api/recruiter/jobs",
        headers=headers,
        json={
            "title": "Junior QA Specialist",
            "company_name": "QA Labs",
            "description": "Initial description before update.",
            "required_skills": "Selenium, Pytest",
            "qualification": "Associate Degree",
            "experience_years": "1 year",
            "work_location": "Hybrid",
            "status": "DRAFT",
        },
    )
    job_id = create_res.json()["id"]

    # Update job
    update_payload = {
        "title": "Lead QA Automation Engineer",
        "salary_min": 90000.0,
        "salary_max": 110000.0,
        "work_location": "Fully Remote",
    }
    update_res = client.put(f"/api/recruiter/jobs/{job_id}", headers=headers, json=update_payload)
    assert update_res.status_code == 200
    updated_data = update_res.json()
    assert updated_data["title"] == "Lead QA Automation Engineer"
    assert updated_data["salary_min"] == 90000.0
    assert updated_data["work_location"] == "Fully Remote"
    assert updated_data["company_name"] == "QA Labs"  # Unchanged field preserved


def test_recruiter_publish_job(recruiter_a_token):
    """Verify recruiter can publish a draft job posting."""
    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    create_res = client.post(
        "/api/recruiter/jobs",
        headers=headers,
        json={
            "title": "Product Designer",
            "company_name": "Design Studio",
            "description": "UI/UX product design for web applications.",
            "required_skills": "Figma, Wireframing",
            "qualification": "Design Degree",
            "experience_years": "3 years",
            "work_location": "Remote",
            "status": "DRAFT",
        },
    )
    job_id = create_res.json()["id"]
    assert create_res.json()["status"] == "DRAFT"

    # Publish
    publish_res = client.patch(f"/api/recruiter/jobs/{job_id}/publish", headers=headers)
    assert publish_res.status_code == 200
    assert publish_res.json()["status"] == "ACTIVE"


def test_recruiter_archive_job(recruiter_a_token):
    """Verify recruiter can archive an active job posting."""
    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    create_res = client.post(
        "/api/recruiter/jobs",
        headers=headers,
        json={
            "title": "Temporary Contract Role",
            "company_name": "Contractors Corp",
            "description": "Short term position to be archived.",
            "required_skills": "General",
            "qualification": "High School",
            "experience_years": "None",
            "work_location": "On-site",
            "status": "ACTIVE",
        },
    )
    job_id = create_res.json()["id"]

    # Archive
    archive_res = client.patch(f"/api/recruiter/jobs/{job_id}/archive", headers=headers)
    assert archive_res.status_code == 200
    assert archive_res.json()["status"] == "ARCHIVED"


def test_recruiter_isolation_cannot_access_or_modify_other_recruiter_job(recruiter_a_token, recruiter_b_token):
    """Verify Recruiter B CANNOT view, modify, publish, or archive Recruiter A's job."""
    headers_a = {"Authorization": f"Bearer {recruiter_a_token}"}
    headers_b = {"Authorization": f"Bearer {recruiter_b_token}"}

    # Recruiter A creates a private job
    res_a = client.post(
        "/api/recruiter/jobs",
        headers=headers_a,
        json={
            "title": "Confidential Executive Role",
            "company_name": "Stealth Startup",
            "description": "Executive leadership position.",
            "required_skills": "Executive Leadership",
            "qualification": "MBA",
            "experience_years": "10+ years",
            "work_location": "Remote",
            "status": "DRAFT",
        },
    )
    job_id = res_a.json()["id"]

    # Recruiter B attempts to view Recruiter A's job -> 403 Forbidden
    view_res = client.get(f"/api/recruiter/jobs/{job_id}", headers=headers_b)
    assert view_res.status_code == 403

    # Recruiter B attempts to update Recruiter A's job -> 403 Forbidden
    update_res = client.put(
        f"/api/recruiter/jobs/{job_id}",
        headers=headers_b,
        json={"title": "Hacked Title"},
    )
    assert update_res.status_code == 403

    # Recruiter B attempts to publish Recruiter A's job -> 403 Forbidden
    publish_res = client.patch(f"/api/recruiter/jobs/{job_id}/publish", headers=headers_b)
    assert publish_res.status_code == 403

    # Recruiter B attempts to archive Recruiter A's job -> 403 Forbidden
    archive_res = client.patch(f"/api/recruiter/jobs/{job_id}/archive", headers=headers_b)
    assert archive_res.status_code == 403

    # Recruiter B attempts to delete Recruiter A's job -> 403 Forbidden
    delete_res = client.delete(f"/api/recruiter/jobs/{job_id}", headers=headers_b)
    assert delete_res.status_code == 403


def test_recruiter_dashboard_stats(recruiter_a_token):
    """Verify recruiter dashboard stats counts are calculated accurately."""
    headers = {"Authorization": f"Bearer {recruiter_a_token}"}
    response = client.get("/api/recruiter/dashboard/stats", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_jobs" in data
    assert "active_jobs" in data
    assert "draft_jobs" in data
    assert "archived_jobs" in data
    assert "total_applications" in data
    assert "recent_jobs" in data
    assert data["total_jobs"] >= 3
    assert len(data["recent_jobs"]) <= 5


def test_jobs_persisted_in_neon_database():
    """Verify jobs are actually saved in Neon PostgreSQL with foreign key relationships."""
    db: Session = SessionLocal()
    try:
        jobs = db.query(Job).all()
        assert len(jobs) >= 3
        sample_job = jobs[0]
        assert sample_job.recruiter is not None
        assert sample_job.recruiter.email is not None
        assert sample_job.status in (JobStatus.DRAFT, JobStatus.ACTIVE, JobStatus.ARCHIVED)
    finally:
        db.close()
