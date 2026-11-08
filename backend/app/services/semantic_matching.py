"""Semantic Job Matching and Recommendation Orchestrator."""

import math
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.application import Application
from app.models.candidate import Resume
from app.models.job import Job, JobStatus
from app.models.screening import ApplicationScreening, ParsedResume, ParsingStatus
from app.services.embedding import EmbeddingService, get_embedding_service
from app.services.vector_db import VectorDBService, get_vector_db_service


def cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
    """Compute cosine similarity between two unit or raw vectors."""
    if not vec1 or not vec2 or len(vec1) != len(vec2):
        return 0.0
    dot = sum(a * b for a, b in zip(vec1, vec2))
    norm1 = math.sqrt(sum(a * a for a in vec1))
    norm2 = math.sqrt(sum(b * b for b in vec2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    raw = dot / (norm1 * norm2)
    # Scale from [-1, 1] to [0, 100]
    scaled = ((raw + 1.0) / 2.0) * 100.0
    return max(0.0, min(100.0, round(scaled, 1)))


class SemanticMatchingService:
    """Orchestrates embedding generation, vector database synchronization, and semantic search."""

    def __init__(
        self,
        vector_db: Optional[VectorDBService] = None,
        embedding_svc: Optional[EmbeddingService] = None,
    ) -> None:
        self.vector_db = vector_db or get_vector_db_service()
        self.embedding_svc = embedding_svc or get_embedding_service()

    # -------------------------------------------------------------------------
    # Resume Synchronization
    # -------------------------------------------------------------------------

    def index_candidate_resume(
        self,
        db: Session,
        parsed_resume_id: int,
    ) -> Optional[str]:
        """Generate dense vector and index candidate parsed resume in Qdrant."""
        parsed_resume = (
            db.query(ParsedResume)
            .filter(ParsedResume.id == parsed_resume_id)
            .first()
        )
        if not parsed_resume or parsed_resume.status != ParsingStatus.PARSED:
            return None

        # Build semantically dense representation
        text_payload = self.embedding_svc.prepare_resume_text(
            parsed_resume.extracted_data or {},
            parsed_resume.raw_text or "",
        )
        vector = self.embedding_svc.embed_text(text_payload)

        metadata = {
            "candidate_id": parsed_resume.candidate_id,
            "resume_id": parsed_resume.resume_id,
            "skills": (parsed_resume.extracted_data or {}).get("technical_skills", []),
            "experience_years": (parsed_resume.extracted_data or {}).get("experience_years"),
        }

        point_id = self.vector_db.upsert_resume_vector(
            candidate_id=parsed_resume.candidate_id,
            resume_id=parsed_resume.resume_id,
            vector=vector,
            metadata=metadata,
        )

        parsed_resume.vector_id = point_id
        parsed_resume.is_indexed = True
        parsed_resume.indexed_at = func.now()
        db.commit()
        db.refresh(parsed_resume)

        return point_id

    def deindex_candidate_resume(self, db: Session, resume_id: int) -> None:
        """Remove candidate resume vector from Qdrant and update relational status."""
        self.vector_db.delete_resume_vector(resume_id)
        parsed_resume = (
            db.query(ParsedResume)
            .filter(ParsedResume.resume_id == resume_id)
            .first()
        )
        if parsed_resume:
            parsed_resume.is_indexed = False
            parsed_resume.vector_id = None
            parsed_resume.indexed_at = None
            db.commit()

    # -------------------------------------------------------------------------
    # Job Synchronization
    # -------------------------------------------------------------------------

    def index_job_posting(self, db: Session, job_id: int) -> Optional[str]:
        """Generate dense vector and index active job requisition in Qdrant."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return None

        if job.status != JobStatus.ACTIVE:
            # Only ACTIVE jobs must be indexed and searchable
            self.deindex_job_posting(db, job_id)
            return None

        text_payload = self.embedding_svc.prepare_job_text(
            title=job.title,
            description=job.description,
            required_skills=job.required_skills,
            qualification=job.qualification,
            experience_years=job.experience_years,
            company_name=job.company_name,
            work_location=job.work_location,
        )
        vector = self.embedding_svc.embed_text(text_payload)

        metadata = {
            "job_id": job.id,
            "recruiter_id": job.recruiter_id,
            "title": job.title,
            "company_name": job.company_name,
            "work_location": job.work_location,
            "employment_type": job.employment_type.value if hasattr(job.employment_type, "value") else str(job.employment_type),
            "status": "ACTIVE",
        }

        point_id = self.vector_db.upsert_job_vector(
            job_id=job.id,
            recruiter_id=job.recruiter_id,
            vector=vector,
            metadata=metadata,
        )

        job.vector_id = point_id
        job.is_indexed = True
        job.indexed_at = func.now()
        db.commit()
        db.refresh(job)

        return point_id

    def deindex_job_posting(self, db: Session, job_id: int) -> None:
        """Remove job requisition vector from Qdrant and update relational flag."""
        self.vector_db.delete_job_vector(job_id)
        job = db.query(Job).filter(Job.id == job_id).first()
        if job and job.is_indexed:
            job.is_indexed = False
            job.vector_id = None
            job.indexed_at = None
            db.commit()

    # -------------------------------------------------------------------------
    # Candidate Matching & Recommendations
    # -------------------------------------------------------------------------

    def get_candidate_job_recommendations(
        self,
        db: Session,
        candidate_id: int,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """Find active jobs that semantically match candidate's resume."""
        resume = (
            db.query(Resume)
            .filter(Resume.candidate_id == candidate_id)
            .order_by(Resume.created_at.desc())
            .first()
        )
        if not resume:
            return []

        parsed = (
            db.query(ParsedResume)
            .filter(ParsedResume.resume_id == resume.id)
            .first()
        )
        if not parsed or parsed.status != ParsingStatus.PARSED:
            return []

        # Ensure resume vector is indexed
        if not parsed.is_indexed:
            self.index_candidate_resume(db, parsed.id)

        # Prepare vector
        resume_text = self.embedding_svc.prepare_resume_text(
            parsed.extracted_data or {},
            parsed.raw_text or "",
        )
        resume_vector = self.embedding_svc.embed_text(resume_text)

        hits = self.vector_db.search_jobs_for_resume(
            resume_vector=resume_vector,
            limit=limit,
            active_only=True,
        )

        results = []
        for hit in hits:
            job_id = hit.get("job_id")
            if not job_id:
                continue
            job = db.query(Job).filter(Job.id == job_id, Job.status == JobStatus.ACTIVE).first()
            if not job:
                continue

            sim_score = hit.get("similarity_score", 0.0)
            if sim_score >= 80:
                tier = "Strong Match"
            elif sim_score >= 65:
                tier = "Good Match"
            elif sim_score >= 50:
                tier = "Moderate Match"
            else:
                tier = "Potential Match"

            results.append({
                "job": job,
                "similarity_score": sim_score,
                "match_tier": tier,
            })

        return results

    # -------------------------------------------------------------------------
    # Recruiter Semantic Applicant Ranking
    # -------------------------------------------------------------------------

    def rank_applicants_semantically(
        self,
        db: Session,
        job_id: int,
    ) -> List[Dict[str, Any]]:
        """Compute and persist semantic vector similarity scores for all job applicants."""
        job = db.query(Job).filter(Job.id == job_id).first()
        if not job:
            return []

        # Prepare job vector
        job_text = self.embedding_svc.prepare_job_text(
            title=job.title,
            description=job.description,
            required_skills=job.required_skills,
            qualification=job.qualification,
            experience_years=job.experience_years,
            company_name=job.company_name,
            work_location=job.work_location,
        )
        job_vector = self.embedding_svc.embed_text(job_text)

        applications = (
            db.query(Application)
            .filter(Application.job_id == job_id)
            .all()
        )

        ranked = []
        for app in applications:
            semantic_score: Optional[float] = None

            if app.resume_id:
                parsed = (
                    db.query(ParsedResume)
                    .filter(ParsedResume.resume_id == app.resume_id)
                    .first()
                )
                if parsed and parsed.status == ParsingStatus.PARSED:
                    # Auto index if needed
                    if not parsed.is_indexed:
                        self.index_candidate_resume(db, parsed.id)

                    resume_text = self.embedding_svc.prepare_resume_text(
                        parsed.extracted_data or {},
                        parsed.raw_text or "",
                    )
                    resume_vector = self.embedding_svc.embed_text(resume_text)
                    semantic_score = cosine_similarity(job_vector, resume_vector)

                    # Persist semantic score on ApplicationScreening
                    if app.screening:
                        app.screening.semantic_score = semantic_score
                    else:
                        screening = ApplicationScreening(
                            application_id=app.id,
                            screening_score=0.0,
                            semantic_score=semantic_score,
                            matched_skills=[],
                            missing_skills=[],
                            qualification_match=False,
                            experience_match=False,
                            explanation="Semantic vector score computed.",
                        )
                        db.add(screening)
                    db.commit()

            ranked.append({
                "application": app,
                "semantic_score": semantic_score,
                "screening": app.screening,
            })

        # Sort descending by semantic score (nulls last)
        ranked.sort(
            key=lambda x: (
                x["semantic_score"] is not None,
                x["semantic_score"] or 0.0,
            ),
            reverse=True,
        )
        return ranked


def get_semantic_matching_service() -> SemanticMatchingService:
    """Dependency provider for SemanticMatchingService."""
    return SemanticMatchingService()
