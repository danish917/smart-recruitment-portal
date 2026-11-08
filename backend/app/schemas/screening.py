"""Pydantic schemas for Parsed Resume, AI Screening, and Skill-Gap Recommendations."""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.screening import ParsingStatus


class ParsedResumeResponse(BaseModel):
    """Schema returned for resume parsing status and extracted data."""

    id: int
    resume_id: int
    candidate_id: int
    status: ParsingStatus
    extracted_data: Optional[Dict[str, Any]] = None
    error_message: Optional[str] = None
    is_indexed: bool = False
    indexed_at: Optional[datetime] = None
    parsed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ScreeningResponse(BaseModel):
    """Schema returned for AI application screening evaluations."""

    id: int
    application_id: int
    screening_score: float
    semantic_score: Optional[float] = None
    skill_coverage: Optional[float] = None
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    skill_gap_analysis: Optional[Dict[str, Any]] = None
    qualification_match: bool
    experience_match: bool
    explanation: str
    score_breakdown: Optional[Dict[str, Any]] = None
    screened_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SemanticApplicantMatch(BaseModel):
    """Schema for candidate ranked via dense semantic matching."""

    application_id: int
    candidate_id: int
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    semantic_score: float
    screening_score: Optional[float] = None
    skill_coverage: Optional[float] = None
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    status: str
    applied_at: datetime


class DocumentationLink(BaseModel):
    """Schema for reputable documentation link."""

    title: str
    url: str


class LearningRecommendationItem(BaseModel):
    """Schema for a single structured skill recommendation."""

    skill_name: str
    required_skill: Optional[str] = None
    category: str
    difficulty: str
    estimated_hours: int
    priority: str
    note: Optional[str] = None
    core_concepts: List[str] = []
    learning_objectives: List[str] = []
    documentation_links: List[DocumentationLink] = []
    practice_project: Optional[str] = None


class PartialSkillMatch(BaseModel):
    """Schema for partial or foundational skill match."""

    required_skill: str
    candidate_related_skill: str
    relationship: str


class SkillGapAnalysisReport(BaseModel):
    """Comprehensive skill-gap analysis report schema."""

    job_id: int
    job_title: str
    coverage_percentage: float
    match_tier: str
    total_required_count: int
    matched_count: int
    missing_count: int
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    partial_skills: List[PartialSkillMatch] = []
    additional_skills: List[str] = []
    skills_to_improve: List[str] = []
    learning_recommendations: List[LearningRecommendationItem] = []
    strengths_summary: str
    growth_summary: str
    advisory_note: str


class RecruiterApplicantSkillInsight(BaseModel):
    """Schema for recruiter viewing applicant skill breakdown."""

    application_id: int
    candidate_id: int
    candidate_name: Optional[str] = None
    candidate_email: Optional[str] = None
    skill_coverage: float
    screening_score: Optional[float] = None
    semantic_score: Optional[float] = None
    matched_skills: List[str] = []
    missing_skills: List[str] = []
    additional_skills: List[str] = []
    partial_skills: List[PartialSkillMatch] = []
    status: str
    applied_at: datetime
