"""Dense Embedding Service for semantic candidate and job matching."""

import os
from typing import Any, Dict, List, Optional
import certifi

# Ensure SSL certificate verification works on Windows
os.environ.setdefault("SSL_CERT_FILE", certifi.where())
os.environ.setdefault("REQUESTS_CA_BUNDLE", certifi.where())

from app.core.config import settings


class EmbeddingService:
    """Singleton service for generating dense vector embeddings using FastEmbed."""

    _instance: Optional["EmbeddingService"] = None
    _model: Any = None

    def __new__(cls) -> "EmbeddingService":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init_model()
        return cls._instance

    def _init_model(self) -> None:
        """Initialize the pretrained embedding model."""
        try:
            from fastembed import TextEmbedding

            self._model = TextEmbedding(model_name=settings.EMBEDDING_MODEL_NAME)
        except Exception as e:
            # Fallback for environments where model download is disabled or mocked
            self._model = None

    def is_available(self) -> bool:
        """Check if the embedding model is loaded."""
        return self._model is not None

    def prepare_resume_text(self, extracted_data: Dict[str, Any], raw_text: str = "") -> str:
        """Build a semantically dense representation of candidate resume."""
        parts = []

        # Name / headline
        if extracted_data.get("name"):
            parts.append(f"Candidate: {extracted_data['name']}.")

        # Technical & soft skills have the highest semantic priority
        tech_skills = extracted_data.get("technical_skills", [])
        if tech_skills:
            parts.append(f"Technical Skills & Proficiencies: {', '.join(tech_skills)}.")

        soft_skills = extracted_data.get("soft_skills", [])
        if soft_skills:
            parts.append(f"Core Competencies: {', '.join(soft_skills)}.")

        # Education
        education = extracted_data.get("education")
        university = extracted_data.get("college_university")
        grad_year = extracted_data.get("graduation_year")
        if education or university:
            edu_str = f"Education: {education or 'Degree'}"
            if university:
                edu_str += f" from {university}"
            if grad_year:
                edu_str += f" ({grad_year})"
            parts.append(edu_str + ".")

        # Experience
        exp_years = extracted_data.get("experience_years")
        if exp_years:
            parts.append(f"Experience: {exp_years} years.")

        work_exp = extracted_data.get("work_experience", [])
        if work_exp:
            parts.append(f"Roles & Work History: {'; '.join(work_exp)}.")

        # Projects & Certifications
        projects = extracted_data.get("projects", [])
        if projects:
            parts.append(f"Key Projects: {'; '.join(projects)}.")

        certs = extracted_data.get("certifications", [])
        if certs:
            parts.append(f"Certifications: {'; '.join(certs)}.")

        if not parts and raw_text:
            # Fallback to truncated raw text
            return raw_text[:2000]

        return " ".join(parts)

    def prepare_job_text(
        self,
        title: str,
        description: str,
        required_skills: str,
        qualification: str,
        experience_years: str,
        company_name: str = "",
        work_location: str = "",
    ) -> str:
        """Build a semantically dense representation of job requisition."""
        parts = [
            f"Job Title: {title}.",
            f"Required Technical Skills: {required_skills}.",
            f"Required Experience: {experience_years} years.",
            f"Required Qualification: {qualification}.",
        ]
        if company_name:
            parts.append(f"Company: {company_name}.")
        if work_location:
            parts.append(f"Location: {work_location}.")

        if description:
            # Append description snippet
            parts.append(f"Description: {description.strip()[:1500]}")

        return " ".join(parts)

    def embed_text(self, text: str) -> List[float]:
        """Generate a single 384-dimensional dense vector for input text."""
        if not text or not text.strip():
            # Return zero vector of configured dimension
            return [0.0] * settings.EMBEDDING_DIMENSION

        if self._model is not None:
            generator = self._model.embed([text])
            vector = list(generator)[0]
            return [float(x) for x in vector]

        # Deterministic lightweight pseudo-embedding fallback for mocked test environments
        import hashlib
        import math

        h = hashlib.sha256(text.encode("utf-8")).digest()
        # Expand 32 bytes to 384 floats
        raw = []
        for i in range(settings.EMBEDDING_DIMENSION):
            byte_val = h[i % len(h)]
            raw.append(math.sin(byte_val + i))
        # Normalize vector
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]

    def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate dense vectors for a list of texts in batch."""
        if not texts:
            return []

        if self._model is not None:
            generator = self._model.embed(texts)
            return [[float(x) for x in vec] for vec in generator]

        return [self.embed_text(t) for t in texts]


def get_embedding_service() -> EmbeddingService:
    """Dependency provider for EmbeddingService."""
    return EmbeddingService()
