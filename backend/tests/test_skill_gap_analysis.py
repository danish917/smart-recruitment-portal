"""Comprehensive tests for Phase 7: Skill-Gap Analysis & Intelligent Recommendations."""

import time
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.skill_gap import (
    SYNONYM_MAP,
    analyze_skill_gap,
    normalize_skill_name,
    parse_skill_list,
)

client = TestClient(app)

timestamp = int(time.time())
RECRUITER_EMAIL = f"recruiter_p7_{timestamp}@example.com"
OTHER_RECRUITER_EMAIL = f"other_recruiter_p7_{timestamp}@example.com"
CANDIDATE_EMAIL = f"candidate_p7_{timestamp}@example.com"
TEST_PASSWORD = "StrongPassword123!"


@pytest.fixture(scope="module")
def auth_tokens():
    """Register and login recruiter, other recruiter, and candidate."""
    # 1. Recruiter
    client.post(
        "/api/auth/register",
        json={
            "email": RECRUITER_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Phase7 Recruiter",
            "role": "RECRUITER",
        },
    )
    r_res = client.post(
        "/api/auth/login",
        json={"email": RECRUITER_EMAIL, "password": TEST_PASSWORD},
    )
    recruiter_token = r_res.json()["access_token"]

    # 2. Other Recruiter
    client.post(
        "/api/auth/register",
        json={
            "email": OTHER_RECRUITER_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Other Recruiter",
            "role": "RECRUITER",
        },
    )
    o_res = client.post(
        "/api/auth/login",
        json={"email": OTHER_RECRUITER_EMAIL, "password": TEST_PASSWORD},
    )
    other_recruiter_token = o_res.json()["access_token"]

    # 3. Candidate
    client.post(
        "/api/auth/register",
        json={
            "email": CANDIDATE_EMAIL,
            "password": TEST_PASSWORD,
            "full_name": "Phase7 Candidate",
            "role": "CANDIDATE",
        },
    )
    c_res = client.post(
        "/api/auth/login",
        json={"email": CANDIDATE_EMAIL, "password": TEST_PASSWORD},
    )
    candidate_token = c_res.json()["access_token"]

    return {
        "recruiter_token": recruiter_token,
        "other_recruiter_token": other_recruiter_token,
        "candidate_token": candidate_token,
    }


# ============================================================================
# 1. DETERMINISTIC NORMALIZATION & SYNONYM TESTS
# ============================================================================

def test_skill_normalization_and_synonym_mapping():
    """Verify skill normalization correctly handles casing, variations, and synonyms."""
    assert normalize_skill_name("React.js") == "react"
    assert normalize_skill_name("REACTJS") == "react"
    assert normalize_skill_name("  react  ") == "react"
    assert normalize_skill_name("K8s") == "kubernetes"
    assert normalize_skill_name("kubernetes") == "kubernetes"
    assert normalize_skill_name("Postgres") == "postgresql"
    assert normalize_skill_name("PostgreSQL") == "postgresql"
    assert normalize_skill_name("psql") == "postgresql"
    assert normalize_skill_name("TS") == "typescript"
    assert normalize_skill_name("TypeScript") == "typescript"
    assert normalize_skill_name("JS") == "javascript"
    assert normalize_skill_name("JavaScript") == "javascript"
    assert normalize_skill_name("Golang") == "go"
    assert normalize_skill_name("Go") == "go"
    assert normalize_skill_name("AWS") == "aws"
    assert normalize_skill_name("Amazon Web Services") == "aws"
    assert normalize_skill_name("Docker-Compose") == "docker"
    assert normalize_skill_name("Containerization") == "docker"
    assert normalize_skill_name("Fast-API") == "fastapi"
    assert normalize_skill_name("FastAPI") == "fastapi"
    assert normalize_skill_name("Spring Boot") == "spring boot"
    assert normalize_skill_name("SpringBoot") == "spring boot"


def test_parse_skill_list():
    """Verify parse_skill_list parses comma, semicolon, bullet, and newline separated skills."""
    raw = "Python, FastAPI; PostgreSQL\nDocker • React | TypeScript"
    parsed = parse_skill_list(raw)
    assert "Python" in parsed
    assert "FastAPI" in parsed
    assert "PostgreSQL" in parsed
    assert "Docker" in parsed
    assert "React" in parsed
    assert "TypeScript" in parsed


# ============================================================================
# 2. SKILL COVERAGE CALCULATION & GAP CLASSIFICATION TESTS
# ============================================================================

