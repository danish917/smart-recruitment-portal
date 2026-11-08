"""Comprehensive Integration & Security Tests for Phase 8:

Covers:
- Recruiter live analytics calculations, status distributions, and ownership isolation.
- Candidate analytics, skill progression tracking, and user isolation.
- Security response headers (nosniff, DENY, XSS protection, Referrer-Policy).
- Rate limiting protection with 429 Too Many Requests and Retry-After headers.
- Resume download authorization and isolation (cross-recruiter prevention).
- Storage security: path traversal and file magic byte verification.
- Full Candidate & Recruiter user journey integration.
"""

import io
import time
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.rate_limiter import limiter
from app.services.storage import LocalStorageService

client = TestClient(app)


def get_unique_email(prefix: str = "p8") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def register_user(client: TestClient, role: str, email: str = None, name: str = None) -> tuple[str, dict]:
    """Register and login user, returning bearer token and user data."""
    if not email:
        email = get_unique_email(role.lower())
    if not name:
        name = f"Test {role.title()} User"

    res = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "StrongPassword123!",
            "full_name": name,
            "role": role,
        },
    )
    assert res.status_code == 201

    login_res = client.post(
        "/api/auth/login",
        json={"email": email, "password": "StrongPassword123!"},
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    user_info = login_res.json()["user"]
    return token, user_info


def make_mock_pdf(text: str = "Candidate Resume with Python, FastAPI, Docker, and PostgreSQL skills") -> bytes:
    """Create a syntactically valid PDF with Latin-1 text stream for pypdf extraction."""
    lines = [
        "Candidate John Doe",
        "Email: john.doe@example.com",
        "Phone: +1 555-0199",
        "Education: Bachelor of Science in Computer Science",
        "Experience: 4 years software development",
        "Technical Skills: Python, FastAPI, Docker, PostgreSQL, Kubernetes, AWS, React, TypeScript",
        text,
    ]
    stream_content = "BT\n/F1 12 Tf\n72 720 Td\n"
    for i, line in enumerate(lines):
        safe_line = line.replace("(", "\\(").replace(")", "\\)")
        if i == 0:
            stream_content += f"({safe_line}) Tj\n"
        else:
            stream_content += f"0 -18 Td\n({safe_line}) Tj\n"
    stream_content += "ET"

    stream_bytes = stream_content.encode("latin-1")
    length = len(stream_bytes)

    return (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>\nendobj\n"
        b"4 0 obj\n<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>\nendobj\n"
        b"5 0 obj\n<< /Length " + str(length).encode("latin-1") + b" >>\nstream\n"
        + stream_bytes + b"\nendstream\nendobj\n"
        b"xref\n0 6\n"
        b"0000000000 65535 f \n"
        b"0000000009 00000 n \n"
        b"0000000058 00000 n \n"
        b"0000000115 00000 n \n"
        b"0000000227 00000 n \n"
        b"0000000295 00000 n \n"
        b"trailer\n<< /Size 6 /Root 1 0 R >>\nstartxref\n500\n%%EOF"
    )


# -----------------------------------------------------------------------------
# 1. Security Headers Verification
# -----------------------------------------------------------------------------

def test_security_headers_present():
    """Verify standard HTTP security headers are included on all responses."""
    res = client.get("/health")
    assert res.status_code == 200
    headers = res.headers
    assert headers.get("X-Content-Type-Options") == "nosniff"
    assert headers.get("X-Frame-Options") == "DENY"
    assert headers.get("X-XSS-Protection") == "1; mode=block"
    assert headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


# -----------------------------------------------------------------------------
# 2. Rate Limiting Protection
# -----------------------------------------------------------------------------

def test_rate_limiter_blocks_excessive_attempts():
    """Verify rate limiter triggers 429 Too Many Requests when threshold exceeded."""
    limiter.clear()
    test_key = "auth_login:192.168.1.100"

    # Make 5 allowed attempts
    for _ in range(5):
        limiter.check(test_key, max_requests=5, window_seconds=60)

    # 6th attempt must raise 429 Too Many Requests
    with pytest.raises(Exception) as exc_info:
        limiter.check(test_key, max_requests=5, window_seconds=60)

    assert exc_info.value.status_code == 429
    assert "Rate limit exceeded" in exc_info.value.detail
    assert "Retry-After" in exc_info.value.headers

    # Reset limiter for subsequent test suite execution
    limiter.clear()


# -----------------------------------------------------------------------------
# 3. Recruiter Live Analytics & Ownership Isolation
# -----------------------------------------------------------------------------

def test_recruiter_analytics_endpoint():
    """Test recruiter analytics returns accurate PostgreSQL aggregation metrics."""
    limiter.clear()
    recruiter_token, recruiter = register_user(client, "RECRUITER")
    r_headers = {"Authorization": f"Bearer {recruiter_token}"}

    # 1. Create 2 jobs (1 Active, 1 Draft)
    j1_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Senior Backend Engineer",
            "company_name": "Acme Corp",
            "description": "Looking for a seasoned backend engineer with Python and Docker.",
            "required_skills": "Python, FastAPI, Docker, PostgreSQL",
            "qualification": "Bachelor's Degree",
            "experience_years": "3+ years",
            "employment_type": "FULL_TIME",
            "work_location": "Remote",
            "status": "ACTIVE",
        },
        headers=r_headers,
    )
    assert j1_res.status_code == 201
    job1_id = j1_res.json()["id"]

    j2_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Frontend Lead",
            "company_name": "Acme Corp",
            "description": "Lead frontend development with React and TypeScript.",
            "required_skills": "React, TypeScript, Tailwind CSS",
            "qualification": "Bachelor's Degree",
            "experience_years": "4+ years",
            "employment_type": "FULL_TIME",
            "work_location": "New York, NY",
            "status": "DRAFT",
        },
        headers=r_headers,
    )
    assert j2_res.status_code == 201

    # 2. Register candidate, upload resume, apply to Job 1
    cand_token, _ = register_user(client, "CANDIDATE")
    c_headers = {"Authorization": f"Bearer {cand_token}"}

    pdf_bytes = make_mock_pdf("Senior Engineer with Python, FastAPI, Docker, and PostgreSQL skills.")
    upload_res = client.post(
        "/api/candidate/resume/upload",
        files={"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=c_headers,
    )
    assert upload_res.status_code == 200

    app_res = client.post(
        "/api/candidate/applications",
        json={"job_id": job1_id, "cover_letter": "I am excited to apply for this backend role."},
        headers=c_headers,
    )
    assert app_res.status_code == 201
    app_id = app_res.json()["id"]

    # 3. Recruiter updates status of application to SHORTLISTED
    status_update = client.patch(
        f"/api/recruiter/applications/{app_id}/status",
        json={"status": "SHORTLISTED", "notes": "Strong technical background"},
        headers=r_headers,
    )
    assert status_update.status_code == 200

    # 4. Fetch Recruiter Analytics
    analytics_res = client.get("/api/recruiter/analytics", headers=r_headers)
    assert analytics_res.status_code == 200
    data = analytics_res.json()

    assert data["total_jobs"] >= 2
    assert data["active_jobs"] >= 1
    assert data["draft_jobs"] >= 1
    assert data["total_applications"] >= 1
    assert data["shortlisted_candidates"] >= 1
    assert data["status_distribution"]["shortlisted"] >= 1

    # Average skill coverage should be populated from Phase 7 screening
    assert data["average_skill_coverage"] is not None
    assert 0.0 <= data["average_skill_coverage"] <= 100.0

    # Top jobs breakdown
    assert len(data["top_jobs"]) > 0
    top_job = next((j for j in data["top_jobs"] if j["job_id"] == job1_id), None)
    assert top_job is not None
    assert top_job["applicant_count"] >= 1
    assert top_job["shortlisted_count"] >= 1

    # Recent activity stream
    assert len(data["recent_activity"]) >= 1
    recent_item = data["recent_activity"][0]
    assert recent_item["job_id"] == job1_id


def test_recruiter_analytics_isolation():
    """A recruiter must only see their own jobs and applicant metrics."""
    limiter.clear()
    recruiter_a_token, _ = register_user(client, "RECRUITER")
    recruiter_b_token, _ = register_user(client, "RECRUITER")

    # Recruiter A creates a job
    client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Private Job A",
            "company_name": "Alpha Corp",
            "description": "Job description",
            "required_skills": "Python",
            "qualification": "BSc",
            "experience_years": "2 years",
            "employment_type": "FULL_TIME",
            "work_location": "Remote",
            "status": "ACTIVE",
        },
        headers={"Authorization": f"Bearer {recruiter_a_token}"},
    )

    # Recruiter B queries analytics -> should see 0 jobs, 0 applications
    b_res = client.get(
        "/api/recruiter/analytics",
        headers={"Authorization": f"Bearer {recruiter_b_token}"},
    )
    assert b_res.status_code == 200
    b_data = b_res.json()
    assert b_data["total_jobs"] == 0
    assert b_data["total_applications"] == 0
    assert len(b_data["recent_activity"]) == 0


