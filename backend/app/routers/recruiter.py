"""Recruiter API Router for Job Postings and Dashboard Metrics."""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.core.deps import require_roles
from app.database import get_db
from app.models.application import Application, ApplicationStatus
from app.models.candidate import Resume
from app.models.job import Job, JobStatus
from app.models.screening import ApplicationScreening, ParsedResume, ParsingStatus
from app.models.user import User, UserRole
from app.schemas.application import (
    ApplicationResponse,
    ApplicationStatusUpdateRequest,
)
from app.schemas.screening import (
    PartialSkillMatch,
    RecruiterApplicantSkillInsight,
    ScreeningResponse,
    SemanticApplicantMatch,
)
from app.schemas.job import (
    JobCreateRequest,
    JobResponse,
    JobUpdateRequest,
    RecruiterDashboardStats,
)
from app.schemas.analytics import (
    JobPerformanceMetric,
    RecentActivityItem,
    RecruiterAnalyticsResponse,
    StatusDistribution,
)
from app.schemas.user import MessageResponse
from app.services.screening import screen_candidate_resume
from app.services.semantic_matching import get_semantic_matching_service
from app.services.skill_gap import analyze_skill_gap
from app.services.storage import StorageService, get_storage_service

router = APIRouter(prefix="/api/recruiter", tags=["Recruiter"])


@router.get(
    "/dashboard/stats",
    response_model=RecruiterDashboardStats,
    summary="Get recruiter dashboard statistics and recent jobs",
)
def get_recruiter_dashboard_stats(
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Fetch statistical metrics for the authenticated recruiter."""
    base_query = db.query(Job).filter(Job.recruiter_id == current_user.id)

    total_jobs = base_query.count()
    active_jobs = base_query.filter(Job.status == JobStatus.ACTIVE).count()
    draft_jobs = base_query.filter(Job.status == JobStatus.DRAFT).count()
    archived_jobs = base_query.filter(Job.status == JobStatus.ARCHIVED).count()

    recent_jobs = (
        base_query.order_by(Job.created_at.desc()).limit(5).all()
    )

    total_applications = (
        db.query(Application)
        .join(Job, Application.job_id == Job.id)
        .filter(Job.recruiter_id == current_user.id)
        .count()
    )

    return RecruiterDashboardStats(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        draft_jobs=draft_jobs,
        archived_jobs=archived_jobs,
        total_applications=total_applications,
        recent_jobs=recent_jobs,
    )


@router.get(
    "/analytics",
    response_model=RecruiterAnalyticsResponse,
    summary="Get comprehensive recruiter analytics and pipeline metrics",
)
def get_recruiter_analytics(
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Retrieve full PostgreSQL analytics for the authenticated recruiter."""
    # 1. Recruiter Jobs
    recruiter_jobs = (
        db.query(Job)
        .filter(Job.recruiter_id == current_user.id)
        .order_by(Job.created_at.desc())
        .all()
    )
    job_ids = [j.id for j in recruiter_jobs]

    total_jobs = len(recruiter_jobs)
    active_jobs = sum(1 for j in recruiter_jobs if j.status == JobStatus.ACTIVE)
    draft_jobs = sum(1 for j in recruiter_jobs if j.status == JobStatus.DRAFT)
    archived_jobs = sum(1 for j in recruiter_jobs if j.status == JobStatus.ARCHIVED)

    if not job_ids:
        return RecruiterAnalyticsResponse(
            total_jobs=total_jobs,
            active_jobs=active_jobs,
            draft_jobs=draft_jobs,
            archived_jobs=archived_jobs,
            total_applications=0,
            applications_under_review=0,
            shortlisted_candidates=0,
            rejected_applications=0,
            average_skill_coverage=None,
            average_semantic_score=None,
            average_screening_score=None,
            status_distribution=StatusDistribution(),
            recent_activity=[],
            top_jobs=[],
        )

    # 2. Applications on Recruiter Jobs
    applications = (
        db.query(Application)
        .filter(Application.job_id.in_(job_ids))
        .order_by(Application.applied_at.desc())
        .all()
    )
    total_applications = len(applications)
    app_ids = [a.id for a in applications]

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

    # 3. Screenings & Averages
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

    screening_scores = [s.screening_score for s in screenings if s.screening_score is not None]
    avg_screening = round(sum(screening_scores) / len(screening_scores), 1) if screening_scores else None

    # 4. Job Performance Breakdown (Top Jobs)
    top_jobs: List[JobPerformanceMetric] = []
    job_map = {j.id: j for j in recruiter_jobs}

    apps_by_job: dict = {}
    for a in applications:
        apps_by_job.setdefault(a.job_id, []).append(a)

    for job in recruiter_jobs:
        job_apps = apps_by_job.get(job.id, [])
        j_app_ids = [a.id for a in job_apps]
        j_screenings = [screening_map[aid] for aid in j_app_ids if aid in screening_map]

        j_coverages = [s.skill_coverage for s in j_screenings if s.skill_coverage is not None]
        j_avg_cov = round(sum(j_coverages) / len(j_coverages), 1) if j_coverages else None

        j_semantics = [s.semantic_score for s in j_screenings if s.semantic_score is not None]
        j_avg_sem = round(sum(j_semantics) / len(j_semantics), 1) if j_semantics else None

        j_shortlisted = sum(1 for a in job_apps if a.status == ApplicationStatus.SHORTLISTED)

        top_jobs.append(
            JobPerformanceMetric(
                job_id=job.id,
                job_title=job.title,
                company_name=job.company_name,
                status=job.status.value,
                applicant_count=len(job_apps),
                average_skill_coverage=j_avg_cov,
                average_semantic_score=j_avg_sem,
                shortlisted_count=j_shortlisted,
            )
        )
    top_jobs.sort(key=lambda x: x.applicant_count, reverse=True)

    # 5. Recent Recruitment Activity
    recent_activity: List[RecentActivityItem] = []
    for app in applications[:15]:
        job = job_map.get(app.job_id)
        scr = screening_map.get(app.id)
        cand_name = app.candidate.full_name if app.candidate else "Candidate"
        job_title = job.title if job else "Job Requisition"

        if app.status == ApplicationStatus.SHORTLISTED:
            act_type = "CANDIDATE_SHORTLISTED"
            desc = f"{cand_name} shortlisted for {job_title}"
        elif app.status == ApplicationStatus.REJECTED:
            act_type = "APPLICATION_REJECTED"
            desc = f"{cand_name} application rejected for {job_title}"
        elif app.status == ApplicationStatus.UNDER_REVIEW:
            act_type = "UNDER_REVIEW"
            desc = f"{cand_name} moved under review for {job_title}"
        else:
            act_type = "APPLICATION_RECEIVED"
            desc = f"New application from {cand_name} for {job_title}"

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
                candidate_name=cand_name,
                metric_value=scr.skill_coverage if scr else None,
            )
        )

    return RecruiterAnalyticsResponse(
        total_jobs=total_jobs,
        active_jobs=active_jobs,
        draft_jobs=draft_jobs,
        archived_jobs=archived_jobs,
        total_applications=total_applications,
        applications_under_review=under_review_count,
        shortlisted_candidates=shortlisted_count,
        rejected_applications=rejected_count,
        average_skill_coverage=avg_coverage,
        average_semantic_score=avg_semantic,
        average_screening_score=avg_screening,
        status_distribution=status_dist,
        recent_activity=recent_activity,
        top_jobs=top_jobs[:5],
    )


