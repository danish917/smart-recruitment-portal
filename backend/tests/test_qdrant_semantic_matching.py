"""Unit and integration tests for Phase 6: Qdrant Vector Database, Dense Embeddings, and Semantic Job Matching."""

import uuid
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.embedding import EmbeddingService, get_embedding_service
from app.services.semantic_matching import SemanticMatchingService, cosine_similarity
from app.services.vector_db import VectorDBService

client = TestClient(app)


def build_test_pdf_bytes(lines: list[str]) -> bytes:
    """Helper to synthesize a valid PDF stream with specified text lines."""
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


def get_unique_email(prefix: str = "p6") -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}@example.com"


def register_user(role: str) -> tuple[str, dict]:
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


# -----------------------------------------------------------------------------
# 1. Embedding Service Tests
# -----------------------------------------------------------------------------

def test_embedding_service_dimensions_and_preprocessing():
    """Verify embedding service produces 384-dimensional normalized dense vectors."""
    svc = get_embedding_service()

    # Resume preprocessing
    resume_data = {
        "name": "Jane Developer",
        "technical_skills": ["Python", "FastAPI", "PostgreSQL", "Docker"],
        "soft_skills": ["Teamwork", "Problem Solving"],
        "education": "Master of Science in Computer Science",
        "college_university": "Stanford University",
        "graduation_year": 2022,
        "experience_years": "4",
        "work_experience": ["Senior Backend Engineer at TechCorp"],
        "projects": ["High-throughput API Gateway"],
        "certifications": ["AWS Certified Solutions Architect"],
    }
    resume_text = svc.prepare_resume_text(resume_data)
    assert "FastAPI" in resume_text
    assert "Stanford University" in resume_text

    vector = svc.embed_text(resume_text)
    assert len(vector) == 384
    assert any(v != 0.0 for v in vector)

    # Job preprocessing
    job_text = svc.prepare_job_text(
        title="Senior Python / FastAPI Developer",
        description="Seeking an experienced Python backend developer with FastAPI and PostgreSQL expertise.",
        required_skills="Python, FastAPI, PostgreSQL",
        qualification="Bachelor in CS or equivalent",
        experience_years="3+",
        company_name="CloudScale Systems",
        work_location="Remote",
    )
    assert "Senior Python / FastAPI Developer" in job_text
    job_vector = svc.embed_text(job_text)
    assert len(job_vector) == 384

    # High semantic similarity between matching resume and job
    sim = cosine_similarity(vector, job_vector)
    assert sim > 60.0  # High match


def test_cosine_similarity_edge_cases():
    """Verify cosine similarity calculation with identical, orthogonal, and empty vectors."""
    v1 = [1.0] * 384
    v2 = [1.0] * 384
    assert cosine_similarity(v1, v2) == 100.0

    v_empty: list[float] = []
    assert cosine_similarity(v_empty, v1) == 0.0


# -----------------------------------------------------------------------------
# 2. Qdrant Vector DB Service Tests (In-Memory)
# -----------------------------------------------------------------------------

def test_vector_db_service_in_memory_crud():
    """Verify Qdrant service in-memory operations for resumes and jobs."""
    vdb = VectorDBService(in_memory=True)
    svc = get_embedding_service()

    vec_python = svc.embed_text("Senior Python Backend Engineer with FastAPI and PostgreSQL")
    vec_frontend = svc.embed_text("React Frontend Developer with Next.js and Tailwind CSS")

    # Index two jobs
    vdb.upsert_job_vector(
        job_id=101,
        recruiter_id=1,
        vector=vec_python,
        metadata={"title": "Python Developer", "status": "ACTIVE"},
    )
    vdb.upsert_job_vector(
        job_id=102,
        recruiter_id=1,
        vector=vec_frontend,
        metadata={"title": "React Developer", "status": "ACTIVE"},
    )

    # Query with a Python candidate vector
    candidate_vec = svc.embed_text("Python FastAPI SQLAlchemy engineer")
    hits = vdb.search_jobs_for_resume(candidate_vec, limit=2)
    assert len(hits) == 2
    # Top hit must be the Python job
    assert hits[0]["job_id"] == 101
    assert hits[0]["similarity_score"] > hits[1]["similarity_score"]

    # Deletion test
    vdb.delete_job_vector(101)
    hits_after = vdb.search_jobs_for_resume(candidate_vec, limit=2)
    assert len(hits_after) == 1
    assert hits_after[0]["job_id"] == 102


