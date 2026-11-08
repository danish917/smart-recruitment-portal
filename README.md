# Smart Recruitment Portal

An enterprise-grade, AI-driven recruitment and talent acquisition platform featuring NLP resume parsing, dense vector embeddings with Qdrant, 3-pillar candidate-job screening, automated skill-gap analysis, live analytics dashboards, and end-to-end security hardening.

---

## 🏗️ Architecture & Technology Stack

The platform is designed as a decoupled, multi-service architecture:

- **Frontend**: Next.js 16 (React 19, TypeScript, Tailwind CSS, Lucide Icons) with App Router, partial prefetching, and client-side JWT token management.
- **Backend**: FastAPI (Python 3.11, Uvicorn, Pydantic v2), RESTful architecture with modular routers and custom middleware.
- **Relational Database**: Neon Serverless PostgreSQL with SQLAlchemy 2.0 ORM and Alembic schema migrations.
- **Vector Database**: Qdrant (local persistent storage or Qdrant Cloud cluster) for dense embeddings and semantic vector search.
- **Embeddings & NLP Engine**: `sentence-transformers` (`all-MiniLM-L6-v2`, 384-dimensional dense vectors), `pypdf` for text extraction, and rule-based heuristic extraction for skills, education, and experience.
- **Storage**: Pluggable storage abstraction supporting local file system storage with magic-byte verification and S3-compatible cloud object storage (AWS S3, Cloudflare R2, MinIO).
- **Security & Protection**: In-memory sliding-window rate limiter per client IP, HTTP security headers middleware (`X-Content-Type-Options`, `X-Frame-Options`, `X-XSS-Protection`, `Referrer-Policy`), dynamic CORS, and strict role-based access control (RBAC).
- **Containerization**: Multi-stage production `Dockerfile`s for frontend and backend, with a unified `docker-compose.yml` orchestrating FastAPI, Next.js, and Qdrant.

---

## 📁 Repository Structure

```
recuitment portel/
├── backend/
│   ├── alembic/                      # Database schema migrations
│   │   ├── versions/                 # Alembic migration revisions (up to Phase 7/8)
│   │   └── env.py                    # Alembic migration environment
│   ├── app/
│   │   ├── core/                     # Configuration, security & utilities
│   │   │   ├── config.py             # App settings (Pydantic Settings)
│   │   │   ├── security.py           # Password hashing (bcrypt) & JWT management
│   │   │   ├── deps.py               # Dependency injection (Auth, RBAC)
│   │   │   └── rate_limiter.py       # Sliding-window rate limiter
│   │   ├── models/                   # SQLAlchemy ORM models
│   │   │   ├── user.py               # User & UserRole (ADMIN, RECRUITER, CANDIDATE)
│   │   │   ├── job.py                # Job & JobStatus (DRAFT, ACTIVE, ARCHIVED)
│   │   │   ├── application.py        # Application, Resume, Screening, ParsedResume
│   │   │   └── candidate_profile.py  # Candidate profile information
│   │   ├── schemas/                  # Pydantic request/response validation
│   │   │   ├── user.py               # User & Auth schemas
│   │   │   ├── job.py                # Job requisitions schemas
│   │   │   ├── application.py        # Applications & candidate profiles
│   │   │   ├── screening.py          # AI screening & skill-gap schemas
│   │   │   └── analytics.py          # Recruiter & Candidate analytics metrics
│   │   ├── services/                 # Core domain & business services
│   │   │   ├── storage.py            # Local & S3 object storage abstraction
│   │   │   ├── resume_parser.py      # PDF text & NLP entity extraction
│   │   │   ├── screening_engine.py   # Rule-based screening & scoring
│   │   │   ├── embedding_service.py  # Sentence-Transformers dense embedding
│   │   │   ├── vector_db.py          # Qdrant client & vector indexing service
│   │   │   └── skill_gap_service.py  # 3-pillar matching & recommendation engine
│   │   ├── routers/                  # Modular FastAPI routers
│   │   │   ├── auth.py               # /api/auth: Register, login, me, logout
│   │   │   ├── recruiter.py          # /api/recruiter: Jobs, applications, analytics
│   │   │   ├── candidate.py          # /api/candidate: Profiles, resumes, applications, analytics
│   │   │   └── jobs.py               # /api/jobs: Public active job board
│   │   ├── database.py               # SQLAlchemy database session & engine
│   │   └── main.py                   # FastAPI application initialization & middleware
│   ├── tests/                        # Comprehensive test suite (70+ unit & integration tests)
│   │   ├── test_main.py              # Health check & basic API tests
│   │   ├── test_auth.py              # Authentication & RBAC tests
│   │   ├── test_recruiter_module.py  # Job lifecycle & recruiter workflows
│   │   ├── test_candidate_module.py  # Profile, resume upload & application tests
│   │   ├── test_nlp_screening.py     # Resume parsing & heuristic screening tests
│   │   ├── test_qdrant_semantic_matching.py # Vector embedding & Qdrant search tests
│   │   ├── test_skill_gap_analysis.py # 3-pillar matching & recommendations tests
│   │   └── test_analytics_and_security.py # Rate limiting, headers & analytics tests
│   ├── Dockerfile                    # Production backend Dockerfile
│   ├── .dockerignore                 # Backend docker build exclusions
│   ├── requirements.txt              # Python production dependencies
│   └── .env.example                  # Backend environment template
│
├── frontend/
│   ├── src/
│   │   ├── app/                      # Next.js App Router
│   │   │   ├── login/                # Sign-in page
│   │   │   ├── register/             # Registration page (Role selection)
│   │   │   ├── recruiter/
│   │   │   │   ├── dashboard/        # Recruiter live analytics dashboard
│   │   │   │   ├── jobs/             # Job requisition management (CRUD)
│   │   │   │   └── applications/     # Candidate screening & pipeline management
│   │   │   ├── candidate/
│   │   │   │   ├── dashboard/        # Candidate analytics & application status
│   │   │   │   ├── profile/          # Profile & resume management
│   │   │   │   ├── jobs/             # Semantic job discovery & recommendations
│   │   │   │   └── applications/     # Application history & skill gap breakdown
│   │   │   ├── layout.tsx            # Root layout
│   │   │   ├── globals.css           # Global Tailwind CSS styles
│   │   │   └── page.tsx              # Public home page
│   │   └── lib/                      # Client utilities & API services
│   │       ├── api.ts                # Base fetch client with Bearer auth injection
│   │       ├── auth.ts               # Auth state & token storage
│   │       ├── jobs.ts               # Recruiter jobs & analytics API client
│   │       └── candidate.ts          # Candidate profile, application & analytics client
│   ├── Dockerfile                    # Production frontend Dockerfile
│   ├── .dockerignore                 # Frontend docker build exclusions
│   ├── package.json                  # Next.js scripts & npm dependencies
│   ├── tsconfig.json                 # TypeScript compiler configuration
│   └── next.config.ts                # Next.js build & standalone configuration
│
├── docker-compose.yml                # Unified multi-container orchestration
├── neon.ts                           # Neon configuration
└── README.md                         # Comprehensive project documentation
```