@router.get(
    "/jobs",
    response_model=List[JobResponse],
    summary="List all jobs created by the recruiter",
)
def list_recruiter_jobs(
    status_filter: Optional[JobStatus] = Query(default=None, alias="status"),
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Retrieve all job postings owned by the authenticated recruiter."""
    query = db.query(Job).filter(Job.recruiter_id == current_user.id)
    if status_filter:
        query = query.filter(Job.status == status_filter)

    jobs = query.order_by(Job.created_at.desc()).all()
    return jobs


@router.post(
    "/jobs",
    response_model=JobResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new job posting",
)
def create_job(
    payload: JobCreateRequest,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Create a new job posting owned by the authenticated recruiter."""
    new_job = Job(
        recruiter_id=current_user.id,
        title=payload.title.strip(),
        company_name=payload.company_name.strip(),
        description=payload.description.strip(),
        required_skills=payload.required_skills.strip(),
        qualification=payload.qualification.strip(),
        experience_years=payload.experience_years.strip(),
        employment_type=payload.employment_type,
        work_location=payload.work_location.strip(),
        salary_min=payload.salary_min,
        salary_max=payload.salary_max,
        salary_currency=payload.salary_currency.upper(),
        deadline=payload.deadline,
        status=payload.status,
    )
    db.add(new_job)
    db.commit()
    db.refresh(new_job)

    # Index active job vector in Qdrant
    if new_job.status == JobStatus.ACTIVE:
        try:
            semantic_svc = get_semantic_matching_service()
            semantic_svc.index_job_posting(db, new_job.id)
            db.refresh(new_job)
        except Exception:
            pass

    return new_job


@router.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Get details of a specific job posting",
)
def get_job_details(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Fetch details for a job owned by the recruiter."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID #{job_id} not found.",
        )

    # Enforce strict isolation: recruiters can only view their own jobs
    if job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You do not have permission to view this job posting.",
        )

    return job