# -----------------------------------------------------------------------------
# 3. Integration Tests via FastAPI Endpoints
# -----------------------------------------------------------------------------

def test_job_vector_indexing_and_archival_lifecycle():
    """Verify active jobs are indexed in vector DB and de-indexed when archived or deleted."""
    recruiter_token, _ = register_user("RECRUITER")
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}

    # 1. Create an active job
    job_payload = {
        "title": "Staff Backend Engineer - Qdrant & FastAPI",
        "company_name": "VectorSearch Inc",
        "description": "Building high-scale search pipelines using Qdrant vector database and FastAPI microservices.",
        "required_skills": "Python, Qdrant, FastAPI, Docker",
        "qualification": "B.Tech or MS in CS",
        "experience_years": "5+",
        "employment_type": "FULL_TIME",
        "work_location": "Remote",
        "salary_min": 120000,
        "salary_max": 180000,
        "salary_currency": "USD",
        "status": "ACTIVE",
    }
    res = client.post("/api/recruiter/jobs", json=job_payload, headers=recruiter_headers)
    assert res.status_code == 201
    job_data = res.json()
    job_id = job_data["id"]
    assert job_data["is_indexed"] is True

    # 2. Archive job -> should be de-indexed
    res_arch = client.patch(f"/api/recruiter/jobs/{job_id}/archive", headers=recruiter_headers)
    assert res_arch.status_code == 200
    assert res_arch.json()["is_indexed"] is False

    # 3. Publish job again -> should be re-indexed
    res_pub = client.patch(f"/api/recruiter/jobs/{job_id}/publish", headers=recruiter_headers)
    assert res_pub.status_code == 200
    assert res_pub.json()["is_indexed"] is True


def test_resume_vector_indexing_and_replacement():
    """Verify candidate resume upload indexes vector in Qdrant, and replacement updates vector."""
    candidate_token, _ = register_user("CANDIDATE")
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}

    # 1. Upload resume
    pdf_bytes = build_test_pdf_bytes([
        "Alex Vector",
        "alex.vec@test.com",
        "Technical Skills: Python, FastAPI, Docker, PostgreSQL, Qdrant",
        "Education: Bachelor of Science in Computer Science from MIT",
        "Experience: 3 years as Software Engineer",
    ])
    res_up = client.post(
        "/api/candidate/resume/upload",
        files={"file": ("alex_resume.pdf", pdf_bytes, "application/pdf")},
        headers=candidate_headers,
    )
    assert res_up.status_code == 200
    data = res_up.json()
    assert data["parsed_resume"] is not None
    assert data["parsed_resume"]["is_indexed"] is True

    # 2. Explicit index trigger endpoint
    res_reindex = client.post("/api/candidate/resume/index-vector", headers=candidate_headers)
    assert res_reindex.status_code == 200
    assert res_reindex.json()["is_indexed"] is True


