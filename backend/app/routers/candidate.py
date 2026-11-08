"""FastAPI router for Candidate Profile, Resume Management, NLP Parsing, Dashboard, and Applications."""

from typing import List, Optional
from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy import func
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.deps import get_current_user, require_roles
from app.core.rate_limiter import rate_limit
from app.database import get_db
from app.models.application import Application, ApplicationStatus
from app.models.candidate import CandidateProfile, Resume
from app.models.job import Job, JobStatus
from app.models.screening import ApplicationScreening, ParsedResume, ParsingStatus
from app.models.user import User, UserRole
from app.schemas.application import (
    ApplicationCreateRequest,
    ApplicationResponse,
)
from app.schemas.candidate import (
    CandidateDashboardStats,
    CandidateProfileResponse,
    CandidateProfileUpdateRequest,
    ResumeResponse,
)
from app.schemas.analytics import (
    CandidateAnalyticsResponse,
    RecentActivityItem,
    SkillProgressPoint,
    StatusDistribution,
)
from app.schemas.job import JobRecommendationResponse, JobResponse
from app.schemas.screening import (
    DocumentationLink,
    LearningRecommendationItem,
    ParsedResumeResponse,
    PartialSkillMatch,
    ScreeningResponse,
    SkillGapAnalysisReport,
)
from app.services.nlp_parser import extract_text_from_pdf, parse_resume_text
from app.services.screening import screen_candidate_resume
from app.services.semantic_matching import get_semantic_matching_service
from app.services.skill_gap import (
    LEARNING_CATALOG,
    analyze_skill_gap,
    get_default_learning_plan_for_unknown_skill,
    normalize_skill_name,
    parse_skill_list,
)
from app.services.storage import StorageService, get_storage_service

router = APIRouter(prefix="/api/candidate", tags=["Candidate Module"])

# Only CANDIDATE (and ADMIN) users can access candidate endpoints
candidate_only = require_roles(UserRole.CANDIDATE, UserRole.ADMIN)


def calculate_profile_completion(profile: CandidateProfile, has_resume: bool) -> int:
    """Calculate candidate profile completeness percentage (0 to 100)."""
    score = 0
    if profile.full_name and profile.full_name.strip():
        score += 10
    if profile.phone_number and profile.phone_number.strip():
        score += 10
    if profile.email and profile.email.strip():
        score += 10
    if profile.education and profile.education.strip():
        score += 10
    if profile.college_university and profile.college_university.strip():
        score += 10
    if profile.graduation_year:
        score += 10
    if profile.skills and profile.skills.strip():
        score += 10
    if profile.experience and profile.experience.strip():
        score += 10
    if profile.location and profile.location.strip():
        score += 10
    if profile.professional_summary and profile.professional_summary.strip():
        score += 5
    if has_resume:
        score += 5
    return min(100, score)


# -------------------------------------------------------------------------
# Candidate Profile Endpoints
# -------------------------------------------------------------------------

@router.get("/profile", response_model=CandidateProfileResponse)
def get_candidate_profile(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Retrieve the candidate profile for the authenticated user.

    If no profile exists yet, initialises one with default user values.
    """
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        profile = CandidateProfile(
            user_id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()

    return CandidateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        phone_number=profile.phone_number,
        email=profile.email or current_user.email,
        education=profile.education,
        college_university=profile.college_university,
        graduation_year=profile.graduation_year,
        skills=profile.skills,
        experience=profile.experience,
        location=profile.location,
        professional_summary=profile.professional_summary,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        has_resume=resume is not None,
    )


@router.put("/profile", response_model=CandidateProfileResponse)
def update_candidate_profile(
    payload: CandidateProfileUpdateRequest,
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Update profile fields for the authenticated candidate."""
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )

    if not profile:
        profile = CandidateProfile(
            user_id=current_user.id,
            email=current_user.email,
        )
        db.add(profile)

    update_data = payload.model_dump(exclude_unset=True)
    for field, val in update_data.items():
        setattr(profile, field, val)

    # Sync full_name back to User record if updated
    if payload.full_name and payload.full_name.strip():
        current_user.full_name = payload.full_name.strip()

    db.commit()
    db.refresh(profile)

    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()

    return CandidateProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        full_name=profile.full_name,
        phone_number=profile.phone_number,
        email=profile.email or current_user.email,
        education=profile.education,
        college_university=profile.college_university,
        graduation_year=profile.graduation_year,
        skills=profile.skills,
        experience=profile.experience,
        location=profile.location,
        professional_summary=profile.professional_summary,
        created_at=profile.created_at,
        updated_at=profile.updated_at,
        has_resume=resume is not None,
    )


