"""Pydantic schemas for Job Applications."""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.application import ApplicationStatus
from app.schemas.job import JobResponse
from app.schemas.screening import ScreeningResponse


class ApplicationCreateRequest(BaseModel):
    """Schema for candidate submitting a job application."""

    job_id: int = Field(..., gt=0, description="Target active job ID")
    cover_letter: Optional[str] = Field(None, max_length=5000)


class ApplicationStatusUpdateRequest(BaseModel):
    """Schema for recruiter/admin updating an application lifecycle status."""

    status: ApplicationStatus


class ApplicationResponse(BaseModel):
    """Schema for returning job application details."""

    id: int
    candidate_id: int
    job_id: int
    status: ApplicationStatus
    cover_letter: Optional[str] = None
    resume_id: Optional[int] = None
    applied_at: datetime
    updated_at: datetime
    job: Optional[JobResponse] = None
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    screening: Optional[ScreeningResponse] = None
    semantic_score: Optional[float] = None
    skill_coverage: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)
