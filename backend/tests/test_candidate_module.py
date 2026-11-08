"""Automated integration tests for Candidate Profile, Resume Management, Job Discovery, and Applications."""

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.application import Application, ApplicationStatus
from app.models.candidate import CandidateProfile, Resume
from app.models.job import Job, JobStatus

client = TestClient(app)


def get_unique_email(prefix: str = "cand") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def register_user(client: TestClient, role: str, email: str = None, name: str = None) -> tuple[str, dict]:
    """Helper to register a user and return (bearer_token, user_dict)."""
    if not email:
        email = get_unique_email(role.lower())
    if not name:
        name = f"Test {role.title()} User"

    res = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": name,
            "role": role,
        },
    )
    assert res.status_code == 201
    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "Password123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    user_info = login_res.json()["user"]
    return token, user_info


def test_unauthenticated_cannot_access_candidate_endpoints():
    """Unauthenticated requests must be rejected with 401."""
    assert client.get("/api/candidate/profile").status_code == 401
    assert client.get("/api/candidate/resume").status_code == 401
    assert client.get("/api/candidate/dashboard/stats").status_code == 401
    assert client.get("/api/candidate/applications").status_code == 401
    assert client.post("/api/candidate/applications", json={"job_id": 1}).status_code == 401


def test_recruiter_cannot_access_candidate_profile():
    """Recruiter role cannot access candidate-only routes (returns 403)."""
    recruiter_token, _ = register_user(client, "RECRUITER")
    headers = {"Authorization": f"Bearer {recruiter_token}"}
    res = client.get("/api/candidate/profile", headers=headers)
    assert res.status_code == 403


def test_candidate_profile_lifecycle():
    """Candidate profile can be fetched and updated."""
    token, user = register_user(client, "CANDIDATE")
    headers = {"Authorization": f"Bearer {token}"}

    # Initial profile get
    res = client.get("/api/candidate/profile", headers=headers)
    assert res.status_code == 200
    profile = res.json()
    assert profile["user_id"] == user["id"]
    assert profile["email"] == user["email"]
    assert profile["has_resume"] is False

    # Update profile
    update_payload = {
        "full_name": "Updated Candidate Name",
        "phone_number": "+1 555-0199",
        "education": "Master of Computer Science",
        "college_university": "Stanford University",
        "graduation_year": 2024,
        "skills": "Python, FastAPI, TypeScript, PostgreSQL",
        "experience": "4 years",
        "location": "San Francisco, CA",
        "professional_summary": "Experienced full-stack engineer specializing in cloud architectures.",
    }
    update_res = client.put(
        "/api/candidate/profile",
        json=update_payload,
        headers=headers,
    )
    assert update_res.status_code == 200
    updated = update_res.json()
    assert updated["full_name"] == "Updated Candidate Name"
    assert updated["education"] == "Master of Computer Science"
    assert updated["graduation_year"] == 2024
    assert "FastAPI" in updated["skills"]


def test_resume_upload_validation_non_pdf():
    """Uploading non-PDF file returns 400 Bad Request."""
    token, _ = register_user(client, "CANDIDATE")
    headers = {"Authorization": f"Bearer {token}"}

    # Non-PDF text file
    fake_file = io.BytesIO(b"This is a text document.")
    res = client.post(
        "/api/candidate/resume/upload",
        files={"file": ("resume.txt", fake_file, "text/plain")},
        headers=headers,
    )
    assert res.status_code == 400
    assert "PDF" in res.json()["detail"]


def test_resume_upload_success_metadata_and_download():
    """Upload valid PDF, inspect metadata, download securely, replace, and delete."""
    token, _ = register_user(client, "CANDIDATE")
    headers = {"Authorization": f"Bearer {token}"}

    # Valid mock PDF content starting with %PDF-
    mock_pdf_content = b"%PDF-1.4\n1 0 obj\n<<>>\nendobj\ntrailer\n<<>>\n%%EOF"
    pdf_file = io.BytesIO(mock_pdf_content)

    upload_res = client.post(
        "/api/candidate/resume/upload",
        files={"file": ("test_resume.pdf", pdf_file, "application/pdf")},
        headers=headers,
    )
    assert upload_res.status_code == 200
    resume_data = upload_res.json()
    assert resume_data["original_filename"] == "test_resume.pdf"
    assert resume_data["file_size"] == len(mock_pdf_content)

    # Fetch metadata
    meta_res = client.get("/api/candidate/resume", headers=headers)
    assert meta_res.status_code == 200
    assert meta_res.json()["id"] == resume_data["id"]

    # Download resume
    download_res = client.get("/api/candidate/resume/download", headers=headers)
    assert download_res.status_code == 200
    assert download_res.content == mock_pdf_content

    # Replace resume
    new_mock_pdf = b"%PDF-1.4\nNew Updated Resume Content\n%%EOF"
    replace_file = io.BytesIO(new_mock_pdf)
    replace_res = client.post(
        "/api/candidate/resume/upload",
        files={"file": ("updated_resume.pdf", replace_file, "application/pdf")},
        headers=headers,
    )
    assert replace_res.status_code == 200
    assert replace_res.json()["original_filename"] == "updated_resume.pdf"

    # Delete resume
    del_res = client.delete("/api/candidate/resume", headers=headers)
    assert del_res.status_code == 200

    # Ensure metadata now 404s
    assert client.get("/api/candidate/resume", headers=headers).status_code == 404