---

## 🚀 Completed Phases Overview

1. **Phase 1: Project Foundation & Neon PostgreSQL**
   - Clean architecture setup separating FastAPI backend and Next.js frontend.
   - Initialized Neon Serverless PostgreSQL with connection pooling.
2. **Phase 2: Authentication & User Management**
   - Role-Based Access Control (`ADMIN`, `RECRUITER`, `CANDIDATE`).
   - Secure password hashing using `bcrypt`, stateless JWT access tokens, and protected `/api/auth/me`.
3. **Phase 3: Recruiter Module**
   - Job requisition lifecycle (`DRAFT`, `ACTIVE`, `ARCHIVED`).
   - Applicant pipeline review with status progression (`PENDING`, `REVIEWING`, `SHORTLISTED`, `REJECTED`, `HIRED`).
4. **Phase 4: Candidate Profile & Resume Management**
   - Candidate profile creation and updating.
   - Multi-resume upload, version tracking, primary resume designation, and isolated download streams.
5. **Phase 5: AI Resume Parsing & Intelligent Screening**
   - PDF text extraction via `pypdf` with error recovery.
   - Heuristic NLP entity extraction: technical skills, soft skills, education, and experience.
   - Automated candidate screening engine producing score breakdowns and qualification flags.
6. **Phase 6: Qdrant Vector Database, Dense Embeddings & Semantic Matching**
   - Integrated Qdrant vector database with in-memory fallback for testing.
   - Text embedding generation using `sentence-transformers/all-MiniLM-L6-v2` (384-dim).
   - Deterministic vector UUIDs (`uuid5`) and semantic similarity scoring between candidate resumes and job postings.
7. **Phase 7: Skill-Gap Analysis & Intelligent Recommendations**
   - 3-Pillar matching algorithm: Technical Skill Match (45%), Experience & Education Match (30%), Semantic Alignment (25%).
   - Missing required vs preferred skill categorization.
   - Actionable career recommendations and curated learning resource paths.
