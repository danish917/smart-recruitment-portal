"""Job Application database model."""

from datetime import datetime
import enum
from sqlalchemy import (
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class ApplicationStatus(str, enum.Enum):
    APPLIED = "APPLIED"
    UNDER_REVIEW = "UNDER_REVIEW"
    SHORTLISTED = "SHORTLISTED"
    REJECTED = "REJECTED"


class Application(Base):
    """Job application linking Candidate to Job with status lifecycle."""

    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    job_id = Column(
        Integer,
        ForeignKey("jobs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum(
            ApplicationStatus,
            name="application_status",
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ApplicationStatus.APPLIED,
        index=True,
    )
    cover_letter = Column(Text, nullable=True)
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="SET NULL"),
        nullable=True,
    )
    applied_at = Column(
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

    # Prevent duplicate applications to the exact same job by the same candidate
    __table_args__ = (
        UniqueConstraint("candidate_id", "job_id", name="uq_candidate_job_application"),
    )

    # Relationships
    candidate = relationship("User", back_populates="applications")
    job = relationship("Job", back_populates="applications")
    resume = relationship("Resume")
    screening = relationship("ApplicationScreening", back_populates="application", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Application id={self.id} candidate_id={self.candidate_id} job_id={self.job_id} status={self.status}>"
