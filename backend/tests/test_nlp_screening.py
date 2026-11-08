"""Automated tests for Phase 5: AI Resume Parsing & Intelligent Screening."""

import io
import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.models.screening import ParsingStatus
from app.services.nlp_parser import (
    extract_text_from_pdf,
    parse_resume_text,
)
from app.services.screening import screen_candidate_resume

client = TestClient(app)


def build_test_pdf_bytes(lines: list[str]) -> bytes:
    """Helper to synthesize a valid PDF stream with specified text lines."""
    stream_content = "BT\n/F1 12 Tf\n72 720 Td\n"
    for i, line in enumerate(lines):
        # Escape parentheses in PDF text
        safe_line = line.replace("(", "\\(").replace(")", "\\)")
        if i == 0:
            stream_content += f"({safe_line}) Tj\n"
        else:
            stream_content += f"0 -18 Td\n({safe_line}) Tj\n"
    stream_content += "ET"

    stream_bytes = stream_content.encode("latin-1")
    length = len(stream_bytes)

    pdf = (
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
    return pdf


def get_unique_email(prefix: str = "cand") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def register_user(client: TestClient, role: str) -> tuple[str, dict]:
    email = get_unique_email(role.lower())
    res = client.post(
        "/api/auth/register",
        json={
            "email": email,
            "password": "Password123!",
            "full_name": f"Test {role.title()} User",
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
    user = login_res.json()["user"]
    return token, user


def test_pdf_text_extraction_valid():
    """Valid PDF extracts text and returns status PARSED."""
    lines = [
        "Jane Doe",
        "jane.doe@example.com",
        "Technical Skills: Python, FastAPI, Docker, PostgreSQL",
        "Education: Master of Science, Stanford University",
    ]
    pdf_bytes = build_test_pdf_bytes(lines)
    text, status, err = extract_text_from_pdf(pdf_bytes)

    assert status == ParsingStatus.PARSED
    assert err is None
    assert "Jane Doe" in text
    assert "FastAPI" in text


def test_pdf_extraction_empty_or_corrupt():
    """Empty or corrupt bytes are handled gracefully with FAILED status."""
    # Empty bytes
    text, status, err = extract_text_from_pdf(b"")
    assert status == ParsingStatus.FAILED
    assert "empty" in err.lower()

    # Corrupt bytes
    corrupt_bytes = b"%PDF-1.4\nInvalid non-pdf binary junk\xff\xfe\x00\x01%%EOF"
    text, status, err = extract_text_from_pdf(corrupt_bytes)
    assert status == ParsingStatus.FAILED
    assert err is not None


def test_pdf_scanned_ocr_required_detection():
    """PDF with near-zero extractable text triggers OCR_REQUIRED status."""
    # 5 bytes of text
    pdf_bytes = build_test_pdf_bytes(["Hi"])
    text, status, err = extract_text_from_pdf(pdf_bytes)
    assert status == ParsingStatus.OCR_REQUIRED
    assert "OCR" in err


def test_nlp_resume_parsing_rules_and_taxonomies():
    """Structured parser extracts skills, education, experience without inventing data."""
    raw_text = """
    Alex Rivera
    alex.rivera@example.com | (555) 234-5678
    
    Professional Summary
    Senior Backend Engineer with 5+ years of experience designing scalable microservices.
    
    Technical Skills
    Languages: Python, TypeScript, Go, SQL
    Frameworks: FastAPI, Django, React, Next.js
    Cloud & DB: PostgreSQL, Redis, Docker, Kubernetes, AWS
    
    Soft Skills
    Leadership, Problem Solving, Communication, Teamwork
    
    Work Experience
    Software Engineer at Acme Corp
    Tech Lead leading 6 engineers
    
    Education
    Master of Science in Computer Science
    Stanford University, 2022
    
    Certifications
    AWS Certified Solutions Architect
    """

    parsed = parse_resume_text(raw_text)

    assert parsed["name"] == "Alex Rivera"
    assert parsed["email"] == "alex.rivera@example.com"
    assert "(555) 234-5678" in parsed["phone"]
    # Technical skills
    tech = parsed["technical_skills"]
    assert "Python" in tech
    assert "FastAPI" in tech
    assert "PostgreSQL" in tech
    assert "Docker" in tech
    assert "Kubernetes" in tech
    # Soft skills
    soft = parsed["soft_skills"]
    assert "Leadership" in soft
    assert "Problem Solving" in soft
    # Education
    assert "Master of Science" in parsed["education"]
    assert "Stanford University" in parsed["college_university"]
    assert parsed["graduation_year"] == 2022
    # Experience
    assert "5+ years" in parsed["experience_years"]
    assert "Software Engineer" in parsed["work_experience"]
    # Certifications
    assert any("AWS" in c for c in parsed["certifications"])


def test_nlp_parsing_missing_info_no_hallucination():
    """Missing fields return None or empty lists, never hallucinated values."""
    minimal_text = "Only Python and Communication mentioned here."
    parsed = parse_resume_text(minimal_text)

    assert parsed["name"] is None
    assert parsed["email"] is None
    assert parsed["phone"] is None
    assert parsed["technical_skills"] == ["Python"]
    assert parsed["soft_skills"] == ["Communication"]
    assert parsed["education"] is None
    assert parsed["college_university"] is None
    assert parsed["graduation_year"] is None
    assert parsed["experience_years"] is None
    assert parsed["projects"] == []
    assert parsed["certifications"] == []


def test_ai_screening_scoring_algorithm():
    """Test transparent explainable screening calculation against job criteria."""
    parsed_candidate = {
        "technical_skills": ["Python", "FastAPI", "Docker", "PostgreSQL", "React"],
        "soft_skills": ["Teamwork", "Communication"],
        "education": "Master of Science (M.S.)",
        "experience_years": "4+ years",
        "work_experience": ["Software Engineer"],
    }
    raw_text = "Experienced Python FastAPI Docker PostgreSQL engineer with 4+ years building APIs."

    # Job A: Strong Match
    result_a = screen_candidate_resume(
        job_title="Senior Python Backend Developer",
        job_description="Seeking a Python FastAPI backend developer with Docker and PostgreSQL experience.",
        required_skills="Python, FastAPI, Docker, PostgreSQL",
        qualification="Bachelor of Science",
        experience_years="3 years",
        parsed_data=parsed_candidate,
        raw_text=raw_text,
    )

    assert result_a["screening_score"] >= 80.0
    assert len(result_a["matched_skills"]) == 4
    assert len(result_a["missing_skills"]) == 0
    assert result_a["qualification_match"] is True
    assert result_a["experience_match"] is True
    assert "Overall Assessment: Strong Match" in result_a["explanation"]
    assert "Matched 4 required skill" in result_a["explanation"]

    # Job B: Partial / Limited Match
    result_b = screen_candidate_resume(
        job_title="Java Enterprise Architect",
        job_description="Seeking experienced Java Spring Boot engineer with Oracle and Kubernetes.",
        required_skills="Java, Spring Boot, Oracle, Kubernetes",
        qualification="Ph.D. in Computer Science",
        experience_years="8 years",
        parsed_data=parsed_candidate,
        raw_text=raw_text,
    )

    assert result_b["screening_score"] < 50.0
    assert "Java" in result_b["missing_skills"]
    assert "Spring Boot" in result_b["missing_skills"]
    assert result_b["qualification_match"] is False
    assert result_b["experience_match"] is False
    assert "Missing:" in result_b["explanation"]


def test_resume_upload_triggers_automated_nlp_and_storage():
    """Uploading resume triggers text extraction and stores parsed data in Neon PostgreSQL."""
    token, _ = register_user(client, "CANDIDATE")
    headers = {"Authorization": f"Bearer {token}"}

    lines = [
        "Morgan Lee",
        "morgan.lee@example.com",
        "Full Stack Developer with 3+ years experience.",
        "Skills: Python, FastAPI, TypeScript, React, PostgreSQL",
        "Education: Bachelor of Technology, Massachusetts Institute of Technology, 2021",
        "Projects: Built scalable microservice gateway",
    ]
    pdf_bytes = build_test_pdf_bytes(lines)

    res = client.post(
        "/api/candidate/resume/upload",
        files={"file": ("morgan_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=headers,
    )
    assert res.status_code == 200
    data = res.json()
    assert data["parsed_resume"] is not None
    assert data["parsed_resume"]["status"] == "PARSED"
    extracted = data["parsed_resume"]["extracted_data"]
    assert extracted["name"] == "Morgan Lee"
    assert "FastAPI" in extracted["technical_skills"]
    assert "PostgreSQL" in extracted["technical_skills"]

    # Inspect parsed resume endpoint directly
    parsed_res = client.get("/api/candidate/resume/parsed", headers=headers)
    assert parsed_res.status_code == 200
    assert parsed_res.json()["status"] == "PARSED"

    # Test re-parse endpoint
    reparse_res = client.post("/api/candidate/resume/reparse", headers=headers)
    assert reparse_res.status_code == 200
    assert reparse_res.json()["status"] == "PARSED"


def test_job_application_automatic_screening_and_recruiter_inspection():
    """Applying with parsed resume generates screening evaluation; recruiter can inspect applicants."""
    # 1. Recruiter creates job
    r_token, _ = register_user(client, "RECRUITER")
    r_headers = {"Authorization": f"Bearer {r_token}"}
    job_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Lead FastAPI Specialist",
            "company_name": "CloudNova Systems",
            "description": "Building high-performance Python FastAPI services with Docker and PostgreSQL.",
            "required_skills": "Python, FastAPI, PostgreSQL",
            "qualification": "B.Tech",
            "experience_years": "2 years",
            "work_location": "Remote",
            "status": "ACTIVE",
        },
        headers=r_headers,
    )
    assert job_res.status_code == 201
    job_id = job_res.json()["id"]

    # 2. Candidate uploads resume
    c_token, _ = register_user(client, "CANDIDATE")
    c_headers = {"Authorization": f"Bearer {c_token}"}

    lines = [
        "Taylor Swift",
        "taylor.backend@example.com",
        "Backend Developer with 3+ years experience.",
        "Skills: Python, FastAPI, PostgreSQL, Docker, Redis",
        "Education: Bachelor of Engineering, Cambridge University, 2021",
    ]
    pdf_bytes = build_test_pdf_bytes(lines)
    client.post(
        "/api/candidate/resume/upload",
        files={"file": ("taylor_resume.pdf", io.BytesIO(pdf_bytes), "application/pdf")},
        headers=c_headers,
    )

    # 3. Candidate applies for the job
    apply_res = client.post(
        "/api/candidate/applications",
        json={"job_id": job_id, "cover_letter": "Excited to join CloudNova!"},
        headers=c_headers,
    )
    assert apply_res.status_code == 201
    app_data = apply_res.json()
    assert app_data["screening"] is not None
    assert app_data["screening"]["screening_score"] >= 70.0
    assert "Python" in app_data["screening"]["matched_skills"]
    assert "FastAPI" in app_data["screening"]["matched_skills"]

    # 4. Recruiter inspects applicants
    recruiter_apps_res = client.get(
        f"/api/recruiter/jobs/{job_id}/applications",
        headers=r_headers,
    )
    assert recruiter_apps_res.status_code == 200
    apps_list = recruiter_apps_res.json()
    assert len(apps_list) >= 1
    target_app = apps_list[0]
    assert target_app["screening"] is not None
    assert target_app["screening"]["screening_score"] >= 70.0

    # 5. Recruiter on-demand re-screen endpoint
    screen_res = client.post(
        f"/api/recruiter/applications/{target_app['id']}/screen",
        headers=r_headers,
    )
    assert screen_res.status_code == 200
    assert screen_res.json()["screening_score"] >= 70.0

    # 6. Recruiter B (unauthorized) cannot access recruiter A's applicants or screening
    r2_token, _ = register_user(client, "RECRUITER")
    r2_headers = {"Authorization": f"Bearer {r2_token}"}
    forbidden_res = client.get(
        f"/api/recruiter/jobs/{job_id}/applications",
        headers=r2_headers,
    )
    assert forbidden_res.status_code == 403