@router.put(
    "/jobs/{job_id}",
    response_model=JobResponse,
    summary="Update an existing job posting",
)
def update_job(
    job_id: int,
    payload: JobUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Update job fields for a job owned by the authenticated recruiter."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID #{job_id} not found.",
        )

    # Enforce ownership isolation
    if job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot modify job postings owned by other recruiters.",
        )

    # Apply updates for provided fields
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            if isinstance(value, str):
                setattr(job, field, value.strip())
            else:
                setattr(job, field, value)

    db.commit()
    db.refresh(job)

    # Sync Qdrant vector index
    try:
        semantic_svc = get_semantic_matching_service()
        if job.status == JobStatus.ACTIVE:
            semantic_svc.index_job_posting(db, job.id)
        else:
            semantic_svc.deindex_job_posting(db, job.id)
        db.refresh(job)
    except Exception:
        pass

    return job


@router.patch(
    "/jobs/{job_id}/publish",
    response_model=JobResponse,
    summary="Publish a job posting (DRAFT -> ACTIVE)",
)
def publish_job(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Publish a draft job posting."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID #{job_id} not found.",
        )

    if job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot publish job postings owned by other recruiters.",
        )

    job.status = JobStatus.ACTIVE
    db.commit()
    db.refresh(job)

    # Index in Qdrant upon publishing
    try:
        semantic_svc = get_semantic_matching_service()
        semantic_svc.index_job_posting(db, job.id)
        db.refresh(job)
    except Exception:
        pass

    return job


@router.patch(
    "/jobs/{job_id}/archive",
    response_model=JobResponse,
    summary="Archive a job posting (ACTIVE -> ARCHIVED)",
)
def archive_job(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Archive an active or draft job posting."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID #{job_id} not found.",
        )

    if job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot archive job postings owned by other recruiters.",
        )

    job.status = JobStatus.ARCHIVED
    db.commit()
    db.refresh(job)

    # De-index from Qdrant upon archival
    try:
        semantic_svc = get_semantic_matching_service()
        semantic_svc.deindex_job_posting(db, job.id)
        db.refresh(job)
    except Exception:
        pass

    return job


@router.delete(
    "/jobs/{job_id}",
    response_model=MessageResponse,
    summary="Delete a job posting",
)
def delete_job(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Permanently delete a job posting owned by the recruiter."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job with ID #{job_id} not found.",
        )

    if job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot delete job postings owned by other recruiters.",
        )

    # Remove from Qdrant
    try:
        semantic_svc = get_semantic_matching_service()
        semantic_svc.deindex_job_posting(db, job.id)
    except Exception:
        pass

    db.delete(job)
    db.commit()
    return MessageResponse(message=f"Job #{job_id} has been permanently deleted.")


@router.get(
    "/jobs/{job_id}/applications",
    response_model=List[ApplicationResponse],
    summary="List all applications submitted to a recruiter's job",
)
def get_job_applications(
    job_id: int,
    sort_by: Optional[str] = Query(default="date", description="Sort by: date, skill_coverage, semantic, screening"),
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Retrieve all candidate applications submitted for a job owned by the recruiter."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job #{job_id} not found.",
        )

    if job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot view applications for jobs owned by other recruiters.",
        )

    query = db.query(Application).filter(Application.job_id == job_id)

    if sort_by == "skill_coverage":
        query = query.outerjoin(ApplicationScreening).order_by(ApplicationScreening.skill_coverage.desc().nullslast(), Application.applied_at.desc())
    elif sort_by == "semantic":
        query = query.outerjoin(ApplicationScreening).order_by(ApplicationScreening.semantic_score.desc().nullslast(), Application.applied_at.desc())
    elif sort_by == "screening":
        query = query.outerjoin(ApplicationScreening).order_by(ApplicationScreening.screening_score.desc().nullslast(), Application.applied_at.desc())
    else:
        query = query.order_by(Application.applied_at.desc())

    applications = query.all()

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
                candidate_name=app.candidate.full_name,
                candidate_email=app.candidate.email,
                screening=ScreeningResponse.model_validate(app.screening) if app.screening else None,
                semantic_score=app.screening.semantic_score if app.screening else None,
                skill_coverage=app.screening.skill_coverage if app.screening else None,
            )
        )
    return results


