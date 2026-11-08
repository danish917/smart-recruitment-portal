"""Database models for AI Resume Parsing and Screening results."""

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
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class ParsingStatus(str, enum.Enum):
    PENDING = "PENDING"
    PARSED = "PARSED"
    FAILED = "FAILED"
    OCR_REQUIRED = "OCR_REQUIRED"


class ParsedResume(Base):
    """Structured extraction results from candidate PDF resume."""

    __tablename__ = "parsed_resumes"

    id = Column(Integer, primary_key=True, index=True)
    resume_id = Column(
        Integer,
        ForeignKey("resumes.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    candidate_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum(
            ParsingStatus,
            name="parsing_status",
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=ParsingStatus.PENDING,
        index=True,
    )
    raw_text = Column(Text, nullable=True)
    extracted_data = Column(JSON, nullable=True)
    error_message = Column(Text, nullable=True)
    vector_id = Column(String(100), nullable=True, index=True)
    is_indexed = Column(Boolean, default=False, nullable=False)
    indexed_at = Column(DateTime(timezone=True), nullable=True)
    parsed_at = Column(DateTime(timezone=True), nullable=True)
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
    resume = relationship("Resume", back_populates="parsed_resume")
    candidate = relationship("User")

    def __repr__(self) -> str:
        return f"<ParsedResume id={self.id} resume_id={self.resume_id} status={self.status}>"


class ApplicationScreening(Base):
    """Job-specific AI screening evaluation for a candidate's application."""

    __tablename__ = "application_screenings"

    id = Column(Integer, primary_key=True, index=True)
    application_id = Column(
        Integer,
        ForeignKey("applications.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    screening_score = Column(Float, nullable=False, default=0.0)
    semantic_score = Column(Float, nullable=True)
    skill_coverage = Column(Float, nullable=True)
    matched_skills = Column(JSON, nullable=False, default=list)
    missing_skills = Column(JSON, nullable=False, default=list)
    skill_gap_analysis = Column(JSON, nullable=True)
    qualification_match = Column(Boolean, nullable=False, default=False)
    experience_match = Column(Boolean, nullable=False, default=False)
    explanation = Column(Text, nullable=False)
    score_breakdown = Column(JSON, nullable=True)
    screened_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    application = relationship("Application", back_populates="screening")

    def __repr__(self) -> str:
        return f"<ApplicationScreening id={self.id} app_id={self.application_id} score={self.screening_score}>"
