"""Intelligent Skill-Gap Analysis & Learning Recommendations Engine (Phase 7).

Features:
1. Deterministic normalization and comprehensive synonyms taxonomy.
2. Skill Categorization:
   - Matched Skills: Skills the candidate possesses that satisfy requirements.
   - Missing Skills: Required skills absent from the candidate profile/resume.
   - Partial Skills: Related/precursor skills that bridge into a missing requirement.
   - Additional Skills: Value-added skills the candidate has beyond the job requirements.
   - Skills to Improve: Prioritized missing and partial skills.
3. Skill Coverage Calculation:
   - Coverage % = (len(matched_skills) / len(required_skills)) * 100.
   - Strictly separate and distinct from Phase 5 screening score and Phase 6 semantic score.
4. Intelligent Learning Recommendations:
   - Practical, actionable objectives and study roadmaps.
   - Priority tiers: HIGH, MEDIUM, LOW.
   - Difficulty tiers: BEGINNER, INTERMEDIATE, ADVANCED.
   - Reputable, free, official documentation links.
   - Zero paid LLM API calls.
5. Responsible AI Guardrails:
   - Strictly advisory recommendations.
   - No automatic candidate disqualification or rejection.
"""

import re
from typing import Any, Dict, List, Optional, Set, Tuple


# ============================================================================
# 1. CANONICAL SYNONYM TAXONOMY & NORMALIZATION
# ============================================================================

SYNONYM_MAP: Dict[str, str] = {
    # Programming Languages
    "js": "javascript",
    "javascript": "javascript",
    "es6": "javascript",
    "ecmascript": "javascript",
    "ts": "typescript",
    "typescript": "typescript",
    "py": "python",
    "python": "python",
    "python3": "python",
    "java": "java",
    "openjdk": "java",
    "jdk": "java",
    "c#": "c#",
    "csharp": "c#",
    ".net": "c#",
    "dotnet": "c#",
    "asp.net": "c#",
    "golang": "go",
    "go": "go",
    "cpp": "c++",
    "c++": "c++",
    "c": "c",
    "ruby": "ruby",
    "php": "php",
    "rust": "rust",
    "kotlin": "kotlin",
    "swift": "swift",
    "dart": "dart",
    "scala": "scala",
    "r": "r",

    # Frontend Frameworks & Web
    "react": "react",
    "reactjs": "react",
    "react.js": "react",
    "react native": "react native",
    "next": "next.js",
    "nextjs": "next.js",
    "next.js": "next.js",
    "vue": "vue.js",
    "vuejs": "vue.js",
    "vue.js": "vue.js",
    "angular": "angular",
    "angularjs": "angular",
    "angular.js": "angular",
    "html": "html",
    "html5": "html",
    "css": "css",
    "css3": "css",
    "tailwind": "tailwind css",
    "tailwindcss": "tailwind css",
    "tailwind css": "tailwind css",
    "bootstrap": "bootstrap",
    "sass": "sass",
    "scss": "sass",
    "redux": "redux",
    "zustand": "zustand",

    # Backend Frameworks
    "node": "node.js",
    "nodejs": "node.js",
    "node.js": "node.js",
    "express": "express.js",
    "expressjs": "express.js",
    "express.js": "express.js",
    "fastapi": "fastapi",
    "fast-api": "fastapi",
    "flask": "flask",
    "django": "django",
    "spring": "spring boot",
    "spring boot": "spring boot",
    "springboot": "spring boot",
    "nest": "nest.js",
    "nestjs": "nest.js",
    "nest.js": "nest.js",
    "graphql": "graphql",
    "graph-ql": "graphql",
    "rest": "rest api",
    "restful": "rest api",
    "rest api": "rest api",
    "restful api": "rest api",
    "grpc": "grpc",
    "microservices": "microservices",

    # Databases & Storage
    "postgres": "postgresql",
    "postgresql": "postgresql",
    "psql": "postgresql",
    "mysql": "mysql",
    "sqlite": "sqlite",
    "sql": "sql",
    "structured query language": "sql",
    "mongo": "mongodb",
    "mongodb": "mongodb",
    "redis": "redis",
    "elasticsearch": "elasticsearch",
    "cassandra": "cassandra",
    "dynamodb": "dynamodb",
    "qdrant": "qdrant",
    "vector database": "vector database",

    # Cloud, Containers & DevOps
    "docker": "docker",
    "container": "docker",
    "containers": "docker",
    "containerization": "docker",
    "docker-compose": "docker",
    "k8s": "kubernetes",
    "kubernetes": "kubernetes",
    "aws": "aws",
    "amazon web services": "aws",
    "gcp": "gcp",
    "google cloud": "gcp",
    "google cloud platform": "gcp",
    "azure": "azure",
    "microsoft azure": "azure",
    "ci/cd": "ci/cd",
    "cicd": "ci/cd",
    "continuous integration": "ci/cd",
    "github actions": "github actions",
    "jenkins": "jenkins",
    "terraform": "terraform",
    "ansible": "ansible",
    "linux": "linux",
    "bash": "linux",
    "git": "git",
    "github": "git",
    "gitlab": "git",
    "kafka": "kafka",
    "apache kafka": "kafka",
    "rabbitmq": "rabbitmq",

    # Data Science, ML & AI
    "ml": "machine learning",
    "machine learning": "machine learning",
    "ai": "artificial intelligence",
    "artificial intelligence": "artificial intelligence",
    "deep learning": "deep learning",
    "nlp": "natural language processing",
    "natural language processing": "natural language processing",
    "pandas": "pandas",
    "numpy": "numpy",
    "scikit-learn": "scikit-learn",
    "sklearn": "scikit-learn",
    "tensorflow": "tensorflow",
    "tf": "tensorflow",
    "pytorch": "pytorch",
    "torch": "pytorch",
    "spark": "apache spark",
    "apache spark": "apache spark",
    "computer vision": "computer vision",

    # Testing & Methodologies
    "unit testing": "unit testing",
    "testing": "unit testing",
    "pytest": "pytest",
    "jest": "jest",
    "agile": "agile",
    "scrum": "agile",
    "kanban": "agile",

    # Soft Skills
    "communication": "communication",
    "verbal communication": "communication",
    "written communication": "communication",
    "presentation": "communication",
    "teamwork": "teamwork",
    "collaboration": "teamwork",
    "problem solving": "problem solving",
    "analytical skills": "problem solving",
    "critical thinking": "problem solving",
    "leadership": "leadership",
    "mentorship": "leadership",
    "time management": "time management",
    "adaptability": "adaptability",
    "creativity": "creativity",
}


