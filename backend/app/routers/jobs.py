"""Public and Candidate Job Discovery API router.

Exposes active job requisitions. Guarantees that DRAFT and ARCHIVED jobs are NEVER returned.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.job import EmploymentType, Job, JobStatus
from app.schemas.job import JobResponse

router = APIRouter(prefix="/api/jobs", tags=["Job Discovery"])


@router.get("", response_model=List[JobResponse])
def discover_active_jobs(
    q: Optional[str] = Query(None, description="Search term matching title or company"),
    location: Optional[str] = Query(None, description="Filter by location substring"),
    employment_type: Optional[EmploymentType] = Query(None, description="Filter by employment type"),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """Search and browse ACTIVE job postings.

    Draft and archived jobs are strictly excluded from discovery results.
    """
    query = db.query(Job).filter(Job.status == JobStatus.ACTIVE)

    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Job.title.ilike(search_term),
                Job.company_name.ilike(search_term),
                Job.required_skills.ilike(search_term),
            )
        )

    if location and location.strip():
        loc_term = f"%{location.strip()}%"
        query = query.filter(Job.work_location.ilike(loc_term))

    if employment_type:
        query = query.filter(Job.employment_type == employment_type)

    jobs = query.order_by(Job.created_at.desc()).offset(skip).limit(limit).all()
    return [JobResponse.model_validate(j) for j in jobs]


@router.get("/{job_id}", response_model=JobResponse)
def get_active_job_details(
    job_id: int,
    db: Session = Depends(get_db),
):
    """Retrieve details for a specific ACTIVE job posting.

    If job is DRAFT or ARCHIVED, returns 404 Not Found to prevent leaking unlisted requisitions.
    """
    job = db.query(Job).filter(Job.id == job_id, Job.status == JobStatus.ACTIVE).first()
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active job #{job_id} not found.",
        )
    return JobResponse.model_validate(job)
