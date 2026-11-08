from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from app.core.config import settings
from app.database import check_db_health
from app.routers import auth, candidate, jobs, recruiter

app = FastAPI(
    title="Smart Recruitment Portal API",
    description="Backend API for Smart Recruitment Portal (FastAPI, Neon PostgreSQL, JWT Auth, Recruiter, Candidate & Analytics Modules)",
    version="0.8.0",
)

# Security Response Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    """Enforce standard HTTP security headers on all responses."""
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Configure CORS dynamically from settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(recruiter.router)
app.include_router(candidate.router)
app.include_router(jobs.router)


@app.get("/health", tags=["Health"])
async def health_check():
    """Health check endpoint to verify backend service and database status."""
    db_health = check_db_health()
    return {
        "status": "healthy" if db_health.get("status") == "connected" else "degraded",
        "service": "smart-recruitment-portal-backend",
        "version": "0.8.0",
        "database": db_health,
    }


@app.get("/health/db", tags=["Health"])
async def database_health():
    """Dedicated endpoint for database connectivity verification."""
    return check_db_health()


@app.get("/", tags=["Root"])
async def root():
    """Root endpoint providing service metadata."""
    return {
        "message": "Welcome to Smart Recruitment Portal API",
        "docs_url": "/docs",
        "health_url": "/health",
        "modules": {
            "auth": "/api/auth",
            "recruiter": "/api/recruiter",
            "candidate": "/api/candidate",
            "jobs": "/api/jobs",
        },
    }