def normalize_skill_name(skill: str) -> str:
    """Normalize skill name to canonical lowercase string using synonym taxonomy."""
    if not skill or not skill.strip():
        return ""
    # Strip whitespace, lowercase
    s = skill.strip().lower()
    # Normalize punctuation while preserving +, #, and dots where meaningful
    s = re.sub(r"[\t\r\n]", " ", s)
    s = re.sub(r"\s+", " ", s).strip()

    # Direct synonym match
    if s in SYNONYM_MAP:
        return SYNONYM_MAP[s]

    # Strip surrounding quotes or parentheses
    clean = re.sub(r"^[\"\'\(]+|[\"\'\)]+$", "", s).strip()
    if clean in SYNONYM_MAP:
        return SYNONYM_MAP[clean]

    # Special punctuation cases
    sub_clean = clean.replace("-", " ").replace("_", " ")
    if sub_clean in SYNONYM_MAP:
        return SYNONYM_MAP[sub_clean]

    return clean


# ============================================================================
# 2. RELATED SKILLS GRAPH (FOR PARTIAL MATCHING)
# ============================================================================

RELATED_SKILLS_GRAPH: Dict[str, List[str]] = {
    "kubernetes": ["docker", "linux", "aws", "gcp", "azure", "ci/cd"],
    "docker": ["linux", "ci/cd", "kubernetes"],
    "postgresql": ["sql", "mysql", "sqlite", "relational database"],
    "mysql": ["sql", "postgresql", "sqlite", "relational database"],
    "mongodb": ["nosql", "redis", "database"],
    "react": ["javascript", "typescript", "html", "css"],
    "next.js": ["react", "javascript", "typescript", "node.js"],
    "vue.js": ["javascript", "typescript", "html", "css"],
    "angular": ["typescript", "javascript", "html", "css"],
    "typescript": ["javascript"],
    "fastapi": ["python", "rest api", "pydantic"],
    "django": ["python", "rest api", "sql"],
    "flask": ["python", "rest api"],
    "spring boot": ["java", "rest api", "sql", "microservices"],
    "c#": ["java", "c++", ".net"],
    "go": ["c++", "c", "microservices", "docker"],
    "rust": ["c++", "c", "systems programming"],
    "aws": ["gcp", "azure", "docker", "linux", "cloud"],
    "gcp": ["aws", "azure", "docker", "linux", "cloud"],
    "azure": ["aws", "gcp", "docker", "linux", "cloud"],
    "ci/cd": ["git", "docker", "jenkins", "github actions"],
    "machine learning": ["python", "pandas", "numpy", "scikit-learn", "data science"],
    "deep learning": ["machine learning", "pytorch", "tensorflow", "python"],
    "natural language processing": ["machine learning", "python", "deep learning"],
    "kafka": ["rabbitmq", "microservices", "distributed systems"],
    "redis": ["postgresql", "mysql", "cache"],
    "graphql": ["rest api", "javascript", "typescript", "node.js"],
    "microservices": ["rest api", "docker", "kubernetes", "distributed systems"],
    "tailwind css": ["css", "html", "react"],
}


