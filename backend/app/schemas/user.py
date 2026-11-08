"""Pydantic schemas for authentication and user management."""

from datetime import datetime
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from app.models.user import UserRole


class UserRegisterRequest(BaseModel):
    """Schema for user registration request."""

    email: EmailStr
    password: str = Field(..., min_length=8, description="Password must be at least 8 characters.")
    full_name: str = Field(..., min_length=2, max_length=150, description="Full name of the user.")
    role: UserRole = Field(default=UserRole.CANDIDATE, description="User role: CANDIDATE, RECRUITER, or ADMIN.")


class UserLoginRequest(BaseModel):
    """Schema for user login credentials."""

    email: EmailStr
    password: str = Field(..., min_length=1, description="Account password.")


class UserResponse(BaseModel):
    """Public user profile schema."""

    id: int
    email: EmailStr
    full_name: str
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class TokenResponse(BaseModel):
    """JWT access token response."""

    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenPayload(BaseModel):
    """Decoded JWT payload."""

    sub: str  # user id as string
    role: str
    exp: int


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str