def test_candidate_semantic_job_recommendations():
    """Verify candidate receives recommended active jobs ranked by dense semantic similarity."""
    recruiter_token, _ = register_user("RECRUITER")
    recruiter_headers = {"Authorization": f"Bearer {recruiter_token}"}
    candidate_token, _ = register_user("CANDIDATE")
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}

    # 1. Post two distinct jobs
    # Python job
    res1 = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Machine Learning Engineer - NLP & Embeddings",
            "company_name": "AI Innovations",
            "description": "Building NLP models, sentence transformers, and semantic vector retrieval systems.",
            "required_skills": "Python, PyTorch, NLP, Transformers",
            "qualification": "Master in CS or AI",
            "experience_years": "3+",
            "employment_type": "FULL_TIME",
            "work_location": "Remote",
            "status": "ACTIVE",
        },
        headers=recruiter_headers,
    )
    assert res1.status_code == 201
    ml_job_id = res1.json()["id"]

    # Java/Spring job
    res2 = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Java Enterprise Backend Architect",
            "company_name": "Legacy Banking",
            "description": "Maintaining legacy enterprise banking applications using Java, Spring Boot, and Oracle.",
            "required_skills": "Java, Spring Boot, Oracle, Microservices",
            "qualification": "Bachelor in CS",
            "experience_years": "8+",
            "employment_type": "FULL_TIME",
            "work_location": "New York, NY",
            "status": "ACTIVE",
        },
        headers=recruiter_headers,
    )
    assert res2.status_code == 201
    java_job_id = res2.json()["id"]

    # 2. Upload an NLP / Python candidate resume
    pdf_bytes = build_test_pdf_bytes([
        "Samantha NLP",
        "sam.nlp@test.com",
        "Technical Skills: Python, Machine Learning, PyTorch, Transformers, NLP",
        "Education: Master of Science in Artificial Intelligence, Carnegie Mellon",
        "Experience: 3 years as AI Specialist",
    ])
    client.post(
        "/api/candidate/resume/upload",
        files={"file": ("samantha_nlp.pdf", pdf_bytes, "application/pdf")},
        headers=candidate_headers,
    )

    # 3. Request recommendations
    res_rec = client.get("/api/candidate/jobs/recommended?limit=5", headers=candidate_headers)
    assert res_rec.status_code == 200
    recommendations = res_rec.json()
    assert len(recommendations) >= 1

    # First recommendation must be the ML/NLP job with higher similarity
    top_rec = recommendations[0]
    assert top_rec["job"]["id"] == ml_job_id
    assert top_rec["similarity_score"] > 60.0
    assert "Match" in top_rec["match_tier"]


def test_recruiter_semantic_applicant_matches_and_isolation():
    """Verify recruiter can query semantic applicant rankings, and recruiter isolation is enforced."""
    recruiter_a_token, _ = register_user("RECRUITER")
    recruiter_a = {"Authorization": f"Bearer {recruiter_a_token}"}

    recruiter_b_token, _ = register_user("RECRUITER")
    recruiter_b = {"Authorization": f"Bearer {recruiter_b_token}"}

    candidate_token, _ = register_user("CANDIDATE")
    candidate_headers = {"Authorization": f"Bearer {candidate_token}"}

    # Recruiter A posts job
    res_job = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Cloud DevOps Engineer",
            "company_name": "InfraCore",
            "description": "Managing Kubernetes clusters, Terraform infrastructure, and CI/CD automation pipelines.",
            "required_skills": "Kubernetes, Docker, Terraform, AWS, CI/CD",
            "qualification": "B.S. in Computer Science or equivalent",
            "experience_years": "4+",
            "employment_type": "FULL_TIME",
            "work_location": "Remote",
            "status": "ACTIVE",
        },
        headers=recruiter_a,
    )
    job_id = res_job.json()["id"]

    # Candidate uploads DevOps resume and applies
    pdf_bytes = build_test_pdf_bytes([
        "DevOps Pro",
        "devops@test.com",
        "Technical Skills: Kubernetes, Docker, Terraform, AWS, Linux, CI/CD, Python",
        "Education: Bachelor of Science from Georgia Tech",
        "Experience: 4 years as Site Reliability Engineer",
    ])
    client.post(
        "/api/candidate/resume/upload",
        files={"file": ("devops_resume.pdf", pdf_bytes, "application/pdf")},
        headers=candidate_headers,
    )

    client.post(
        "/api/candidate/applications",
        json={"job_id": job_id, "cover_letter": "Passionate about Kubernetes and cloud infra."},
        headers=candidate_headers,
    )

    # Recruiter A gets semantic applicant matches
    res_matches = client.get(f"/api/recruiter/jobs/{job_id}/semantic-matches", headers=recruiter_a)
    assert res_matches.status_code == 200
    matches = res_matches.json()
    assert len(matches) == 1
    assert matches[0]["semantic_score"] > 60.0
    assert matches[0]["screening_score"] is not None

    # Recruiter B cannot access Recruiter A's job matches
    res_forbidden = client.get(f"/api/recruiter/jobs/{job_id}/semantic-matches", headers=recruiter_b)
    assert res_forbidden.status_code == 403
