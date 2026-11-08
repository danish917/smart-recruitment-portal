"""Pydantic schemas for Recruiter and Candidate Analytics."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class StatusDistribution(BaseModel):
    """Distribution counts for applications by status."""

    applied: int = Field(default=0, description="Applications awaiting recruiter review")
    under_review: int = Field(default=0, description="Applications currently under review")
    shortlisted: int = Field(default=0, description="Applications marked as shortlisted")
    rejected: int = Field(default=0, description="Applications marked as rejected")
    total: int = Field(default=0, description="Total applications across all statuses")


class RecentActivityItem(BaseModel):
    """An activity log item representing recruitment or candidate pipeline events."""

    id: int
    activity_type: str = Field(description="APPLICATION_SUBMITTED, STATUS_CHANGED, SCREENING_COMPLETED")
    title: str
    description: str
    timestamp: datetime
    status: Optional[str] = None
    job_id: Optional[int] = None
    job_title: Optional[str] = None
    candidate_name: Optional[str] = None
    metric_value: Optional[float] = None


class JobPerformanceMetric(BaseModel):
    """Summary of applicant performance for a specific job."""

    job_id: int
    job_title: str
    company_name: str
    status: str
    applicant_count: int
    average_skill_coverage: Optional[float] = None
    average_semantic_score: Optional[float] = None
    shortlisted_count: int = 0


class RecruiterAnalyticsResponse(BaseModel):
    """Comprehensive analytics metrics for recruiter pipeline."""

    total_jobs: int
    active_jobs: int
    draft_jobs: int
    archived_jobs: int
    total_applications: int
    applications_under_review: int
    shortlisted_candidates: int
    rejected_applications: int
    average_skill_coverage: Optional[float] = None
    average_semantic_score: Optional[float] = None
    average_screening_score: Optional[float] = None
    status_distribution: StatusDistribution
    recent_activity: List[RecentActivityItem] = []
    top_jobs: List[JobPerformanceMetric] = []

    model_config = ConfigDict(from_attributes=True)


class SkillProgressPoint(BaseModel):
    """Data point tracking a candidate's skill coverage over chronological applications."""

    application_id: int
    job_id: int
    job_title: str
    applied_at: datetime
    skill_coverage: Optional[float] = None
    semantic_score: Optional[float] = None
    screening_score: Optional[float] = None
    status: str


class CandidateAnalyticsResponse(BaseModel):
    """Comprehensive analytics metrics for candidate application pipeline."""

    total_applications: int
    applications_under_review: int
    shortlisted_applications: int
    rejected_applications: int
    status_distribution: StatusDistribution
    average_skill_coverage: Optional[float] = None
    average_semantic_score: Optional[float] = None
    profile_completion_percentage: int = 0
    has_resume: bool = False
    recent_activity: List[RecentActivityItem] = []
    skill_progress_history: List[SkillProgressPoint] = []
    recommended_jobs_count: int = 0

    model_config = ConfigDict(from_attributes=True)
