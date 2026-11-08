"""Pydantic schemas for Job postings and Recruiter Dashboard."""

from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.job import EmploymentType, JobStatus


class JobCreateRequest(BaseModel):
    """Schema for creating a new job posting."""

    title: str = Field(..., min_length=3, max_length=200, description="Job title.")
    company_name: str = Field(..., min_length=2, max_length=150, description="Hiring company name.")
    description: str = Field(..., min_length=10, description="Full job description and responsibilities.")
    required_skills: str = Field(..., min_length=2, description="Comma-separated required skills.")
    qualification: str = Field(..., min_length=2, max_length=200, description="Required education/qualification.")
    experience_years: str = Field(..., min_length=1, max_length=100, description="Years of experience required.")
    employment_type: EmploymentType = Field(default=EmploymentType.FULL_TIME, description="Type of employment.")
    work_location: str = Field(..., min_length=2, max_length=150, description="Work location (Remote, Hybrid, On-site).")
    salary_min: Optional[float] = Field(default=None, ge=0, description="Minimum base salary.")
    salary_max: Optional[float] = Field(default=None, ge=0, description="Maximum base salary.")
    salary_currency: str = Field(default="USD", max_length=10, description="Currency code (e.g. USD, EUR, GBP).")
    deadline: Optional[datetime] = Field(default=None, description="Application closing deadline.")
    status: JobStatus = Field(default=JobStatus.DRAFT, description="Initial job status: DRAFT or ACTIVE.")


class JobUpdateRequest(BaseModel):
    """Schema for updating an existing job posting."""

    title: Optional[str] = Field(default=None, min_length=3, max_length=200)
    company_name: Optional[str] = Field(default=None, min_length=2, max_length=150)
    description: Optional[str] = Field(default=None, min_length=10)
    required_skills: Optional[str] = Field(default=None, min_length=2)
    qualification: Optional[str] = Field(default=None, min_length=2, max_length=200)
    experience_years: Optional[str] = Field(default=None, min_length=1, max_length=100)
    employment_type: Optional[EmploymentType] = None
    work_location: Optional[str] = Field(default=None, min_length=2, max_length=150)
    salary_min: Optional[float] = Field(default=None, ge=0)
    salary_max: Optional[float] = Field(default=None, ge=0)
    salary_currency: Optional[str] = Field(default=None, max_length=10)
    deadline: Optional[datetime] = None
    status: Optional[JobStatus] = None


class JobStatusUpdateRequest(BaseModel):
    """Schema for updating only the job status (e.g. publish, archive)."""

    status: JobStatus


class JobResponse(BaseModel):
    """Complete public job posting representation."""

    id: int
    recruiter_id: int
    title: str
    company_name: str
    description: str
    required_skills: str
    qualification: str
    experience_years: str
    employment_type: EmploymentType
    work_location: str
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    salary_currency: str
    deadline: Optional[datetime] = None
    status: JobStatus
    is_indexed: bool = False
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobRecommendationResponse(BaseModel):
    """Schema for a job recommended to a candidate via dense semantic matching."""

    job: JobResponse
    similarity_score: float
    match_tier: str


class RecruiterDashboardStats(BaseModel):
    """Statistical summary for the recruiter dashboard."""

    total_jobs: int
    active_jobs: int
    draft_jobs: int
    archived_jobs: int
    total_applications: int
    recent_jobs: List[JobResponse]