# ============================================================================
# 3. CURATED LEARNING OBJECTIVES & FREE DOCUMENTATION REPOSITORY
# ============================================================================

LEARNING_CATALOG: Dict[str, Dict[str, Any]] = {
    "docker": {
        "skill_name": "Docker",
        "category": "DevOps & Cloud",
        "difficulty": "intermediate",
        "estimated_hours": 15,
        "priority_default": "HIGH",
        "core_concepts": [
            "Dockerfile directives and multi-stage builds",
            "Container networking, bridge networks, and port forwarding",
            "Persistent volumes and bind mounts",
            "Docker Compose multi-service orchestration",
            "Image security and minimal base images (Alpine/Distroless)",
        ],
        "learning_objectives": [
            "Write efficient Dockerfiles leveraging build caching and multi-stage layers",
            "Configure multi-container environments with Docker Compose and healthchecks",
            "Manage container lifecycles, volumes, and network segmentation securely",
        ],
        "documentation_links": [
            {"title": "Docker Getting Started Guide", "url": "https://docs.docker.com/get-started/"},
            {"title": "Dockerfile Best Practices", "url": "https://docs.docker.com/develop/develop-images/dockerfile_best-practices/"},
            {"title": "Docker Compose Overview", "url": "https://docs.docker.com/compose/"},
        ],
        "practice_project": "Containerize a full-stack web application with frontend, backend, and PostgreSQL database using Docker Compose.",
    },
    "kubernetes": {
        "skill_name": "Kubernetes",
        "category": "DevOps & Cloud",
        "difficulty": "advanced",
        "estimated_hours": 30,
        "priority_default": "HIGH",
        "core_concepts": [
            "Pods, ReplicaSets, and Deployments",
            "Services (ClusterIP, NodePort, LoadBalancer) and Ingress controllers",
            "ConfigMaps, Secrets, and Environment injection",
            "PersistentVolumes (PV), Claims (PVC), and StorageClasses",
            "Horizontal Pod Autoscaler (HPA) and resource limits/requests",
        ],
        "learning_objectives": [
            "Deploy and scale microservices with zero-downtime rolling updates",
            "Configure declarative manifest YAMLs with proper resource quotas",
            "Debug failing pods using kubectl logs, describe, and port-forward",
        ],
        "documentation_links": [
            {"title": "Kubernetes Official Documentation", "url": "https://kubernetes.io/docs/home/"},
            {"title": "Kubernetes Basics Interactive Tutorial", "url": "https://kubernetes.io/docs/tutorials/kubernetes-basics/"},
        ],
        "practice_project": "Deploy a stateless REST API with 3 replicas, Ingress routing, and automatic HPA scaling on local Minikube or Kind.",
    },
    "aws": {
        "skill_name": "AWS (Amazon Web Services)",
        "category": "DevOps & Cloud",
        "difficulty": "intermediate",
        "estimated_hours": 25,
        "priority_default": "HIGH",
        "core_concepts": [
            "Core Compute: EC2, ECS, and AWS Lambda",
            "Storage & DB: S3 bucket policies, RDS PostgreSQL, and DynamoDB",
            "Networking: VPC, Subnets, Internet Gateways, and Security Groups",
            "IAM: Roles, Policies, Principle of Least Privilege, and STS",
            "Monitoring: CloudWatch metrics, alarms, and CloudTrail audit logs",
        ],
        "learning_objectives": [
            "Architect secure 3-tier VPC setups with private and public subnets",
            "Deploy containerized applications to ECS Fargate or Lambda",
            "Manage access safely with IAM roles rather than permanent credentials",
        ],
        "documentation_links": [
            {"title": "AWS Cloud Essentials Documentation", "url": "https://docs.aws.amazon.com/"},
            {"title": "AWS Free Tier Hands-on Tutorials", "url": "https://aws.amazon.com/getting-started/hands-on/"},
        ],
        "practice_project": "Host an API with ECS Fargate backed by RDS PostgreSQL inside a custom VPC with S3 asset storage.",
    },
    "gcp": {
        "skill_name": "Google Cloud Platform (GCP)",
        "category": "DevOps & Cloud",
        "difficulty": "intermediate",
        "estimated_hours": 20,
        "priority_default": "MEDIUM",
        "core_concepts": [
            "Cloud Run serverless containers",
            "Google Kubernetes Engine (GKE) Autopilot",
            "Cloud Storage and Cloud SQL",
            "IAM service accounts and Workload Identity",
            "Cloud Monitoring and Cloud Logging",
        ],
        "learning_objectives": [
            "Deploy stateless containerized microservices to Cloud Run",
            "Configure Cloud SQL instances with private IP VPC peering",
            "Set up Workload Identity Federation for secure GitHub Actions deployment",
        ],
        "documentation_links": [
            {"title": "Google Cloud Documentation", "url": "https://cloud.google.com/docs"},
            {"title": "Cloud Run Quickstart", "url": "https://cloud.google.com/run/docs/quickstarts"},
        ],
        "practice_project": "Build and deploy an automated CI/CD pipeline shipping a FastAPI container to Google Cloud Run.",
    },
    "ci/cd": {
        "skill_name": "CI/CD (Continuous Integration & Delivery)",
        "category": "DevOps & Cloud",
        "difficulty": "intermediate",
        "estimated_hours": 15,
        "priority_default": "MEDIUM",
        "core_concepts": [
            "Automated build and test workflows on pull requests",
            "GitHub Actions runners, matrix builds, and caching",
            "Semantic release versioning and artifact publishing",
            "Branch protection rules and mandatory status checks",
            "Automated deployment to staging and production environments",
        ],
        "learning_objectives": [
            "Construct robust GitHub Actions workflows with test and lint stages",
            "Safely inject deployment secrets via encrypted environment secrets",
            "Implement multi-environment promotion gates with manual approvals",
        ],
        "documentation_links": [
            {"title": "GitHub Actions Documentation", "url": "https://docs.github.com/en/actions"},
            {"title": "CI/CD Best Practices", "url": "https://martinfowler.com/articles/continuousIntegration.html"},
        ],
        "practice_project": "Create a GitHub Actions pipeline running lint, unit tests, coverage reports, and automated container build.",
    },
    "python": {
        "skill_name": "Python",
        "category": "Backend",
        "difficulty": "beginner",
        "estimated_hours": 20,
        "priority_default": "HIGH",
        "core_concepts": [
            "Data structures, list/dict comprehensions, and generators",
            "Object-oriented programming, classes, and inheritance",
            "Type hints and static checking with mypy",
            "Asynchronous programming with asyncio, async, and await",
            "Virtual environments, poetry/uv packaging, and dependency management",
        ],
        "learning_objectives": [
            "Write idiomatic, PEP 8 compliant code with explicit type annotations",
            "Build concurrent I/O applications using modern Python asyncio",
            "Structure modular packages with unit test suites using pytest",
        ],
        "documentation_links": [
            {"title": "Python Official Tutorial", "url": "https://docs.python.org/3/tutorial/"},
            {"title": "Real Python Tutorials", "url": "https://realpython.com/"},
        ],
        "practice_project": "Build an asynchronous CLI data scraper and parser with comprehensive type hints and pytest coverage.",
    },
    "fastapi": {
        "skill_name": "FastAPI",
        "category": "Backend",
        "difficulty": "intermediate",
        "estimated_hours": 15,
        "priority_default": "HIGH",
        "core_concepts": [
            "Pydantic v2 schemas for request validation and response models",
            "FastAPI Dependency Injection (`Depends`) system",
            "OAuth2 and JWT token authentication flows",
            "SQLAlchemy / SQLModel async database sessions",
            "Interactive OpenAPI Swagger documentation and automated tests",
        ],
        "learning_objectives": [
            "Design RESTful APIs following OpenAPI specifications",
            "Implement role-based authorization using reusable dependencies",
            "Write integration tests using Starlette/HTTPX TestClient",
        ],
        "documentation_links": [
            {"title": "FastAPI Official Documentation", "url": "https://fastapi.tiangolo.com/"},
            {"title": "FastAPI Tutorial - User Guide", "url": "https://fastapi.tiangolo.com/tutorial/"},
        ],
        "practice_project": "Build a secure REST API with JWT authentication, role-based access control, and SQLite/PostgreSQL persistence.",
    },
    "typescript": {
        "skill_name": "TypeScript",
        "category": "Frontend",
        "difficulty": "intermediate",
        "estimated_hours": 20,
        "priority_default": "HIGH",
        "core_concepts": [
            "Static types, interfaces, type aliases, and unions",
            "Generics, utility types (Pick, Omit, Partial, Record), and keyof",
            "Strict null checking, type guards, and type narrowing",
            "Module resolution, tsconfig compiler options, and ESM",
            "Typing React components, hooks, and asynchronous API calls",
        ],
        "learning_objectives": [
            "Eliminate `any` types by creating expressive domain models",
            "Leverage advanced utility types and discriminating unions",
            "Ensure end-to-end type safety between backend schemas and frontend views",
        ],
        "documentation_links": [
            {"title": "TypeScript Official Handbook", "url": "https://www.typescriptlang.org/docs/handbook/intro.html"},
            {"title": "TypeScript for JavaScript Programmers", "url": "https://www.typescriptlang.org/docs/handbook/typescript-in-5-minutes.html"},
        ],
        "practice_project": "Refactor a vanilla JavaScript React project into strict TypeScript with zero compilation warnings.",
    },
    "react": {
        "skill_name": "React",
        "category": "Frontend",
        "difficulty": "intermediate",
        "estimated_hours": 25,
        "priority_default": "HIGH",
        "core_concepts": [
            "Component lifecycle, JSX rendering, and reconciliation",
            "Hooks: useState, useEffect, useMemo, useCallback, and useRef",
            "State management patterns and Context API",
            "Forms, controlled inputs, and validation libraries",
            "Performance optimization (memoization, virtualization, code splitting)",
        ],
        "learning_objectives": [
            "Build reusable, accessible component hierarchies",
            "Manage complex application state without unnecessary re-renders",
            "Write custom hooks to decouple data fetching and business logic",
        ],
        "documentation_links": [
            {"title": "React Official Documentation", "url": "https://react.dev/"},
            {"title": "Thinking in React Tutorial", "url": "https://react.dev/learn/thinking-in-react"},
        ],
        "practice_project": "Build a dynamic task and workflow tracker with custom hooks, filters, local storage sync, and animations.",
    },
    "next.js": {
        "skill_name": "Next.js",
        "category": "Frontend",
        "difficulty": "intermediate",
        "estimated_hours": 25,
        "priority_default": "HIGH",
        "core_concepts": [
            "App Router architecture, layouts, templates, and route handlers",
            "Server Components (RSC) vs Client Components ('use client')",
            "Server Actions for mutations and form handling",
            "Static Site Generation (SSG), SSR, and Incremental Static Regeneration (ISR)",
            "Metadata API, SEO optimization, and Image optimization",
        ],
        "learning_objectives": [
            "Architect performant full-stack applications with Next.js App Router",
            "Optimize data loading boundaries with React Suspense and streaming",
            "Deploy production Next.js apps with proper environment configurations",
        ],
        "documentation_links": [
            {"title": "Next.js Official Documentation", "url": "https://nextjs.org/docs"},
            {"title": "Next.js App Router Learn Course", "url": "https://nextjs.org/learn"},
        ],
        "practice_project": "Build a blog or recruitment dashboard with Next.js App Router, Server Actions, and Tailwind CSS.",
    },
    "spring boot": {
        "skill_name": "Spring Boot",
        "category": "Backend",
        "difficulty": "intermediate",
        "estimated_hours": 30,
        "priority_default": "HIGH",
        "core_concepts": [
            "Dependency Injection and Inversion of Control (IoC) container",
            "Spring Data JPA, Hibernate ORM, and Entity relationships",
            "Spring Security 6, JWT authentication, and Method Security",
            "REST Controllers, DTOs, and global exception handlers",
            "Spring Boot Actuator, Micrometer, and integration testing with @SpringBootTest",
        ],
        "learning_objectives": [
            "Create production-ready microservices with Spring Boot 3 and Java 17+",
            "Implement declarative security rules and token-based authentication",
            "Write robust repository queries with Spring Data and transactions",
        ],
        "documentation_links": [
            {"title": "Spring Boot Reference Documentation", "url": "https://docs.spring.io/spring-boot/docs/current/reference/html/"},
            {"title": "Spring Quickstart Guides", "url": "https://spring.io/quickstart"},
        ],
        "practice_project": "Build a secure RESTful e-commerce or recruitment service with Spring Boot, Spring Security, and PostgreSQL.",
    },
    "postgresql": {
        "skill_name": "PostgreSQL",
        "category": "Database",
        "difficulty": "intermediate",
        "estimated_hours": 20,
        "priority_default": "HIGH",
        "core_concepts": [
            "ACID transactions, isolation levels, and row locking",
            "Complex queries: JOINs, CTEs, Window functions, and JSONB indexing",
            "B-tree, GiST, GIN indexes, and EXPLAIN ANALYZE query plans",
            "Schema migrations, foreign keys, and constraint cascades",
            "Connection pooling (PgBouncer/Neon Pooler) and backup strategies",
        ],
        "learning_objectives": [
            "Optimize slow queries by inspecting EXPLAIN ANALYZE execution plans",
            "Model normalized schemas with rigorous data integrity constraints",
            "Leverage PostgreSQL advanced features like JSONB and full-text search",
        ],
        "documentation_links": [
            {"title": "PostgreSQL Official Documentation", "url": "https://www.postgresql.org/docs/"},
            {"title": "PostgreSQL Tutorial", "url": "https://www.postgresqltutorial.com/"},
        ],
        "practice_project": "Design a relational schema with complex analytical queries, CTEs, and GIN-indexed JSON columns.",
    },
    "mongodb": {
        "skill_name": "MongoDB",
        "category": "Database",
        "difficulty": "intermediate",
        "estimated_hours": 15,
        "priority_default": "MEDIUM",
        "core_concepts": [
            "Document data modeling: embedding vs referencing",
            "MongoDB Aggregation Framework pipelines ($match, $group, $lookup)",
            "Compound indexes, TTL indexes, and performance tuning",
            "Replica sets, write concerns, and read preferences",
        ],
        "learning_objectives": [
            "Design flexible document schemas tailored to high-read access patterns",
            "Construct multi-stage aggregation pipelines for reporting",
        ],
        "documentation_links": [
            {"title": "MongoDB Manual", "url": "https://www.mongodb.com/docs/manual/"},
            {"title": "MongoDB University Free Courses", "url": "https://learn.mongodb.com/"},
        ],
        "practice_project": "Build an analytical logging system with multi-stage aggregation pipelines in MongoDB.",
    },
    "redis": {
        "skill_name": "Redis",
        "category": "Database",
        "difficulty": "intermediate",
        "estimated_hours": 12,
        "priority_default": "MEDIUM",
        "core_concepts": [
            "Data structures: Strings, Hashes, Lists, Sets, and Sorted Sets",
            "Caching strategies: Cache-Aside, Write-Through, and TTL expiration",
            "Pub/Sub messaging and Redis Streams",
            "Distributed locks and rate limiting algorithms",
        ],
        "learning_objectives": [
            "Implement sub-millisecond caching layers with proper eviction policies",
            "Build real-time rate limiters and session stores using Redis",
        ],
        "documentation_links": [
            {"title": "Redis Documentation", "url": "https://redis.io/docs/"},
            {"title": "Redis University", "url": "https://university.redis.io/"},
        ],
        "practice_project": "Implement an API rate-limiting middleware and session cache backed by Redis.",
    },
    "kafka": {
        "skill_name": "Apache Kafka",
        "category": "Backend",
        "difficulty": "advanced",
        "estimated_hours": 25,
        "priority_default": "HIGH",
        "core_concepts": [
            "Event-driven architecture, Topics, Partitions, and Offsets",
            "Producers: acks, idempotence, and partitioner strategies",
            "Consumer groups, rebalancing, and committed offsets",
            "Schema Registry, Avro serialization, and event contracts",
        ],
        "learning_objectives": [
            "Build decoupled event-driven systems with guaranteed delivery semantics",
            "Handle consumer lag, backpressure, and dead-letter queues",
        ],
        "documentation_links": [
            {"title": "Apache Kafka Documentation", "url": "https://kafka.apache.org/documentation/"},
            {"title": "Confluent Kafka Tutorials", "url": "https://developer.confluent.io/tutorials/"},
        ],
        "practice_project": "Implement an asynchronous event-driven notifications pipeline with Kafka producers and consumers.",
    },
    "microservices": {
        "skill_name": "Microservices Architecture",
        "category": "Software Engineering",
        "difficulty": "advanced",
        "estimated_hours": 25,
        "priority_default": "HIGH",
        "core_concepts": [
            "Domain-Driven Design (DDD) and Bounded Contexts",
            "API Gateway pattern, service discovery, and circuit breakers",
            "Saga pattern for distributed transactions and eventual consistency",
            "Distributed tracing with OpenTelemetry and correlation IDs",
        ],
        "learning_objectives": [
            "Decompose monolithic applications into independent, resilient services",
            "Manage distributed data consistency and observability across service boundaries",
        ],
        "documentation_links": [
            {"title": "Microservices.io Architecture Patterns", "url": "https://microservices.io/"},
            {"title": "Martin Fowler Microservices Guide", "url": "https://martinfowler.com/articles/microservices.html"},
        ],
        "practice_project": "Design a 2-service order/inventory system communicating asynchronously via messaging with a central API Gateway.",
    },
    "machine learning": {
        "skill_name": "Machine Learning",
        "category": "Data & AI",
        "difficulty": "intermediate",
        "estimated_hours": 35,
        "priority_default": "HIGH",
        "core_concepts": [
            "Supervised vs Unsupervised learning algorithms",
            "Feature engineering, normalization, and train/test cross-validation",
            "Evaluation metrics: Precision, Recall, F1-Score, ROC-AUC, and Confusion Matrix",
            "Scikit-learn pipelines and model serialization (pickle/ONNX)",
            "Dense vector embeddings and semantic similarity metrics (Cosine, Dot)",
        ],
        "learning_objectives": [
            "Train, evaluate, and benchmark regression and classification models",
            "Prevent overfitting with regularization, cross-validation, and feature pruning",
            "Deploy inference pipelines with ONNX or lightweight serving engines",
        ],
        "documentation_links": [
            {"title": "Scikit-Learn User Guide", "url": "https://scikit-learn.org/stable/user_guide.html"},
            {"title": "Google Machine Learning Crash Course", "url": "https://developers.google.com/machine-learning/crash-course"},
        ],
        "practice_project": "Build an end-to-end classification pipeline predicting customer churn or candidate-job match score.",
    },
    "communication": {
        "skill_name": "Effective Communication",
        "category": "Soft Skills",
        "difficulty": "beginner",
        "estimated_hours": 10,
        "priority_default": "LOW",
        "core_concepts": [
            "Technical writing: RFCs, architectural decision records (ADRs), and documentation",
            "Structuring concise asynchronous updates for distributed engineering teams",
            "Active listening and constructive code review feedback",
        ],
        "learning_objectives": [
            "Document engineering decisions clearly for technical and non-technical stakeholders",
            "Deliver empathetic, actionable code review comments that elevate team standards",
        ],
        "documentation_links": [
            {"title": "Google Technical Writing Courses", "url": "https://developers.google.com/tech-writing"},
        ],
        "practice_project": "Author a comprehensive Architectural Decision Record (ADR) justifying a technology choice for an existing system.",
    },
    "problem solving": {
        "skill_name": "Problem Solving & Analytical Thinking",
        "category": "Soft Skills",
        "difficulty": "intermediate",
        "estimated_hours": 15,
        "priority_default": "LOW",
        "core_concepts": [
            "Root-cause analysis (5 Whys, Ishikawa diagrams)",
            "Algorithmic complexity (Big-O time and space analysis)",
            "System debugging methodologies and hypothesis-driven triage",
        ],
        "learning_objectives": [
            "Systematically diagnose complex distributed software regressions",
            "Formulate measurable test hypotheses before refactoring or fixing bugs",
        ],
        "documentation_links": [
            {"title": "MIT OpenCourseWare - Introduction to Algorithms", "url": "https://ocw.mit.edu/courses/6-006-introduction-to-algorithms-fall-2011/"},
        ],
        "practice_project": "Perform a complete post-mortem RCA report on a simulated production database outage.",
    },
}


