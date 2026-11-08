"""Qdrant Vector Database Service abstraction."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import uuid

from qdrant_client import QdrantClient, models
from qdrant_client.models import Distance, PointStruct, VectorParams

from app.core.config import settings

# Base storage directory for local Qdrant
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class VectorDBService:
    """Service abstraction managing Qdrant vector database operations."""

    _instance: Optional["VectorDBService"] = None

    def __init__(self, in_memory: bool = False) -> None:
        if in_memory:
            self.client = QdrantClient(":memory:")
        elif settings.QDRANT_URL and settings.QDRANT_URL.strip():
            # Cloud or Remote Qdrant instance
            api_key = settings.QDRANT_API_KEY.strip() if settings.QDRANT_API_KEY else None
            self.client = QdrantClient(url=settings.QDRANT_URL.strip(), api_key=api_key)
        else:
            # Local persistent disk storage
            qdrant_dir = BASE_DIR / settings.QDRANT_PATH
            qdrant_dir.mkdir(parents=True, exist_ok=True)
            try:
                self.client = QdrantClient(path=str(qdrant_dir))
            except Exception:
                # In case file lock is held or permission issue, fallback to memory
                self.client = QdrantClient(":memory:")

        self._ensure_collections()

    def _ensure_collections(self) -> None:
        """Create collections with cosine metric if they don't exist yet."""
        collections = [
            settings.RESUME_COLLECTION_NAME,
            settings.JOB_COLLECTION_NAME,
        ]
        for name in collections:
            try:
                if not self.client.collection_exists(name):
                    self.client.create_collection(
                        collection_name=name,
                        vectors_config=VectorParams(
                            size=settings.EMBEDDING_DIMENSION,
                            distance=Distance.COSINE,
                        ),
                    )
            except Exception:
                pass

    # -------------------------------------------------------------------------
    # Resume Vector Operations
    # -------------------------------------------------------------------------

    def get_resume_point_id(self, resume_id: int) -> str:
        """Generate a deterministic UUID for a resume point."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"resume-{resume_id}"))

    def upsert_resume_vector(
        self,
        candidate_id: int,
        resume_id: int,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Index or update candidate resume vector in Qdrant."""
        point_id = self.get_resume_point_id(resume_id)
        payload = {
            "candidate_id": candidate_id,
            "resume_id": resume_id,
            **(metadata or {}),
        }

        self.client.upsert(
            collection_name=settings.RESUME_COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
        return point_id

    def delete_resume_vector(self, resume_id: int) -> None:
        """Remove candidate resume vector from Qdrant."""
        point_id = self.get_resume_point_id(resume_id)
        try:
            self.client.delete(
                collection_name=settings.RESUME_COLLECTION_NAME,
                points_selector=[point_id],
            )
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Job Vector Operations
    # -------------------------------------------------------------------------

    def get_job_point_id(self, job_id: int) -> str:
        """Generate a deterministic UUID for a job point."""
        return str(uuid.uuid5(uuid.NAMESPACE_DNS, f"job-{job_id}"))

    def upsert_job_vector(
        self,
        job_id: int,
        recruiter_id: int,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Index or update job posting vector in Qdrant."""
        point_id = self.get_job_point_id(job_id)
        payload = {
            "job_id": job_id,
            "recruiter_id": recruiter_id,
            "status": "ACTIVE",
            **(metadata or {}),
        }

        self.client.upsert(
            collection_name=settings.JOB_COLLECTION_NAME,
            points=[
                PointStruct(
                    id=point_id,
                    vector=vector,
                    payload=payload,
                )
            ],
        )
        return point_id

    def delete_job_vector(self, job_id: int) -> None:
        """Remove job vector from Qdrant when archived or deleted."""
        point_id = self.get_job_point_id(job_id)
        try:
            self.client.delete(
                collection_name=settings.JOB_COLLECTION_NAME,
                points_selector=[point_id],
            )
        except Exception:
            pass

    # -------------------------------------------------------------------------
    # Semantic Search Operations
    # -------------------------------------------------------------------------

    def search_jobs_for_resume(
        self,
        resume_vector: List[float],
        limit: int = 10,
        active_only: bool = True,
    ) -> List[Dict[str, Any]]:
        """Find most relevant job postings for a candidate's resume vector."""
        query_filter = None
        if active_only:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="status",
                        match=models.MatchValue(value="ACTIVE"),
                    )
                ]
            )

        try:
            response = self.client.query_points(
                collection_name=settings.JOB_COLLECTION_NAME,
                query=resume_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
            hits = []
            for point in response.points:
                # Cosine similarity typically ranges from -1 to 1; normalize/clip to 0.0 - 100.0%
                raw_score = point.score if point.score is not None else 0.0
                similarity_percentage = max(0.0, min(100.0, ((raw_score + 1.0) / 2.0) * 100.0 if raw_score <= 1.0 else raw_score))
                hits.append({
                    "job_id": point.payload.get("job_id"),
                    "recruiter_id": point.payload.get("recruiter_id"),
                    "raw_score": raw_score,
                    "similarity_score": round(similarity_percentage, 1),
                    "payload": point.payload,
                })
            return hits
        except Exception:
            return []

    def search_candidates_for_job(
        self,
        job_vector: List[float],
        limit: int = 20,
        candidate_ids: Optional[List[int]] = None,
    ) -> List[Dict[str, Any]]:
        """Find most relevant candidate resumes for a job requisition vector."""
        query_filter = None
        if candidate_ids:
            query_filter = models.Filter(
                must=[
                    models.FieldCondition(
                        key="candidate_id",
                        match=models.MatchAny(any=candidate_ids),
                    )
                ]
            )

        try:
            response = self.client.query_points(
                collection_name=settings.RESUME_COLLECTION_NAME,
                query=job_vector,
                query_filter=query_filter,
                limit=limit,
                with_payload=True,
            )
            hits = []
            for point in response.points:
                raw_score = point.score if point.score is not None else 0.0
                similarity_percentage = max(0.0, min(100.0, ((raw_score + 1.0) / 2.0) * 100.0 if raw_score <= 1.0 else raw_score))
                hits.append({
                    "candidate_id": point.payload.get("candidate_id"),
                    "resume_id": point.payload.get("resume_id"),
                    "raw_score": raw_score,
                    "similarity_score": round(similarity_percentage, 1),
                    "payload": point.payload,
                })
            return hits
        except Exception:
            return []


# Global singleton instance
_vector_db_service: Optional[VectorDBService] = None


def get_vector_db_service() -> VectorDBService:
    """Dependency provider for VectorDBService."""
    global _vector_db_service
    if _vector_db_service is None:
        _vector_db_service = VectorDBService()
    return _vector_db_service