@router.get(
    "/jobs/{job_id}/skill-insights",
    response_model=List[RecruiterApplicantSkillInsight],
    summary="Detailed skill coverage breakdown for all job applicants",
)
def get_job_skill_insights(
    job_id: int,
    sort_by: Optional[str] = Query(default="skill_coverage", description="Sort by: skill_coverage, semantic_score, screening_score, applied_at"),
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Inspect and sort applicant skill coverage, matched vs missing skills, and candidate strengths."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job #{job_id} not found.",
        )

    if job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot view skill insights for jobs owned by other recruiters.",
        )

    applications = (
        db.query(Application)
        .filter(Application.job_id == job_id)
        .all()
    )

    insights = []
    for app in applications:
        screening = app.screening
        coverage = screening.skill_coverage if screening and screening.skill_coverage is not None else 0.0
        screening_score = screening.screening_score if screening else None
        semantic_score = screening.semantic_score if screening else None
        matched = screening.matched_skills if screening and screening.matched_skills else []
        missing = screening.missing_skills if screening and screening.missing_skills else []
        additional = []
        partial_list = []

        if screening and screening.skill_gap_analysis:
            additional = screening.skill_gap_analysis.get("additional_skills") or []
            raw_partial = screening.skill_gap_analysis.get("partial_skills") or []
            partial_list = [PartialSkillMatch(**p) for p in raw_partial]
        else:
            # Fallback compute on the fly if screened prior to Phase 7
            candidate_skills = []
            resume = db.query(Resume).filter(Resume.id == app.resume_id).first() if app.resume_id else None
            parsed_resume = db.query(ParsedResume).filter(ParsedResume.resume_id == resume.id).first() if resume else None
            if parsed_resume and parsed_resume.extracted_data:
                candidate_skills.extend(parsed_resume.extracted_data.get("technical_skills") or [])
                candidate_skills.extend(parsed_resume.extracted_data.get("soft_skills") or [])
                gap = analyze_skill_gap(
                    candidate_skills=candidate_skills,
                    required_skills=job.required_skills,
                    candidate_experience_years=parsed_resume.extracted_data.get("experience_years"),
                    job_experience_years=job.experience_years,
                    resume_text=parsed_resume.raw_text,
                    job_description=job.description,
                )
                coverage = gap["coverage_percentage"]
                matched = gap["matched_skills"]
                missing = gap["missing_skills"]
                additional = gap["additional_skills"]
                partial_list = [PartialSkillMatch(**p) for p in gap["partial_skills"]]

        insights.append(
            RecruiterApplicantSkillInsight(
                application_id=app.id,
                candidate_id=app.candidate_id,
                candidate_name=app.candidate.full_name,
                candidate_email=app.candidate.email,
                skill_coverage=coverage,
                screening_score=screening_score,
                semantic_score=semantic_score,
                matched_skills=matched,
                missing_skills=missing,
                additional_skills=additional,
                partial_skills=partial_list,
                status=app.status.value if hasattr(app.status, "value") else str(app.status),
                applied_at=app.applied_at,
            )
        )

    # Sort insights according to parameter
    if sort_by == "semantic_score":
        insights.sort(key=lambda x: (x.semantic_score is not None, x.semantic_score or 0.0), reverse=True)
    elif sort_by == "screening_score":
        insights.sort(key=lambda x: (x.screening_score is not None, x.screening_score or 0.0), reverse=True)
    elif sort_by == "applied_at":
        insights.sort(key=lambda x: x.applied_at, reverse=True)
    else:  # default skill_coverage
        insights.sort(key=lambda x: x.skill_coverage, reverse=True)

    return insights


@router.patch(
    "/applications/{application_id}/status",
    response_model=ApplicationResponse,
    summary="Update application lifecycle status",
)
def update_application_status(
    application_id: int,
    payload: ApplicationStatusUpdateRequest,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Update an applicant's status (UNDER_REVIEW, SHORTLISTED, REJECTED)."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application #{application_id} not found.",
        )

    if application.job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot update applications for jobs owned by other recruiters.",
        )

    application.status = payload.status
    db.commit()
    db.refresh(application)

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
        candidate_name=application.candidate.full_name,
        candidate_email=application.candidate.email,
        screening=ScreeningResponse.model_validate(application.screening) if application.screening else None,
        semantic_score=application.screening.semantic_score if application.screening else None,
    )