def get_default_learning_plan_for_unknown_skill(skill_name: str) -> Dict[str, Any]:
    """Generate a high-quality fallback learning plan for niche or unindexed skills."""
    canonical = skill_name.strip()
    return {
        "skill_name": canonical.title(),
        "category": "Software Engineering",
        "difficulty": "intermediate",
        "estimated_hours": 15,
        "priority_default": "MEDIUM",
        "core_concepts": [
            f"Core fundamentals and architecture of {canonical}",
            f"Industry standard patterns and best practices for {canonical}",
            f"Integration and practical deployment of {canonical}",
        ],
        "learning_objectives": [
            f"Gain foundational fluency with {canonical} core concepts and CLI/APIs",
            f"Build a reference proof-of-concept demonstrating {canonical} in action",
        ],
        "documentation_links": [
            {
                "title": f"Official {canonical.title()} Documentation",
                "url": f"https://www.google.com/search?q={canonical}+official+documentation",
            }
        ],
        "practice_project": f"Create a working sample application integrating {canonical} with automated testing.",
    }


# ============================================================================
# 4. SKILL GAP ANALYSIS ENGINE
# ============================================================================

def parse_skill_list(skills_input: Any) -> List[str]:
    """Parse comma/newline separated string or list into individual skill tokens."""
    if not skills_input:
        return []
    if isinstance(skills_input, list):
        items = skills_input
    elif isinstance(skills_input, str):
        items = re.split(r"[,;\n•|]+", skills_input)
    else:
        items = [str(skills_input)]

    result = []
    for s in items:
        cleaned = s.strip()
        if cleaned and len(cleaned) >= 1:
            result.append(cleaned)
    return result


