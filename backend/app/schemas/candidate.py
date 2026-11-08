"""Pydantic schemas for candidate profile, resume, and dashboard metrics."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.schemas.job import JobResponse
from app.schemas.screening import ParsedResumeResponse


class CandidateProfileUpdateRequest(BaseModel):
    """Schema for creating or updating candidate profile information."""

    full_name: Optional[str] = Field(None, max_length=150)
    phone_number: Optional[str] = Field(None, max_length=50)
    education: Optional[str] = Field(None, max_length=150)
    college_university: Optional[str] = Field(None, max_length=200)
    graduation_year: Optional[int] = Field(None, ge=1950, le=2100)
    skills: Optional[str] = None
    experience: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=150)
    professional_summary: Optional[str] = None


class CandidateProfileResponse(BaseModel):
    """Schema returned for candidate profile data."""

    id: int
    user_id: int
    full_name: Optional[str] = None
    phone_number: Optional[str] = None
    email: Optional[str] = None
    education: Optional[str] = None
    college_university: Optional[str] = None
    graduation_year: Optional[int] = None
    skills: Optional[str] = None
    experience: Optional[str] = None
    location: Optional[str] = None
    professional_summary: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    parsed_resume: Optional[ParsedResumeResponse] = None
    has_resume: bool = False

    model_config = ConfigDict(from_attributes=True)


class ResumeResponse(BaseModel):
    """Schema returned for resume metadata."""

    id: int
    candidate_id: int
    original_filename: str
    file_size: int
    content_type: str
    created_at: datetime
    updated_at: datetime
    parsed_resume: Optional[ParsedResumeResponse] = None

    model_config = ConfigDict(from_attributes=True)


class CandidateDashboardStats(BaseModel):
    """Aggregated metrics for candidate dashboard."""

    profile_completion_percentage: int
    total_applications: int
    pending_applications: int
    shortlisted_applications: int
    rejected_applications: int
    has_resume: bool
    recent_jobs: List[JobResponse] = []