# -------------------------------------------------------------------------
# Resume Management & NLP Parsing Endpoints
# -------------------------------------------------------------------------

@router.post(
    "/resume/upload",
    response_model=ResumeResponse,
    dependencies=[Depends(rate_limit(settings.MAX_UPLOADS_PER_MINUTE, 60))],
)
async def upload_resume(
    file: UploadFile = File(...),
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """Upload or replace candidate resume and trigger automated NLP extraction.

    Validates PDF format and 5MB size limit.
    Stores file securely outside web root and extracts skills, education, and credentials.
    """
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty.",
        )

    # Check for existing resume
    existing_resume = (
        db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    )

    # Save to storage abstraction
    stored_filename, relative_path, file_size = storage.save_file(
        file_content=content,
        original_filename=file.filename or "resume.pdf",
        content_type=file.content_type or "application/pdf",
    )

    if existing_resume:
        # Delete old file from storage
        storage.delete_file(existing_resume.filename)
        # Update record
        existing_resume.filename = stored_filename
        existing_resume.original_filename = file.filename or "resume.pdf"
        existing_resume.file_size = file_size
        existing_resume.content_type = "application/pdf"
        existing_resume.file_path = relative_path
        db.commit()
        db.refresh(existing_resume)
        resume_record = existing_resume
    else:
        new_resume = Resume(
            candidate_id=current_user.id,
            filename=stored_filename,
            original_filename=file.filename or "resume.pdf",
            file_size=file_size,
            content_type="application/pdf",
            file_path=relative_path,
        )
        db.add(new_resume)
        db.commit()
        db.refresh(new_resume)
        resume_record = new_resume

    # Perform automated text extraction & NLP structuring
    raw_text, parse_status, error_msg = extract_text_from_pdf(content)
    parsed_json = (
        parse_resume_text(raw_text)
        if parse_status == ParsingStatus.PARSED
        else None
    )

    parsed_record = (
        db.query(ParsedResume)
        .filter(ParsedResume.resume_id == resume_record.id)
        .first()
    )
    if parsed_record:
        parsed_record.status = parse_status
        parsed_record.raw_text = raw_text
        parsed_record.extracted_data = parsed_json
        parsed_record.error_message = error_msg
        parsed_record.parsed_at = func.now()
    else:
        parsed_record = ParsedResume(
            resume_id=resume_record.id,
            candidate_id=current_user.id,
            status=parse_status,
            raw_text=raw_text,
            extracted_data=parsed_json,
            error_message=error_msg,
            parsed_at=func.now(),
        )
        db.add(parsed_record)
    db.commit()
    db.refresh(parsed_record)

    # Automatically index dense resume vector in Qdrant if parsing succeeded
    if parse_status == ParsingStatus.PARSED:
        try:
            semantic_svc = get_semantic_matching_service()
            semantic_svc.index_candidate_resume(db, parsed_record.id)
            db.refresh(parsed_record)
        except Exception:
            pass

    # If candidate profile has empty skills/education, backfill from parsed resume
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if profile and parsed_json:
        if not profile.skills and parsed_json.get("technical_skills"):
            profile.skills = ", ".join(parsed_json["technical_skills"][:10])
        if not profile.education and parsed_json.get("education"):
            profile.education = parsed_json["education"]
        if not profile.college_university and parsed_json.get("college_university"):
            profile.college_university = parsed_json["college_university"]
        if not profile.graduation_year and parsed_json.get("graduation_year"):
            profile.graduation_year = parsed_json["graduation_year"]
        db.commit()

    return ResumeResponse(
        id=resume_record.id,
        candidate_id=resume_record.candidate_id,
        original_filename=resume_record.original_filename,
        file_size=resume_record.file_size,
        content_type=resume_record.content_type,
        created_at=resume_record.created_at,
        updated_at=resume_record.updated_at,
        parsed_resume=ParsedResumeResponse.model_validate(parsed_record),
    )