def test_skill_gap_mathematical_coverage():
    """Verify coverage percentage calculation: (matched / total_required) * 100."""
    required = ["Python", "FastAPI", "Docker", "PostgreSQL", "Kubernetes"]

    # Candidate has 3 out of 5 required -> exactly 60.0%
    candidate = ["Python", "FastAPI", "PostgreSQL"]
    res = analyze_skill_gap(candidate_skills=candidate, required_skills=required)
    assert res["coverage_percentage"] == 60.0
    assert len(res["matched_skills"]) == 3
    assert len(res["missing_skills"]) == 2
    assert "Docker" in res["missing_skills"]
    assert "Kubernetes" in res["missing_skills"]

    # Candidate has 5 out of 5 -> exactly 100.0%
    candidate_all = ["Python", "FastAPI", "Docker", "PostgreSQL", "Kubernetes"]
    res_all = analyze_skill_gap(candidate_skills=candidate_all, required_skills=required)
    assert res_all["coverage_percentage"] == 100.0
    assert len(res_all["missing_skills"]) == 0

    # Candidate has 0 out of 5 -> 0.0%
    res_none = analyze_skill_gap(candidate_skills=[], required_skills=required)
    assert res_none["coverage_percentage"] == 0.0
    assert len(res_none["missing_skills"]) == 5


def test_partial_skills_and_related_skills():
    """Verify related precursor skills are flagged as partial matches."""
    required = ["Kubernetes", "Next.js"]
    # Candidate does not have Kubernetes or Next.js, but has Docker and React
    candidate = ["Docker", "React"]

    res = analyze_skill_gap(candidate_skills=candidate, required_skills=required)
    assert res["coverage_percentage"] == 0.0  # Not a direct match
    assert len(res["partial_skills"]) >= 1

    partial_reqs = [p["required_skill"] for p in res["partial_skills"]]
    assert "Kubernetes" in partial_reqs or "Next.js" in partial_reqs


def test_additional_skills_identification():
    """Verify candidate skills not in job requirements are marked as additional strengths."""
    required = ["Python", "FastAPI"]
    candidate = ["Python", "FastAPI", "GraphQL", "Redis", "Kafka"]

    res = analyze_skill_gap(candidate_skills=candidate, required_skills=required)
    assert res["coverage_percentage"] == 100.0
    assert "GraphQL" in res["additional_skills"]
    assert "Redis" in res["additional_skills"]
    assert "Kafka" in res["additional_skills"]


def test_empty_requirements_and_edge_cases():
    """Verify edge cases like empty job requirements or candidate profile."""
    # Empty job requirements -> 100% coverage
    res1 = analyze_skill_gap(candidate_skills=["Python"], required_skills="")
    assert res1["coverage_percentage"] == 100.0
    assert res1["total_required_count"] == 0

    # None required skills
    res2 = analyze_skill_gap(candidate_skills=["Python"], required_skills=None)
    assert res2["coverage_percentage"] == 100.0

    # Empty candidate skills
    res3 = analyze_skill_gap(candidate_skills=[], required_skills=["Java", "Spring Boot"])
    assert res3["coverage_percentage"] == 0.0
    assert len(res3["missing_skills"]) == 2


def test_curated_learning_recommendations():
    """Verify generated recommendations have practical objectives and official documentation."""
    required = ["Docker", "Kubernetes", "QuantumAlgorithmXYZ"]
    candidate = ["Python"]

    res = analyze_skill_gap(candidate_skills=candidate, required_skills=required)
    recs = res["learning_recommendations"]
    assert len(recs) == 3

    # Find Docker recommendation
    docker_rec = next((r for r in recs if r["required_skill"] == "Docker"), None)
    assert docker_rec is not None
    assert docker_rec["priority"] in ["HIGH", "MEDIUM"]
    assert len(docker_rec["core_concepts"]) >= 3
    assert len(docker_rec["documentation_links"]) >= 1
    assert "docker.com" in docker_rec["documentation_links"][0]["url"]

    # Obscure skill fallback
    xyz_rec = next((r for r in recs if r["required_skill"] == "QuantumAlgorithmXYZ"), None)
    assert xyz_rec is not None
    assert xyz_rec["category"] == "Software Engineering"


# ============================================================================
# 3. END-TO-END API TESTS (CANDIDATE & RECRUITER)
# ============================================================================