8. **Phase 8: Analytics, Security Hardening & Production Deployment**
   - Live Recruiter Analytics (pipeline distribution, score averages, top jobs, recruitment feed).
   - Live Candidate Analytics (application status distribution, skill coverage, chronological progression).
   - Security hardening: HTTP security headers, sliding-window IP rate limiting, path traversal defense, and magic-byte validation.
   - Multi-stage Docker containerization and comprehensive documentation.

---

## 🔐 API Reference

### 1. Authentication (`/api/auth`)
- `POST /api/auth/register`: Register new user (`RECRUITER` or `CANDIDATE`). *Rate limited.*
- `POST /api/auth/login`: Authenticate credentials and receive JWT Bearer token. *Rate limited.*
- `POST /api/auth/logout`: Stateless session logout.
- `GET /api/auth/me`: Current authenticated user profile.
- `GET /api/auth/recruiter-dashboard`: Recruiter/Admin role check.
- `GET /api/auth/candidate-dashboard`: Candidate/Admin role check.
- `GET /api/auth/admin-panel`: Admin exclusive endpoint.

### 2. Recruiter Operations (`/api/recruiter`)
- `GET /api/recruiter/analytics`: Live recruitment pipeline metrics and activity feed.
- `GET /api/recruiter/jobs`: List all requisitions created by authenticated recruiter.
- `POST /api/recruiter/jobs`: Create new job posting.
- `GET /api/recruiter/jobs/{job_id}`: Retrieve job requisition details.
- `PUT /api/recruiter/jobs/{job_id}`: Update job requisition.
- `DELETE /api/recruiter/jobs/{job_id}`: Archive job requisition.
- `GET /api/recruiter/jobs/{job_id}/applications`: View applicant pipeline with AI screening scores.
- `PUT /api/recruiter/applications/{app_id}/status`: Update candidate application status.
- `GET /api/recruiter/applications/{app_id}/screening`: Detailed screening breakdown and skill-gap report.
- `GET /api/recruiter/resumes/{resume_id}/download`: Download applicant resume PDF securely.

### 3. Candidate Operations (`/api/candidate`)
- `GET /api/candidate/analytics`: Live application pipeline metrics, skill averages, and progression history.
- `GET /api/candidate/profile`: Retrieve candidate profile.
- `PUT /api/candidate/profile`: Update candidate profile details.
- `POST /api/candidate/resume/upload`: Upload PDF resume. Triggers NLP parsing and vector indexing. *Rate limited.*
- `GET /api/candidate/resumes`: List uploaded candidate resumes.
- `PUT /api/candidate/resumes/{resume_id}/primary`: Set primary resume.
- `GET /api/candidate/resumes/{resume_id}/download`: Download own resume PDF.
- `GET /api/candidate/recommendations`: Top semantic job recommendations based on candidate resume.
- `GET /api/candidate/jobs/{job_id}/skill-gap`: On-demand 3-pillar skill gap analysis for a job.
- `POST /api/candidate/applications`: Submit application for an active job requisition.
- `GET /api/candidate/applications`: View submitted applications and status updates.

### 4. Public Job Board (`/api/jobs`)
- `GET /api/jobs`: List all active job postings with search and filtering.
- `GET /api/jobs/{job_id}`: View public details of an active job posting.

---

## 💻 Local Development Setup

### Prerequisites
- Python 3.11+
- Node.js 20+ and npm
- PostgreSQL database (or Neon Serverless PostgreSQL connection)
- (Optional) Qdrant running locally via Docker on port 6333

### Backend Setup

1. **Activate virtual environment**:
   ```powershell
   # Windows PowerShell
   cd backend
   python -m venv venv
   .\venv\Scripts\Activate.ps1
   ```