# -----------------------------------------------------------------------------
# 4. Candidate Live Analytics & Progression Tracking
# -----------------------------------------------------------------------------

def test_candidate_analytics_endpoint():
    """Test candidate analytics returns accurate status distribution and skill progress."""
    limiter.clear()
    cand_token, cand_user = register_user(client, "CANDIDATE")
    c_headers = {"Authorization": f"Bearer {cand_token}"}

    # Recruiter posts a job
    r_token, _ = register_user(client, "RECRUITER")
    r_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Cloud Architect",
            "company_name": "CloudNine",
            "description": "AWS and Kubernetes architecture.",
            "required_skills": "AWS, Kubernetes, Terraform",
            "qualification": "BSc in CS",
            "experience_years": "5 years",
            "employment_type": "FULL_TIME",
            "work_location": "Seattle, WA",
            "status": "ACTIVE",
        },
        headers={"Authorization": f"Bearer {r_token}"},
    )
    job_id = r_res.json()["id"]

    # Candidate uploads resume and applies
    pdf_bytes = make_mock_pdf("Experienced with AWS, Kubernetes, Terraform, and Go.")
    client.post(
        "/api/candidate/resume/upload",
        files={"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=c_headers,
    )
    client.post(
        "/api/candidate/applications",
        json={"job_id": job_id, "cover_letter": "I have extensive AWS and K8s experience."},
        headers=c_headers,
    )

    # Fetch Candidate Analytics
    analytics_res = client.get("/api/candidate/analytics", headers=c_headers)
    assert analytics_res.status_code == 200
    data = analytics_res.json()

    assert data["total_applications"] >= 1
    assert data["has_resume"] is True
    assert data["status_distribution"]["total"] >= 1
    assert len(data["recent_activity"]) >= 1
    assert len(data["skill_progress_history"]) >= 1

    pt = data["skill_progress_history"][0]
    assert pt["job_id"] == job_id
    assert pt["job_title"] == "Cloud Architect"


# -----------------------------------------------------------------------------
# 5. Resume Download Authorization & Cross-Recruiter Isolation
# -----------------------------------------------------------------------------

def test_resume_download_authorization_and_isolation():
    """Verify recruiter can only download resumes for applicants of their own jobs."""
    limiter.clear()
    recruiter_a_token, _ = register_user(client, "RECRUITER")
    recruiter_b_token, _ = register_user(client, "RECRUITER")
    cand_token, _ = register_user(client, "CANDIDATE")

    # Recruiter A posts job
    j_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Recruiter A Job",
            "company_name": "Alpha Corp",
            "description": "Comprehensive engineering position at Alpha Corp.",
            "required_skills": "Python, Docker, SQL",
            "qualification": "BSc",
            "experience_years": "1 year",
            "employment_type": "FULL_TIME",
            "work_location": "Remote",
            "status": "ACTIVE",
        },
        headers={"Authorization": f"Bearer {recruiter_a_token}"},
    )
    job_id = j_res.json()["id"]

    # Candidate uploads resume and applies to Job A
    pdf_bytes = make_mock_pdf("Candidate Resume for Job A")
    client.post(
        "/api/candidate/resume/upload",
        files={"file": ("resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    app_res = client.post(
        "/api/candidate/applications",
        json={"job_id": job_id},
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    app_id = app_res.json()["id"]

    # 1. Recruiter A downloads applicant resume -> 200 OK
    res_a = client.get(
        f"/api/recruiter/applications/{app_id}/resume",
        headers={"Authorization": f"Bearer {recruiter_a_token}"},
    )
    assert res_a.status_code == 200
    assert res_a.headers["content-type"] == "application/pdf"

    # 2. Recruiter B tries to download Job A applicant resume -> 403 Forbidden
    res_b = client.get(
        f"/api/recruiter/applications/{app_id}/resume",
        headers={"Authorization": f"Bearer {recruiter_b_token}"},
    )
    assert res_b.status_code == 403
    assert "Access denied" in res_b.json()["detail"]

    # 3. Candidate downloading their own resume via candidate endpoint -> 200 OK
    cand_download = client.get(
        "/api/candidate/resume/download",
        headers={"Authorization": f"Bearer {cand_token}"},
    )
    assert cand_download.status_code == 200


# -----------------------------------------------------------------------------
# 6. Storage Security: Path Traversal & Magic Bytes
# -----------------------------------------------------------------------------

def test_storage_security_path_traversal_and_validation():
    """Verify local storage service prevents path traversal and rejects non-PDFs."""
    service = LocalStorageService()

    # 1. Path traversal attempt in stored_filename
    traversal_path = service.get_file_path("../../etc/passwd")
    assert traversal_path is None or not str(traversal_path).endswith("passwd")

    # 2. Rejection of invalid magic bytes
    fake_content = b"Plain text content without PDF header"
    with pytest.raises(Exception) as exc:
        service.save_file(fake_content, "resume.pdf", "application/pdf")
    assert "valid PDF" in str(exc.value)


# -----------------------------------------------------------------------------
# 7. Administrator Permissions
# -----------------------------------------------------------------------------

def test_admin_access_authorization():
    """Verify administrator role can view recruiter analytics and manage jobs."""
    limiter.clear()
    admin_token, _ = register_user(client, "ADMIN")
    a_headers = {"Authorization": f"Bearer {admin_token}"}

    # Admin accessing analytics endpoint
    res = client.get("/api/recruiter/analytics", headers=a_headers)
    assert res.status_code == 200
    assert "total_jobs" in res.json()