def analyze_skill_gap(
    candidate_skills: List[str],
    required_skills: Any,
    candidate_experience_years: Optional[str] = None,
    job_experience_years: Optional[str] = None,
    resume_text: Optional[str] = None,
    job_description: Optional[str] = None,
) -> Dict[str, Any]:
    """Perform comprehensive skill-gap analysis between candidate and job requisition.

    Returns:
    - coverage_percentage: float (0.0 to 100.0)
    - matched_skills: List[str]
    - missing_skills: List[str]
    - partial_skills: List[Dict[str, str]] (required skill + candidate related skill)
    - additional_skills: List[str] (candidate strengths not required by job)
    - skills_to_improve: List[str] (missing + partial skills to develop)
    - learning_recommendations: List[Dict[str, Any]] (structured study plans)
    - strengths_summary: str
    - growth_summary: str
    - advisory_note: str
    """
    raw_required = parse_skill_list(required_skills)
    cand_parsed = parse_skill_list(candidate_skills)

    # Normalize candidate skills
    candidate_norm_map: Dict[str, str] = {}
    for cs in cand_parsed:
        norm = normalize_skill_name(cs)
        if norm:
            candidate_norm_map[norm] = cs

    resume_text_lower = resume_text.lower() if resume_text else ""

    matched_skills: List[str] = []
    missing_skills: List[str] = []
    partial_skills: List[Dict[str, str]] = []

    matched_canonical_set: Set[str] = set()

    for req in raw_required:
        norm_req = normalize_skill_name(req)
        if not norm_req:
            continue

        # 1. Direct or synonym match with candidate skills
        if norm_req in candidate_norm_map:
            matched_skills.append(req)
            matched_canonical_set.add(norm_req)
            continue

        # 2. Text boundary match in candidate resume text
        if resume_text_lower and re.search(r"\b" + re.escape(norm_req) + r"\b", resume_text_lower):
            matched_skills.append(req)
            matched_canonical_set.add(norm_req)
            continue

        # 3. Check for partial / precursor relationship
        related = RELATED_SKILLS_GRAPH.get(norm_req, [])
        found_partial = False
        for rel in related:
            norm_rel = normalize_skill_name(rel)
            if norm_rel in candidate_norm_map:
                partial_skills.append({
                    "required_skill": req,
                    "candidate_related_skill": candidate_norm_map[norm_rel],
                    "relationship": f"Candidate possesses '{candidate_norm_map[norm_rel]}', which provides a foundation for '{req}'.",
                })
                found_partial = True
                break

        # If not matched, it is missing
        missing_skills.append(req)

    # Additional skills: candidate skills that were not requested by the job
    additional_skills: List[str] = []
    required_canonical_set = {normalize_skill_name(r) for r in raw_required if normalize_skill_name(r)}

    for norm_c, original_c in candidate_norm_map.items():
        if norm_c not in required_canonical_set:
            additional_skills.append(original_c)

    # Calculate skill coverage percentage
    # If no required skills were specified on the requisition, coverage is 100%
    if raw_required:
        coverage_percentage = round((len(matched_skills) / len(raw_required)) * 100.0, 1)
        coverage_percentage = min(100.0, max(0.0, coverage_percentage))
    else:
        coverage_percentage = 100.0

    # Skills to improve (unique missing skills)
    skills_to_improve = list(dict.fromkeys(missing_skills))

    # Generate Learning Recommendations
    learning_recommendations: List[Dict[str, Any]] = []
    for skill_name in skills_to_improve:
        norm_s = normalize_skill_name(skill_name)
        catalog_entry = LEARNING_CATALOG.get(norm_s)
        if catalog_entry:
            rec = dict(catalog_entry)
            rec["required_skill"] = skill_name
            # Check if partial match exists
            is_partial = any(p["required_skill"].lower() == skill_name.lower() for p in partial_skills)
            if is_partial:
                rec["priority"] = "MEDIUM"
                rec["note"] = f"Candidate already has related foundational background. Accelerated ramp-up recommended."
            else:
                rec["priority"] = rec.get("priority_default", "HIGH")
                rec["note"] = f"Core requirement gap. Prioritize early in professional development."
            learning_recommendations.append(rec)
        else:
            fallback = get_default_learning_plan_for_unknown_skill(skill_name)
            fallback["required_skill"] = skill_name
            fallback["priority"] = "MEDIUM"
            fallback["note"] = "General industry learning path for specified skill requirement."
            learning_recommendations.append(fallback)

    # Sort recommendations by Priority: HIGH first, then MEDIUM, then LOW
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    learning_recommendations.sort(key=lambda r: priority_order.get(r.get("priority", "MEDIUM"), 3))

    # Generate narrative summaries
    if coverage_percentage >= 80.0:
        match_tier = "High Skill Alignment"
    elif coverage_percentage >= 50.0:
        match_tier = "Moderate Skill Alignment"
    else:
        match_tier = "Emerging Skill Alignment"

    strengths_text = (
        f"Candidate satisfies {len(matched_skills)} of {len(raw_required)} key job requirement(s) ({coverage_percentage}% coverage)."
    )
    if additional_skills:
        strengths_text += f" Bonus capabilities include: {', '.join(additional_skills[:4])}."

    if missing_skills:
        growth_text = (
            f"Key growth opportunities identified in {len(missing_skills)} area(s): {', '.join(missing_skills[:3])}."
        )
    else:
        growth_text = "All listed technical requirements are satisfied by the candidate's profile."

    return {
        "coverage_percentage": coverage_percentage,
        "match_tier": match_tier,
        "total_required_count": len(raw_required),
        "matched_count": len(matched_skills),
        "missing_count": len(missing_skills),
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "partial_skills": partial_skills,
        "additional_skills": additional_skills,
        "skills_to_improve": skills_to_improve,
        "learning_recommendations": learning_recommendations,
        "strengths_summary": strengths_text,
        "growth_summary": growth_text,
        "advisory_note": (
            "Responsible AI Notice: Skill-gap analysis and learning recommendations are advisory only. "
            "They support recruiter evaluations and candidate professional development. "
            "Candidates are never automatically disqualified based on skill gap calculations."
        ),
    }