@router.get("/resume", response_model=ResumeResponse)
def get_resume_metadata(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Get metadata for the authenticated candidate's active resume and parsing status."""
    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found for this candidate.",
        )

    parsed = db.query(ParsedResume).filter(ParsedResume.resume_id == resume.id).first()

    return ResumeResponse(
        id=resume.id,
        candidate_id=resume.candidate_id,
        original_filename=resume.original_filename,
        file_size=resume.file_size,
        content_type=resume.content_type,
        created_at=resume.created_at,
        updated_at=resume.updated_at,
        parsed_resume=ParsedResumeResponse.model_validate(parsed) if parsed else None,
    )


@router.get("/resume/parsed", response_model=ParsedResumeResponse)
def get_parsed_resume_data(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Retrieve structured NLP extraction details for candidate's resume."""
    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No uploaded resume found.",
        )

    parsed = db.query(ParsedResume).filter(ParsedResume.resume_id == resume.id).first()
    if not parsed:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume has not been parsed yet.",
        )
    return ParsedResumeResponse.model_validate(parsed)


@router.post("/resume/reparse", response_model=ParsedResumeResponse)
def reparse_candidate_resume(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """Re-trigger PDF text extraction and NLP parsing on the existing resume."""
    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found to parse.",
        )

    file_path = storage.get_file_path(resume.filename)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file is missing from storage.",
        )

    with open(file_path, "rb") as f:
        content = f.read()

    raw_text, parse_status, error_msg = extract_text_from_pdf(content)
    parsed_json = (
        parse_resume_text(raw_text)
        if parse_status == ParsingStatus.PARSED
        else None
    )

    parsed_record = (
        db.query(ParsedResume).filter(ParsedResume.resume_id == resume.id).first()
    )
    if parsed_record:
        parsed_record.status = parse_status
        parsed_record.raw_text = raw_text
        parsed_record.extracted_data = parsed_json
        parsed_record.error_message = error_msg
        parsed_record.parsed_at = func.now()
    else:
        parsed_record = ParsedResume(
            resume_id=resume.id,
            candidate_id=current_user.id,
            status=parse_status,
            raw_text=raw_text,
            extracted_data=parsed_json,
            error_message=error_msg,
            parsed_at=func.now(),
        )
        db.add(parsed_record)
    db.commit()
    db.refresh(parsed_record)

    # Automatically index dense resume vector in Qdrant if parsing succeeded
    if parse_status == ParsingStatus.PARSED:
        try:
            semantic_svc = get_semantic_matching_service()
            semantic_svc.index_candidate_resume(db, parsed_record.id)
            db.refresh(parsed_record)
        except Exception:
            pass

    return ParsedResumeResponse.model_validate(parsed_record)


@router.get("/resume/download")
def download_resume(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """Stream the candidate's uploaded resume securely.

    Requires authentication; files are never exposed publicly.
    """
    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found to download.",
        )

    file_path = storage.get_file_path(resume.filename)
    if not file_path or not file_path.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume file is missing from storage.",
        )

    return FileResponse(
        path=str(file_path),
        media_type="application/pdf",
        filename=resume.original_filename,
    )


@router.delete("/resume")
def delete_resume(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """Delete candidate's uploaded resume from disk and database."""
    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No resume found to delete.",
        )

    storage.delete_file(resume.filename)
    try:
        semantic_svc = get_semantic_matching_service()
        semantic_svc.deindex_candidate_resume(db, resume.id)
    except Exception:
        pass
    db.delete(resume)
    db.commit()
    return {"message": "Resume successfully deleted."}