2. **Install dependencies**:
   ```powershell
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables**:
   Create `backend/.env` using `.env.example` as reference:
   ```env
   DATABASE_URL=postgresql://user:password@ep-sample-pooler.us-east-2.aws.neon.tech/neondb?sslmode=require
   JWT_SECRET_KEY=your_super_secret_jwt_key_min_32_chars
   JWT_ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=60
   QDRANT_HOST=localhost
   QDRANT_PORT=6333
   CORS_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
   RATE_LIMIT_ENABLED=True
   STORAGE_BACKEND=local
   RESUME_STORAGE_DIR=resumes
   ```

4. **Run Database Migrations**:
   ```powershell
   $env:PYTHONPATH = "E:\recuitment portel\backend"
   .\venv\Scripts\alembic.exe upgrade head
   ```

5. **Start FastAPI Development Server**:
   ```powershell
   .\venv\Scripts\uvicorn.exe app.main:app --reload --port 8000
   ```
   API Swagger Docs will be available at: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### Frontend Setup

1. **Navigate and install dependencies**:
   ```powershell
   cd frontend
   npm install
   ```

2. **Configure Environment Variables**:
   Create `frontend/.env.local`:
   ```env
   NEXT_PUBLIC_API_URL=http://localhost:8000
   ```

3. **Run Next.js Development Server**:
   ```powershell
   npm run dev
   ```
   The application will be accessible at: [http://localhost:3000](http://localhost:3000)

---

## 🧪 Running Automated Tests

The backend test suite covers the complete system across 8 test modules:
```powershell
# Run the complete test suite
cd "E:\recuitment portel"
backend\venv\Scripts\python.exe -m pytest backend/tests -v
```

Test coverage includes:
- `test_main.py`: Database connection & health checks.
- `test_auth.py`: Registration, JWT issuance, password hashing, and RBAC enforcement.
- `test_recruiter_module.py`: Job requisition lifecycle, application reviews, and status updates.
- `test_candidate_module.py`: Profile updates, resume upload, primary selection, and application submissions.
- `test_nlp_screening.py`: PDF text extraction, NLP heuristics, and automated screening scoring.
- `test_qdrant_semantic_matching.py`: Dense embedding generation, Qdrant CRUD, and semantic job recommendations.
- `test_skill_gap_analysis.py`: 3-pillar scoring breakdown, missing skills detection, and learning path generation.
- `test_analytics_and_security.py`: HTTP security headers, sliding-window rate limiting (429), recruiter analytics, recruiter isolation, candidate analytics, resume download authorization & isolation, path traversal defense, and magic byte validation.

---

## 🐳 Docker & Docker Compose Deployment

The platform is containerized for production readiness using Docker Compose.

### Docker Compose Architecture:
- `backend`: FastAPI Python service running Uvicorn with a non-root user.
- `frontend`: Next.js standalone multi-stage production build running Node.js.
- `qdrant`: Qdrant vector database container with persistent volume storage (`qdrant-data`).
- `resume-data`: Persistent named volume for secure local resume storage.

### Running via Docker Compose:

1. **Build and start all services**:
   ```bash
   docker compose up --build -d
   ```

2. **Verify services**:
   - Frontend: [http://localhost:3000](http://localhost:3000)
   - Backend API: [http://localhost:8000](http://localhost:8000)
   - Swagger Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)
   - Qdrant Web UI: [http://localhost:6333/dashboard](http://localhost:6333/dashboard)

3. **Stop services**:
   ```bash
   docker compose down
   ```

---

## 🌐 Production Cloud Deployment Guide

| Component | Recommended Host | Configuration Notes |
| :--- | :--- | :--- |
| **Frontend** | Vercel or AWS Amplify | Set `NEXT_PUBLIC_API_URL` to backend URL. Connect GitHub repo for automated CI/CD. |
| **Backend** | Render, Railway, or AWS ECS | Docker container or Python 3.11 runtime. Command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. |
| **Database** | Neon Serverless PostgreSQL | Set `DATABASE_URL` with SSL mode (`sslmode=require`). Free tier handles scale with connection pooling. |
| **Vector DB** | Qdrant Cloud | Set `QDRANT_URL` and `QDRANT_API_KEY` in backend environment variables. |
| **Object Storage** | Cloudflare R2 or AWS S3 | Set `STORAGE_BACKEND=s3`, `S3_BUCKET_NAME`, `S3_ACCESS_KEY_ID`, `S3_SECRET_ACCESS_KEY`. |

---

## 🛡️ Security Best Practices Implemented

- **Password Hashing**: Bcrypt with automatic salt generation; plain passwords never stored or logged.
- **JWT Authentication**: HS256 stateless tokens with configurable expiration, verified on every protected request.
- **Role-Based Access Control**: Strict dependency enforcement separating `ADMIN`, `RECRUITER`, and `CANDIDATE` operations.
- **Rate Limiting**: Sliding-window IP rate limiter on sensitive endpoints (`/register`, `/login`, `/resume/upload`) returning HTTP 429 and `Retry-After` headers.
- **Security Response Headers**: Enforces `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 1; mode=block`, and `Referrer-Policy: strict-origin-when-cross-origin`.
- **Dynamic CORS**: Whitelist-based origin validation via `CORS_ORIGINS`.
- **Data Isolation**: Strict recruiter isolation ensuring recruiters cannot view or modify requisitions or candidates belonging to other recruiters.
- **File Validation**: Strict magic byte verification (`%PDF-`), file size limits, extension validation, and sanitization preventing directory traversal attacks.
