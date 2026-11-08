"""Candidate Profile and Resume database models."""

from datetime import datetime
from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.orm import relationship
from app.database import Base


class CandidateProfile(Base):
    """Candidate professional profile information."""

    __tablename__ = "candidate_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    full_name = Column(String(150), nullable=True)
    phone_number = Column(String(50), nullable=True)
    email = Column(String(255), nullable=True)
    education = Column(String(150), nullable=True)
    college_university = Column(String(200), nullable=True)
    graduation_year = Column(Integer, nullable=True)
    skills = Column(Text, nullable=True)
    experience = Column(String(100), nullable=True)
    location = Column(String(150), nullable=True)
    professional_summary = Column(Text, nullable=True)
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
    user = relationship("User", back_populates="candidate_profile")

    def __repr__(self) -> str:
        return f"<CandidateProfile id={self.id} user_id={self.user_id}>"


class Resume(Base):
    """Uploaded candidate resume metadata referencing secure local/cloud storage."""

    __tablename__ = "resumes"

    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,
        nullable=False,
        index=True,
    )
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_size = Column(Integer, nullable=False)
    content_type = Column(String(100), nullable=False, default="application/pdf")
    file_path = Column(String(500), nullable=False)
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
    candidate = relationship("User", back_populates="resume")
    parsed_resume = relationship("ParsedResume", back_populates="resume", uselist=False, cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Resume id={self.id} candidate_id={self.candidate_id} filename={self.filename}>"