def test_job_discovery_active_filtering():
    """Public/Candidate discovery only surfaces ACTIVE jobs; DRAFT and ARCHIVED remain hidden."""
    recruiter_token, _ = register_user(client, "RECRUITER")
    r_headers = {"Authorization": f"Bearer {recruiter_token}"}

    # 1. Create a DRAFT job
    draft_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Secret Internal Tooling Engineer",
            "company_name": "Stealth Corp",
            "description": "Internal test description",
            "required_skills": "Python, Go",
            "qualification": "B.Tech",
            "experience_years": "2 years",
            "employment_type": "FULL_TIME",
            "work_location": "Remote",
            "status": "DRAFT",
        },
        headers=r_headers,
    )
    assert draft_res.status_code == 201
    draft_job_id = draft_res.json()["id"]

    # 2. Create an ACTIVE job
    active_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Lead Artificial Intelligence Architect",
            "company_name": "Nova Dynamics",
            "description": "Designing production LLM agent architectures",
            "required_skills": "Python, PyTorch, Vector DB",
            "qualification": "M.S. in CS",
            "experience_years": "5+ years",
            "employment_type": "REMOTE",
            "work_location": "Remote - Worldwide",
            "status": "ACTIVE",
        },
        headers=r_headers,
    )
    assert active_res.status_code == 201
    active_job_id = active_res.json()["id"]

    # 3. Query public discovery endpoint
    disc_res = client.get("/api/jobs")
    assert disc_res.status_code == 200
    jobs = disc_res.json()
    job_ids = [j["id"] for j in jobs]

    # Active job must be present; Draft job must NOT be present
    assert active_job_id in job_ids
    assert draft_job_id not in job_ids

    # Query details for active job -> 200
    assert client.get(f"/api/jobs/{active_job_id}").status_code == 200
    # Query details for draft job -> 404
    assert client.get(f"/api/jobs/{draft_job_id}").status_code == 404

    # Search filter check
    search_res = client.get("/api/jobs?q=Artificial+Intelligence")
    assert search_res.status_code == 200
    search_ids = [j["id"] for j in search_res.json()]
    assert active_job_id in search_ids


def test_job_application_and_duplicate_prevention():
    """Candidate can apply to an active job; duplicate applications are prevented."""
    recruiter_token, _ = register_user(client, "RECRUITER")
    r_headers = {"Authorization": f"Bearer {recruiter_token}"}

    job_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Senior Backend Specialist",
            "company_name": "Apex Cloud Systems",
            "description": "Microservices architect",
            "required_skills": "FastAPI, PostgreSQL",
            "qualification": "BS",
            "experience_years": "3 years",
            "employment_type": "FULL_TIME",
            "work_location": "Seattle, WA",
            "status": "ACTIVE",
        },
        headers=r_headers,
    )
    assert job_res.status_code == 201
    job_id = job_res.json()["id"]

    candidate_token, cand_user = register_user(client, "CANDIDATE")
    c_headers = {"Authorization": f"Bearer {candidate_token}"}

    # Upload resume first
    mock_pdf = io.BytesIO(b"%PDF-1.4 Mock Application Resume\n%%EOF")
    client.post(
        "/api/candidate/resume/upload",
        files={"file": ("my_resume.pdf", mock_pdf, "application/pdf")},
        headers=c_headers,
    )

    # Submit application
    apply_res = client.post(
        "/api/candidate/applications",
        json={"job_id": job_id, "cover_letter": "I am excited to apply for this backend position."},
        headers=c_headers,
    )
    assert apply_res.status_code == 201
    app_data = apply_res.json()
    assert app_data["job_id"] == job_id
    assert app_data["status"] == "APPLIED"
    assert app_data["resume_id"] is not None

    # Duplicate application must fail with 400
    duplicate_res = client.post(
        "/api/candidate/applications",
        json={"job_id": job_id, "cover_letter": "Duplicate application attempt."},
        headers=c_headers,
    )
    assert duplicate_res.status_code == 400
    assert "already submitted" in duplicate_res.json()["detail"].lower()


def test_candidate_applications_isolation():
    """Candidates can only see their own applications; cannot view other candidates' applications."""
    recruiter_token, _ = register_user(client, "RECRUITER")
    r_headers = {"Authorization": f"Bearer {recruiter_token}"}

    job_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Cloud Platform Engineer",
            "company_name": "Skyline Tech",
            "description": "DevOps role",
            "required_skills": "Terraform, Docker",
            "qualification": "BS",
            "experience_years": "2 years",
            "work_location": "Austin, TX",
            "status": "ACTIVE",
        },
        headers=r_headers,
    )
    job_id = job_res.json()["id"]

    # Candidate 1
    c1_token, _ = register_user(client, "CANDIDATE")
    c1_headers = {"Authorization": f"Bearer {c1_token}"}
    app1_res = client.post(
        "/api/candidate/applications",
        json={"job_id": job_id},
        headers=c1_headers,
    )
    assert app1_res.status_code == 201
    app1_id = app1_res.json()["id"]

    # Candidate 2
    c2_token, _ = register_user(client, "CANDIDATE")
    c2_headers = {"Authorization": f"Bearer {c2_token}"}

    # Candidate 2 lists applications -> must be empty
    c2_list = client.get("/api/candidate/applications", headers=c2_headers).json()
    assert len(c2_list) == 0

    # Candidate 2 tries to view Candidate 1's application -> 403 Forbidden
    forbidden_res = client.get(f"/api/candidate/applications/{app1_id}", headers=c2_headers)
    assert forbidden_res.status_code == 403


def test_candidate_dashboard_stats():
    """Dashboard metrics accurately compute profile completion and application counters."""
    token, _ = register_user(client, "CANDIDATE")
    headers = {"Authorization": f"Bearer {token}"}

    # Initial stats
    stats_res = client.get("/api/candidate/dashboard/stats", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_applications"] == 0
    assert stats["profile_completion_percentage"] >= 20  # Name + email pre-filled
    assert stats["has_resume"] is False
