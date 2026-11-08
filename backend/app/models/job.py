"""Job database model for recruiter job postings."""

from datetime import datetime
import enum
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class JobStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    ARCHIVED = "ARCHIVED"


class EmploymentType(str, enum.Enum):
    FULL_TIME = "FULL_TIME"
    PART_TIME = "PART_TIME"
    CONTRACT = "CONTRACT"
    INTERNSHIP = "INTERNSHIP"
    REMOTE = "REMOTE"


class Job(Base):
    """Job posting database model created and managed by recruiters."""

    __tablename__ = "jobs"

    id = Column(Integer, primary_key=True, index=True)
    recruiter_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(200), nullable=False, index=True)
    company_name = Column(String(150), nullable=False)
    description = Column(Text, nullable=False)
    required_skills = Column(Text, nullable=False)
    qualification = Column(String(200), nullable=False)
    experience_years = Column(String(100), nullable=False)
    employment_type = Column(
        Enum(
            EmploymentType,
            name="employment_type",
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=EmploymentType.FULL_TIME,
    )
    work_location = Column(String(150), nullable=False)
    salary_min = Column(Float, nullable=True)
    salary_max = Column(Float, nullable=True)
    salary_currency = Column(String(10), nullable=False, default="USD")
    deadline = Column(DateTime(timezone=True), nullable=True)
    vector_id = Column(String(100), nullable=True, index=True)
    is_indexed = Column(Boolean, default=False, nullable=False)
    indexed_at = Column(DateTime(timezone=True), nullable=True)
    status = Column(
        Enum(
            JobStatus,
            name="job_status",
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=JobStatus.DRAFT,
        index=True,
    )
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    recruiter = relationship("User", back_populates="jobs")
    applications = relationship("Application", back_populates="job", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Job id={self.id} title={self.title} status={self.status} recruiter_id={self.recruiter_id}>"