@router.post("/resume/index-vector", response_model=ParsedResumeResponse)
def index_candidate_resume_vector(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Explicitly generate vector embedding and index resume in Qdrant."""
    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No uploaded resume found to index.",
        )

    parsed = db.query(ParsedResume).filter(ParsedResume.resume_id == resume.id).first()
    if not parsed or parsed.status != ParsingStatus.PARSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Resume must be successfully parsed before vector indexing.",
        )

    semantic_svc = get_semantic_matching_service()
    point_id = semantic_svc.index_candidate_resume(db, parsed.id)
    if not point_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate vector embedding or index in Qdrant.",
        )

    db.refresh(parsed)
    return ParsedResumeResponse.model_validate(parsed)


# -------------------------------------------------------------------------
# Candidate Dashboard Stats
# -------------------------------------------------------------------------

@router.get("/dashboard/stats", response_model=CandidateDashboardStats)
def get_candidate_dashboard_stats(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Retrieve candidate metrics: profile completeness, application counts, and recent active jobs."""
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    if not profile:
        profile = CandidateProfile(
            user_id=current_user.id,
            full_name=current_user.full_name,
            email=current_user.email,
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)

    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    has_resume = resume is not None

    completion = calculate_profile_completion(profile, has_resume)

    total_apps = (
        db.query(Application)
        .filter(Application.candidate_id == current_user.id)
        .count()
    )
    pending_apps = (
        db.query(Application)
        .filter(
            Application.candidate_id == current_user.id,
            Application.status.in_([ApplicationStatus.APPLIED, ApplicationStatus.UNDER_REVIEW]),
        )
        .count()
    )
    shortlisted_apps = (
        db.query(Application)
        .filter(
            Application.candidate_id == current_user.id,
            Application.status == ApplicationStatus.SHORTLISTED,
        )
        .count()
    )
    rejected_apps = (
        db.query(Application)
        .filter(
            Application.candidate_id == current_user.id,
            Application.status == ApplicationStatus.REJECTED,
        )
        .count()
    )

    # Top 5 recently published ACTIVE jobs
    recent_jobs = (
        db.query(Job)
        .filter(Job.status == JobStatus.ACTIVE)
        .order_by(Job.created_at.desc())
        .limit(5)
        .all()
    )

    return CandidateDashboardStats(
        profile_completion_percentage=completion,
        total_applications=total_apps,
        pending_applications=pending_apps,
        shortlisted_applications=shortlisted_apps,
        rejected_applications=rejected_apps,
        has_resume=has_resume,
        recent_jobs=[JobResponse.model_validate(j) for j in recent_jobs],
    )


@router.get(
    "/analytics",
    response_model=CandidateAnalyticsResponse,
    summary="Get candidate application pipeline analytics and skill progression",
)
def get_candidate_analytics(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Retrieve full PostgreSQL analytics and historical skill progress for the candidate."""
    profile = (
        db.query(CandidateProfile)
        .filter(CandidateProfile.user_id == current_user.id)
        .first()
    )
    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    has_resume = resume is not None
    completion = calculate_profile_completion(profile, has_resume) if profile else 0

    # Applications submitted by candidate in chronological order
    applications = (
        db.query(Application)
        .filter(Application.candidate_id == current_user.id)
        .order_by(Application.applied_at.asc())
        .all()
    )

    total_applications = len(applications)
    applied_count = sum(1 for a in applications if a.status == ApplicationStatus.APPLIED)
    under_review_count = sum(1 for a in applications if a.status == ApplicationStatus.UNDER_REVIEW)
    shortlisted_count = sum(1 for a in applications if a.status == ApplicationStatus.SHORTLISTED)
    rejected_count = sum(1 for a in applications if a.status == ApplicationStatus.REJECTED)

    status_dist = StatusDistribution(
        applied=applied_count,
        under_review=under_review_count,
        shortlisted=shortlisted_count,
        rejected=rejected_count,
        total=total_applications,
    )

    app_ids = [a.id for a in applications]
    screenings = (
        db.query(ApplicationScreening)
        .filter(ApplicationScreening.application_id.in_(app_ids))
        .all()
    ) if app_ids else []

    screening_map = {s.application_id: s for s in screenings}

    coverages = [s.skill_coverage for s in screenings if s.skill_coverage is not None]
    avg_coverage = round(sum(coverages) / len(coverages), 1) if coverages else None

    semantic_scores = [s.semantic_score for s in screenings if s.semantic_score is not None]
    avg_semantic = round(sum(semantic_scores) / len(semantic_scores), 1) if semantic_scores else None

    # Chronological skill progress history across real job applications
    skill_progress_history: List[SkillProgressPoint] = []
    for app in applications:
        scr = screening_map.get(app.id)
        skill_progress_history.append(
            SkillProgressPoint(
                application_id=app.id,
                job_id=app.job_id,
                job_title=app.job.title if app.job else "Job Requisition",
                applied_at=app.applied_at,
                skill_coverage=scr.skill_coverage if scr else None,
                semantic_score=scr.semantic_score if scr else None,
                screening_score=scr.screening_score if scr else None,
                status=app.status.value,
            )
        )

    # Recent activity items in reverse-chronological order
    recent_activity: List[RecentActivityItem] = []
    for app in reversed(applications[-15:]):
        scr = screening_map.get(app.id)
        job_title = app.job.title if app.job else "Job Requisition"
        company_name = app.job.company_name if app.job else "Hiring Company"

        if app.status == ApplicationStatus.SHORTLISTED:
            act_type = "APPLICATION_SHORTLISTED"
            desc = f"Congratulations! Your application for {job_title} at {company_name} was shortlisted."
        elif app.status == ApplicationStatus.REJECTED:
            act_type = "APPLICATION_REJECTED"
            desc = f"Application for {job_title} at {company_name} was not selected."
        elif app.status == ApplicationStatus.UNDER_REVIEW:
            act_type = "UNDER_REVIEW"
            desc = f"Your application for {job_title} is being reviewed by the hiring team."
        else:
            act_type = "APPLICATION_SUBMITTED"
            desc = f"Successfully submitted application for {job_title} at {company_name}."

        recent_activity.append(
            RecentActivityItem(
                id=app.id,
                activity_type=act_type,
                title=act_type.replace("_", " ").title(),
                description=desc,
                timestamp=app.applied_at,
                status=app.status.value,
                job_id=app.job_id,
                job_title=job_title,
                candidate_name=current_user.full_name,
                metric_value=scr.skill_coverage if scr else None,
            )
        )

    # Count recommended / active jobs
    active_jobs_count = db.query(Job).filter(Job.status == JobStatus.ACTIVE).count()

    return CandidateAnalyticsResponse(
        total_applications=total_applications,
        applications_under_review=under_review_count,
        shortlisted_applications=shortlisted_count,
        rejected_applications=rejected_count,
        status_distribution=status_dist,
        average_skill_coverage=avg_coverage,
        average_semantic_score=avg_semantic,
        profile_completion_percentage=completion,
        has_resume=has_resume,
        recent_activity=recent_activity,
        skill_progress_history=skill_progress_history,
        recommended_jobs_count=active_jobs_count,
    )


# -------------------------------------------------------------------------
# Job Application Endpoints (Candidate Side)
# -------------------------------------------------------------------------

@router.post("/applications", response_model=ApplicationResponse, status_code=status.HTTP_201_CREATED)
def apply_to_job(
    payload: ApplicationCreateRequest,
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Submit a job application for an ACTIVE job requisition and trigger AI screening.

    Validates job existence and active status.
    Prevents duplicate submissions to the same job.
    Attaches candidate's active resume reference and generates preliminary screening score.
    """
    job = db.query(Job).filter(Job.id == payload.job_id).first()
    if not job or job.status != JobStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Job requisition is not active or does not exist.",
        )

    # Prevent duplicate application
    existing_app = (
        db.query(Application)
        .filter(
            Application.candidate_id == current_user.id,
            Application.job_id == payload.job_id,
        )
        .first()
    )
    if existing_app:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="You have already submitted an application for this job.",
        )

    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()

    application = Application(
        candidate_id=current_user.id,
        job_id=job.id,
        status=ApplicationStatus.APPLIED,
        cover_letter=payload.cover_letter,
        resume_id=resume.id if resume else None,
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    # Automated preliminary AI screening if parsed resume is available
    screening_record = None
    if resume:
        parsed_resume = (
            db.query(ParsedResume)
            .filter(
                ParsedResume.resume_id == resume.id,
                ParsedResume.status == ParsingStatus.PARSED,
            )
            .first()
        )
        if parsed_resume and parsed_resume.extracted_data:
            eval_result = screen_candidate_resume(
                job_title=job.title,
                job_description=job.description,
                required_skills=job.required_skills,
                qualification=job.qualification,
                experience_years=job.experience_years,
                parsed_data=parsed_resume.extracted_data,
                raw_text=parsed_resume.raw_text or "",
            )
            candidate_skills = (parsed_resume.extracted_data.get("technical_skills") or []) + (
                parsed_resume.extracted_data.get("soft_skills") or []
            )
            gap_result = analyze_skill_gap(
                candidate_skills=candidate_skills,
                required_skills=job.required_skills,
                candidate_experience_years=parsed_resume.extracted_data.get("experience_years"),
                job_experience_years=job.experience_years,
                resume_text=parsed_resume.raw_text,
                job_description=job.description,
            )
            screening_record = ApplicationScreening(
                application_id=application.id,
                screening_score=eval_result["screening_score"],
                matched_skills=eval_result["matched_skills"],
                missing_skills=eval_result["missing_skills"],
                qualification_match=eval_result["qualification_match"],
                experience_match=eval_result["experience_match"],
                explanation=eval_result["explanation"],
                score_breakdown=eval_result["score_breakdown"],
                skill_coverage=gap_result["coverage_percentage"],
                skill_gap_analysis=gap_result,
            )
            # Compute dense semantic vector similarity score
            try:
                from app.services.embedding import get_embedding_service
                from app.services.semantic_matching import cosine_similarity
                emb_svc = get_embedding_service()
                j_text = emb_svc.prepare_job_text(
                    title=job.title,
                    description=job.description,
                    required_skills=job.required_skills,
                    qualification=job.qualification,
                    experience_years=job.experience_years,
                )
                r_text = emb_svc.prepare_resume_text(
                    extracted_data=parsed_resume.extracted_data or {},
                    raw_text=parsed_resume.raw_text or "",
                )
                j_vec = emb_svc.embed_text(j_text)
                r_vec = emb_svc.embed_text(r_text)
                screening_record.semantic_score = cosine_similarity(j_vec, r_vec)
            except Exception:
                pass

            db.add(screening_record)
            db.commit()
            db.refresh(screening_record)

    return ApplicationResponse(
        id=application.id,
        candidate_id=application.candidate_id,
        job_id=application.job_id,
        status=application.status,
        cover_letter=application.cover_letter,
        resume_id=application.resume_id,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
        job=JobResponse.model_validate(job),
        candidate_name=current_user.full_name,
        candidate_email=current_user.email,
        screening=ScreeningResponse.model_validate(screening_record) if screening_record else None,
        semantic_score=screening_record.semantic_score if screening_record else None,
        skill_coverage=screening_record.skill_coverage if screening_record else None,
    )


@router.get("/applications", response_model=List[ApplicationResponse])
def list_candidate_applications(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """List all job applications submitted by the authenticated candidate."""
    applications = (
        db.query(Application)
        .filter(Application.candidate_id == current_user.id)
        .order_by(Application.applied_at.desc())
        .all()
    )

    results = []
    for app in applications:
        results.append(
            ApplicationResponse(
                id=app.id,
                candidate_id=app.candidate_id,
                job_id=app.job_id,
                status=app.status,
                cover_letter=app.cover_letter,
                resume_id=app.resume_id,
                applied_at=app.applied_at,
                updated_at=app.updated_at,
                job=JobResponse.model_validate(app.job),
                candidate_name=current_user.full_name,
                candidate_email=current_user.email,
                screening=ScreeningResponse.model_validate(app.screening) if app.screening else None,
                semantic_score=app.screening.semantic_score if app.screening else None,
                skill_coverage=app.screening.skill_coverage if app.screening else None,
            )
        )
    return results


@router.get("/applications/{application_id}", response_model=ApplicationResponse)
def get_candidate_application(
    application_id: int,
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Retrieve individual application details."""
    application = (
        db.query(Application)
        .filter(
            Application.id == application_id,
            Application.candidate_id == current_user.id,
        )
        .first()
    )

    if not application:
        other_app = db.query(Application).filter(Application.id == application_id).first()
        if other_app:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You do not have permission to view this application.",
            )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application #{application_id} not found.",
        )

    return ApplicationResponse(
        id=application.id,
        candidate_id=application.candidate_id,
        job_id=application.job_id,
        status=application.status,
        cover_letter=application.cover_letter,
        resume_id=application.resume_id,
        applied_at=application.applied_at,
        updated_at=application.updated_at,
        job=JobResponse.model_validate(application.job),
        candidate_name=current_user.full_name,
        candidate_email=current_user.email,
        screening=ScreeningResponse.model_validate(application.screening) if application.screening else None,
        semantic_score=application.screening.semantic_score if application.screening else None,
        skill_coverage=application.screening.skill_coverage if application.screening else None,
    )


# -------------------------------------------------------------------------
# Semantic Recommendations
# -------------------------------------------------------------------------

@router.get("/jobs/recommended", response_model=List[JobRecommendationResponse])
def get_recommended_jobs(
    limit: int = Query(default=10, ge=1, le=50),
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Retrieve active jobs recommended to the candidate via dense semantic matching."""
    semantic_svc = get_semantic_matching_service()
    recommendations = semantic_svc.get_candidate_job_recommendations(
        db=db,
        candidate_id=current_user.id,
        limit=limit,
    )

    results = []
    for rec in recommendations:
        results.append(
            JobRecommendationResponse(
                job=JobResponse.model_validate(rec["job"]),
                similarity_score=rec["similarity_score"],
                match_tier=rec["match_tier"],
            )
        )
    return results


# -------------------------------------------------------------------------
# Phase 7 Skill-Gap Analysis & Intelligent Recommendations
# -------------------------------------------------------------------------

@router.get("/jobs/{job_id}/skill-gap", response_model=SkillGapAnalysisReport)
@router.get("/skill-gap/job/{job_id}", response_model=SkillGapAnalysisReport)
def get_job_skill_gap(
    job_id: int,
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Evaluate skill-gap and generate structured learning plan for a specific job."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job #{job_id} not found.",
        )

    # Extract candidate skills from parsed resume or profile
    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    parsed_resume = None
    if resume:
        parsed_resume = (
            db.query(ParsedResume)
            .filter(
                ParsedResume.resume_id == resume.id,
                ParsedResume.status == ParsingStatus.PARSED,
            )
            .first()
        )

    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()

    cand_skills: List[str] = []
    resume_text = ""
    cand_exp = None
    if parsed_resume and parsed_resume.extracted_data:
        cand_skills.extend(parsed_resume.extracted_data.get("technical_skills") or [])
        cand_skills.extend(parsed_resume.extracted_data.get("soft_skills") or [])
        resume_text = parsed_resume.raw_text or ""
        cand_exp = parsed_resume.extracted_data.get("experience_years")
    elif profile and profile.skills:
        cand_skills.extend(parse_skill_list(profile.skills))
        cand_exp = profile.experience

    # Run deterministic skill gap analysis
    gap = analyze_skill_gap(
        candidate_skills=cand_skills,
        required_skills=job.required_skills,
        candidate_experience_years=cand_exp,
        job_experience_years=job.experience_years,
        resume_text=resume_text,
        job_description=job.description,
    )

    return SkillGapAnalysisReport(
        job_id=job.id,
        job_title=job.title,
        coverage_percentage=gap["coverage_percentage"],
        match_tier=gap["match_tier"],
        total_required_count=gap["total_required_count"],
        matched_count=gap["matched_count"],
        missing_count=gap["missing_count"],
        matched_skills=gap["matched_skills"],
        missing_skills=gap["missing_skills"],
        partial_skills=[PartialSkillMatch(**p) for p in gap["partial_skills"]],
        additional_skills=gap["additional_skills"],
        skills_to_improve=gap["skills_to_improve"],
        learning_recommendations=[LearningRecommendationItem(**r) for r in gap["learning_recommendations"]],
        strengths_summary=gap["strengths_summary"],
        growth_summary=gap["growth_summary"],
        advisory_note=gap["advisory_note"],
    )


@router.get("/skill-gap/summary")
def get_candidate_skill_gap_summary(
    current_user: User = Depends(candidate_only),
    db: Session = Depends(get_db),
):
    """Aggregate overall candidate skill profile, common market gaps, and top learning roadmaps."""
    resume = db.query(Resume).filter(Resume.candidate_id == current_user.id).first()
    parsed_resume = None
    if resume:
        parsed_resume = (
            db.query(ParsedResume)
            .filter(
                ParsedResume.resume_id == resume.id,
                ParsedResume.status == ParsingStatus.PARSED,
            )
            .first()
        )
    profile = db.query(CandidateProfile).filter(CandidateProfile.user_id == current_user.id).first()

    cand_skills: List[str] = []
    if parsed_resume and parsed_resume.extracted_data:
        cand_skills.extend(parsed_resume.extracted_data.get("technical_skills") or [])
        cand_skills.extend(parsed_resume.extracted_data.get("soft_skills") or [])
    elif profile and profile.skills:
        cand_skills.extend(parse_skill_list(profile.skills))

    # Retrieve all candidate applications
    applications = (
        db.query(Application)
        .filter(Application.candidate_id == current_user.id)
        .all()
    )

    total_apps = len(applications)
    coverages = []
    missing_freq: dict[str, int] = {}

    for app in applications:
        if app.screening and app.screening.skill_coverage is not None:
            coverages.append(app.screening.skill_coverage)
        if app.screening and app.screening.missing_skills:
            for ms in app.screening.missing_skills:
                norm = normalize_skill_name(ms)
                if norm:
                    missing_freq[norm] = missing_freq.get(norm, 0) + 1

    avg_coverage = round(sum(coverages) / len(coverages), 1) if coverages else 0.0

    # Sort missing skills by frequency
    sorted_missing = sorted(missing_freq.items(), key=lambda x: x[1], reverse=True)
    top_missing_skills = [item[0] for item in sorted_missing[:5]]

    # Generate top learning recommendations
    recommendations = []
    for skill in top_missing_skills:
        plan = LEARNING_CATALOG.get(skill)
        if plan:
            recommendations.append(plan)
        else:
            recommendations.append(get_default_learning_plan_for_unknown_skill(skill))

    return {
        "candidate_id": current_user.id,
        "candidate_name": current_user.full_name,
        "total_skills_detected": len(cand_skills),
        "detected_skills": cand_skills,
        "total_applications_analyzed": total_apps,
        "average_skill_coverage": avg_coverage,
        "top_market_skill_gaps": top_missing_skills,
        "recommended_learning_roadmaps": recommendations,
        "advisory_note": (
            "Responsible AI Notice: This summary synthesizes your skill profile across current job applications. "
            "Use these insights to prioritize your upskilling journey. All hiring decisions are made by human recruiters."
        ),
    }