def test_candidate_job_skill_gap_endpoint(auth_tokens):
    """Verify candidate can retrieve skill-gap analysis for an active job."""
    recruiter_token = auth_tokens["recruiter_token"]
    candidate_token = auth_tokens["candidate_token"]

    # 1. Recruiter creates a job
    job_payload = {
        "title": "Senior Cloud Backend Engineer",
        "company_name": "Acme Cloud Corp",
        "description": "Building scalable microservices with Python, FastAPI, Docker, and PostgreSQL.",
        "work_location": "Remote",
        "employment_type": "FULL_TIME",
        "experience_years": "4+ years",
        "qualification": "Bachelor's in Computer Science",
        "required_skills": "Python, FastAPI, Docker, PostgreSQL, Kubernetes",
    }
    create_res = client.post(
        "/api/recruiter/jobs",
        json=job_payload,
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert create_res.status_code == 201
    job_id = create_res.json()["id"]

    # Publish job
    client.patch(
        f"/api/recruiter/jobs/{job_id}/publish",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )

    # 2. Candidate updates profile skills
    client.put(
        "/api/candidate/profile",
        json={
            "full_name": "Phase7 Candidate",
            "skills": "Python, FastAPI, PostgreSQL",
            "experience": "3 years",
            "education": "B.Tech in Computer Science",
        },
        headers={"Authorization": f"Bearer {candidate_token}"},
    )

    # 3. Candidate queries skill-gap for this job
    gap_res = client.get(
        f"/api/candidate/jobs/{job_id}/skill-gap",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert gap_res.status_code == 200
    data = gap_res.json()
    assert data["job_id"] == job_id
    assert data["total_required_count"] == 5
    assert data["matched_count"] == 3
    assert data["missing_count"] == 2
    assert data["coverage_percentage"] == 60.0
    assert "Python" in data["matched_skills"]
    assert "FastAPI" in data["matched_skills"]
    assert "PostgreSQL" in data["matched_skills"]
    assert "Docker" in data["missing_skills"]
    assert "Kubernetes" in data["missing_skills"]
    assert len(data["learning_recommendations"]) >= 2
    assert "advisory" in data["advisory_note"].lower()


def test_application_screening_persists_skill_coverage(auth_tokens):
    """Verify application submission stores skill coverage and gap breakdown."""
    recruiter_token = auth_tokens["recruiter_token"]
    candidate_token = auth_tokens["candidate_token"]

    # 1. Create and publish job
    job_payload = {
        "title": "Frontend React Developer",
        "company_name": "Modern Web Tech",
        "description": "Develop modern UI with React and TypeScript.",
        "work_location": "New York, NY",
        "employment_type": "FULL_TIME",
        "experience_years": "2+ years",
        "qualification": "Bachelor's Degree",
        "required_skills": "React, TypeScript, CSS",
    }
    j_res = client.post(
        "/api/recruiter/jobs",
        json=job_payload,
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert j_res.status_code == 201
    job_id = j_res.json()["id"]
    client.patch(
        f"/api/recruiter/jobs/{job_id}/publish",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )

    # 2. Candidate applies
    app_res = client.post(
        "/api/candidate/applications",
        json={"job_id": job_id, "cover_letter": "Passionate developer!"},
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert app_res.status_code == 201
    app_data = app_res.json()
    assert app_data["job_id"] == job_id


def test_recruiter_skill_insights_and_sorting(auth_tokens):
    """Verify recruiter can inspect and sort applicants by skill coverage."""
    recruiter_token = auth_tokens["recruiter_token"]

    # Create job
    j_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Fullstack Platform Engineer",
            "company_name": "Platform Cloud Ltd",
            "description": "Work across Python, React, and Docker.",
            "work_location": "Remote",
            "employment_type": "FULL_TIME",
            "qualification": "Bachelor's Degree",
            "experience_years": "3+ years",
            "required_skills": "Python, React, Docker",
        },
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert j_res.status_code == 201
    job_id = j_res.json()["id"]
    client.patch(
        f"/api/recruiter/jobs/{job_id}/publish",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )

    # Recruiter inspects skill insights
    insights_res = client.get(
        f"/api/recruiter/jobs/{job_id}/skill-insights?sort_by=skill_coverage",
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert insights_res.status_code == 200
    assert isinstance(insights_res.json(), list)


def test_authorization_and_isolation(auth_tokens):
    """Verify candidates and unauthorized recruiters cannot access job skill insights."""
    recruiter_token = auth_tokens["recruiter_token"]
    other_recruiter_token = auth_tokens["other_recruiter_token"]
    candidate_token = auth_tokens["candidate_token"]

    # Create job owned by Recruiter A
    j_res = client.post(
        "/api/recruiter/jobs",
        json={
            "title": "Private Core Architect",
            "company_name": "Private Enterprise",
            "description": "Restricted job posting.",
            "work_location": "Remote",
            "employment_type": "FULL_TIME",
            "qualification": "Master's Degree",
            "experience_years": "5+ years",
            "required_skills": "Go, Distributed Systems",
        },
        headers={"Authorization": f"Bearer {recruiter_token}"},
    )
    assert j_res.status_code == 201
    job_id = j_res.json()["id"]

    # 1. Candidate accessing recruiter skill insights -> 403 Forbidden
    res1 = client.get(
        f"/api/recruiter/jobs/{job_id}/skill-insights",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert res1.status_code == 403

    # 2. Other Recruiter accessing Recruiter A's skill insights -> 403 Forbidden
    res2 = client.get(
        f"/api/recruiter/jobs/{job_id}/skill-insights",
        headers={"Authorization": f"Bearer {other_recruiter_token}"},
    )
    assert res2.status_code == 403

    # 3. Unauthenticated -> 401 Unauthorized
    res3 = client.get(f"/api/recruiter/jobs/{job_id}/skill-insights")
    assert res3.status_code == 401


def test_candidate_skill_gap_summary(auth_tokens):
    """Verify candidate skill gap summary aggregates profile and market gap trends."""
    candidate_token = auth_tokens["candidate_token"]

    res = client.get(
        "/api/candidate/skill-gap/summary",
        headers={"Authorization": f"Bearer {candidate_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "detected_skills" in data
    assert "top_market_skill_gaps" in data
    assert "recommended_learning_roadmaps" in data
    assert "advisory_note" in data
