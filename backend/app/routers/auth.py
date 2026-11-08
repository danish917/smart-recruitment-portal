"""Authentication router providing registration, login, profile, and role verification."""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.core.config import settings
from app.core.deps import get_current_user, require_roles
from app.core.rate_limiter import rate_limit
from app.core.security import create_access_token, hash_password, verify_password
from app.database import get_db
from app.models.user import User, UserRole
from app.schemas.user import (
    MessageResponse,
    TokenResponse,
    UserLoginRequest,
    UserRegisterRequest,
    UserResponse,
)

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    dependencies=[Depends(rate_limit(settings.MAX_REGISTER_ATTEMPTS_PER_MINUTE, 60))],
)
def register(
    payload: UserRegisterRequest,
    db: Session = Depends(get_db),
):
    """Register a new candidate or recruiter with secure password hashing."""
    # Check if email is already taken
    existing_user = db.query(User).filter(User.email == payload.email.lower()).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email address already exists.",
        )

    # Hash the password
    hashed_pwd = hash_password(payload.password)

    # Create and persist the user
    new_user = User(
        email=payload.email.lower(),
        hashed_password=hashed_pwd,
        full_name=payload.full_name.strip(),
        role=payload.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Authenticate user and issue JWT token",
    dependencies=[Depends(rate_limit(settings.MAX_LOGIN_ATTEMPTS_PER_MINUTE, 60))],
)
def login(
    payload: UserLoginRequest,
    db: Session = Depends(get_db),
):
    """Authenticate credentials and issue a signed JWT Bearer access token."""
    user = db.query(User).filter(User.email == payload.email.lower()).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive or suspended. Please contact support.",
        )

    # Issue JWT token
    access_token = create_access_token(subject=user.id, role=user.role.value)

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        user=UserResponse.model_validate(user),
    )


@router.post(
    "/logout",
    response_model=MessageResponse,
    summary="Client session logout",
)
def logout():
    """Stateless JWT logout endpoint for client session cleanup."""
    return MessageResponse(message="Logged out successfully.")


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Get authenticated user profile",
)
def get_me(current_user: User = Depends(get_current_user)):
    """Fetch current user identity verified via JWT token."""
    return current_user


# Role-Based Verification Endpoints
@router.get(
    "/recruiter-dashboard",
    response_model=MessageResponse,
    summary="Protected recruiter area",
)
def recruiter_dashboard(
    current_user: User = Depends(require_roles(UserRole.RECRUITER, UserRole.ADMIN)),
):
    """Accessible only to users with RECRUITER or ADMIN roles."""
    return MessageResponse(
        message=f"Recruiter access granted for {current_user.full_name} ({current_user.role.value})."
    )


@router.get(
    "/candidate-dashboard",
    response_model=MessageResponse,
    summary="Protected candidate area",
)
def candidate_dashboard(
    current_user: User = Depends(require_roles(UserRole.CANDIDATE, UserRole.ADMIN)),
):
    """Accessible only to users with CANDIDATE or ADMIN roles."""
    return MessageResponse(
        message=f"Candidate access granted for {current_user.full_name} ({current_user.role.value})."
    )


@router.get(
    "/admin-panel",
    response_model=MessageResponse,
    summary="Protected admin area",
)
def admin_panel(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    """Accessible only to users with the ADMIN role."""
    return MessageResponse(
        message=f"Admin privileges confirmed for {current_user.full_name}."
    )
