from datetime import datetime
import enum
from sqlalchemy import Boolean, Column, DateTime, Enum, Integer, String, func
from sqlalchemy.orm import relationship
from app.database import Base


class UserRole(str, enum.Enum):
    ADMIN = "ADMIN"
    RECRUITER = "RECRUITER"
    CANDIDATE = "CANDIDATE"


class User(Base):
    """User database model supporting role-based access control."""

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(150), nullable=False)
    role = Column(
        Enum(
            UserRole,
            name="user_role",
            native_enum=False,
            values_callable=lambda obj: [e.value for e in obj],
        ),
        nullable=False,
        default=UserRole.CANDIDATE,
    )
    is_active = Column(Boolean, default=True, nullable=False)
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
    jobs = relationship("Job", back_populates="recruiter", cascade="all, delete-orphan")
    candidate_profile = relationship("CandidateProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    resume = relationship("Resume", back_populates="candidate", uselist=False, cascade="all, delete-orphan")
    applications = relationship("Application", back_populates="candidate", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email} role={self.role}>"