@router.post(
    "/applications/{application_id}/screen",
    response_model=ScreeningResponse,
    summary="Trigger or re-evaluate AI screening for an application",
)
def screen_application(
    application_id: int,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Run job-specific AI screening evaluation against applicant's parsed resume."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application #{application_id} not found.",
        )

    if application.job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot screen applications for jobs owned by other recruiters.",
        )

    if not application.resume_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This application has no attached resume to screen.",
        )

    parsed_resume = (
        db.query(ParsedResume)
        .filter(ParsedResume.resume_id == application.resume_id)
        .first()
    )
    if not parsed_resume or not parsed_resume.extracted_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Attached resume has not been parsed or is in OCR_REQUIRED / FAILED status.",
        )

    job = application.job
    eval_result = screen_candidate_resume(
        job_title=job.title,
        job_description=job.description,
        required_skills=job.required_skills,
        qualification=job.qualification,
        experience_years=job.experience_years,
        parsed_data=parsed_resume.extracted_data,
        raw_text=parsed_resume.raw_text or "",
    )

    screening = (
        db.query(ApplicationScreening)
        .filter(ApplicationScreening.application_id == application.id)
        .first()
    )
    if screening:
        screening.screening_score = eval_result["screening_score"]
        screening.matched_skills = eval_result["matched_skills"]
        screening.missing_skills = eval_result["missing_skills"]
        screening.qualification_match = eval_result["qualification_match"]
        screening.experience_match = eval_result["experience_match"]
        screening.explanation = eval_result["explanation"]
        screening.score_breakdown = eval_result["score_breakdown"]
    else:
        screening = ApplicationScreening(
            application_id=application.id,
            screening_score=eval_result["screening_score"],
            matched_skills=eval_result["matched_skills"],
            missing_skills=eval_result["missing_skills"],
            qualification_match=eval_result["qualification_match"],
            experience_match=eval_result["experience_match"],
            explanation=eval_result["explanation"],
            score_breakdown=eval_result["score_breakdown"],
        )
        db.add(screening)

    # Compute dense semantic score
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
        screening.semantic_score = cosine_similarity(j_vec, r_vec)
    except Exception:
        pass

    db.commit()
    db.refresh(screening)

    return ScreeningResponse.model_validate(screening)


@router.post(
    "/jobs/{job_id}/index-vector",
    response_model=JobResponse,
    summary="Index or refresh dense vector embedding for a job in Qdrant",
)
def index_job_vector(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Explicitly generate vector embedding and index active job in Qdrant."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job #{job_id} not found.",
        )

    if job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot index job postings owned by other recruiters.",
        )

    if job.status != JobStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only ACTIVE job postings can be indexed in the vector database.",
        )

    semantic_svc = get_semantic_matching_service()
    point_id = semantic_svc.index_job_posting(db, job.id)
    if not point_id:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate vector embedding or index job in Qdrant.",
        )

    db.refresh(job)
    return job


@router.get(
    "/jobs/{job_id}/semantic-matches",
    response_model=List[SemanticApplicantMatch],
    summary="Rank applicants by dense semantic similarity to job requisition",
)
def get_job_semantic_applicant_matches(
    job_id: int,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
):
    """Rank job applicants by dense vector cosine similarity."""
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job #{job_id} not found.",
        )

    if job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot view applicants for jobs owned by other recruiters.",
        )

    semantic_svc = get_semantic_matching_service()
    ranked_results = semantic_svc.rank_applicants_semantically(db, job.id)

    matches = []
    for item in ranked_results:
        app = item["application"]
        screening = item.get("screening")
        score = item.get("semantic_score") or 0.0

        matches.append(
            SemanticApplicantMatch(
                application_id=app.id,
                candidate_id=app.candidate_id,
                candidate_name=app.candidate.full_name,
                candidate_email=app.candidate.email,
                semantic_score=score,
                screening_score=screening.screening_score if screening else None,
                skill_coverage=screening.skill_coverage if screening else None,
                matched_skills=screening.matched_skills if screening and screening.matched_skills else [],
                missing_skills=screening.missing_skills if screening and screening.missing_skills else [],
                status=app.status.value if hasattr(app.status, "value") else str(app.status),
                applied_at=app.applied_at,
            )
        )

    return matches


@router.get(
    "/applications/{application_id}/resume",
    summary="Securely view/download applicant resume",
)
def get_applicant_resume(
    application_id: int,
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
    db: Session = Depends(get_db),
    storage: StorageService = Depends(get_storage_service),
):
    """Securely download candidate resume attached to this application."""
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Application #{application_id} not found.",
        )

    if application.job.recruiter_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied: You cannot view applicant resumes for jobs owned by other recruiters.",
        )

    if not application.resume_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="This application does not have an attached resume.",
        )

    resume = db.query(Resume).filter(Resume.id == application.resume_id).first()
    if not resume:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Resume record not found.",
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
        filename=f"{application.candidate.full_name.replace(' ', '_')}_{resume.original_filename}",
    )
