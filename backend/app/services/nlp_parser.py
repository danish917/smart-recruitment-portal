"""NLP Resume Parsing Engine and PDF Text Extraction Service.

Features:
- Secure in-memory PDF text extraction via pypdf.
- Robust handling of corrupted, empty, and scanned image PDFs (flagging OCR_REQUIRED).
- Rule-based & heuristic NLP structuring for skills, education, experience, projects, and credentials.
- Strict adherence to responsible AI: No hallucinations, and no parsing of protected characteristics.
"""

import io
import re
from typing import Any, Dict, List, Optional, Tuple
import pypdf
from pypdf.errors import PdfStreamError
from app.models.screening import ParsingStatus

# Curated Technical Skills Taxonomy (case-normalized patterns)
TECHNICAL_SKILLS_TAXONOMY = [
    # Languages
    "Python", "JavaScript", "TypeScript", "Java", "C++", "C#", "C", "Go", "Golang",
    "Rust", "Ruby", "PHP", "Kotlin", "Swift", "Scala", "R", "Dart", "Shell", "Bash",
    "SQL", "HTML", "HTML5", "CSS", "CSS3", "Sass", "GraphQL", "Perl",
    # Backend & Web Frameworks
    "FastAPI", "Django", "Flask", "React", "Next.js", "Vue", "Vue.js", "Angular",
    "Node.js", "Express", "Express.js", "Spring", "Spring Boot", "ASP.NET", ".NET",
    "Ruby on Rails", "Laravel", "NestJS", "Fastify", "Tailwind CSS", "Bootstrap",
    # Databases & Caching
    "PostgreSQL", "Postgres", "MySQL", "MongoDB", "Redis", "SQLite", "Oracle",
    "Cassandra", "Elasticsearch", "DynamoDB", "MariaDB", "CouchDB", "Neo4j", "Firebase",
    "Supabase", "Prisma", "SQLAlchemy", "TypeORM", "Alembic",
    # Cloud, DevOps & Infrastructure
    "AWS", "Amazon Web Services", "Azure", "GCP", "Google Cloud", "Docker",
    "Kubernetes", "K8s", "Terraform", "Ansible", "Jenkins", "Git", "GitHub", "GitLab",
    "CI/CD", "Linux", "Unix", "Nginx", "Apache", "Kafka", "RabbitMQ", "Celery",
    "Microservices", "REST API", "RESTful", "gRPC", "Serverless", "Prometheus", "Grafana",
    # AI, ML & Data
    "Machine Learning", "Deep Learning", "NLP", "Computer Vision", "PyTorch",
    "TensorFlow", "Scikit-Learn", "Keras", "Pandas", "NumPy", "SciPy", "Spark",
    "Hadoop", "Airflow", "Data Mining", "BigQuery", "Snowflake", "Databricks",
    # Architecture & Practices
    "OOP", "Design Patterns", "Agile", "Scrum", "TDD", "System Design", "Microservices Architecture",
]

# Curated Soft Skills Taxonomy
SOFT_SKILLS_TAXONOMY = [
    "Leadership", "Communication", "Problem Solving", "Teamwork", "Collaboration",
    "Critical Thinking", "Adaptability", "Time Management", "Project Management",
    "Mentoring", "Analytical Thinking", "Negotiation", "Creativity", "Attention to Detail",
    "Conflict Resolution", "Decision Making", "Work Ethic",
]

# Common Degrees
DEGREE_PATTERNS = [
    (r"\b(Ph\.?D\.?|Doctor of Philosophy|Doctorate)\b", "Doctorate (Ph.D.)"),
    (r"\b(M\.?S\.?|M\.?Sc\.?|Master of Science)\b", "Master of Science (M.S.)"),
    (r"\b(M\.?Tech\.?|Master of Technology)\b", "Master of Technology (M.Tech)"),
    (r"\b(M\.?B\.?A\.?|Master of Business Administration)\b", "MBA"),
    (r"\b(B\.?S\.?|B\.?Sc\.?|Bachelor of Science)\b", "Bachelor of Science (B.S.)"),
    (r"\b(B\.?E\.?|B\.?Tech\.?|Bachelor of Technology|Bachelor of Engineering)\b", "Bachelor of Technology / Engineering (B.Tech/B.E.)"),
    (r"\b(Bachelor of Arts|B\.?A\.?)\b", "Bachelor of Arts (B.A.)"),
    (r"\b(Associate Degree|Associate of Science|Associate of Arts)\b", "Associate Degree"),
    (r"\b(Diploma in [A-Za-z ]+)\b", "Diploma"),
]

# Known University keywords
UNIVERSITY_PATTERNS = [
    r"([A-Z][a-zA-Z\s]+(?:University|College|Institute of Technology|Polytechnic|Academy))",
    r"((?:University|College|Institute) of [A-Z][a-zA-Z\s]+)",
]

# Common Certifications
CERTIFICATION_PATTERNS = [
    "AWS Certified Solutions Architect", "AWS Certified Developer", "AWS Certified",
    "Certified Kubernetes Administrator", "CKA", "CKAD",
    "Google Cloud Certified", "GCP Professional", "Azure Fundamentals", "Azure Solutions Architect",
    "PMP", "Project Management Professional", "Certified Scrum Master", "CSM",
    "CompTIA Security+", "CISSP", "Cisco CCNA", "Cisco CCNP", "HashiCorp Certified Terraform",
]


def extract_text_from_pdf(content: bytes) -> Tuple[str, ParsingStatus, Optional[str]]:
    """Extract plain text from PDF bytes.

    Handles empty, corrupted, and image-scanned PDFs gracefully.
    """
    if not content or len(content) < 10:
        return "", ParsingStatus.FAILED, "PDF file is empty or missing data."

    try:
        reader = pypdf.PdfReader(io.BytesIO(content))
        if len(reader.pages) == 0:
            return "", ParsingStatus.FAILED, "PDF contains no pages."

        extracted_text_parts = []
        for i, page in enumerate(reader.pages):
            try:
                page_text = page.extract_text() or ""
                if page_text.strip():
                    extracted_text_parts.append(page_text.strip())
            except Exception as page_err:
                # Continue reading remaining pages
                continue

        full_text = "\n\n".join(extracted_text_parts).strip()

        # Check for scanned PDF / image-only documents
        if len(full_text) < 30:
            return (
                full_text,
                ParsingStatus.OCR_REQUIRED,
                "Scanned or image-based document detected without an extractable text layer. Optical Character Recognition (OCR) recommended.",
            )

        return full_text, ParsingStatus.PARSED, None

    except (PdfStreamError, Exception) as err:
        return "", ParsingStatus.FAILED, f"Failed to parse PDF document: {str(err)}"


def extract_candidate_name(text: str) -> Optional[str]:
    """Extract candidate name from first few lines using clean entity heuristics."""
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    for line in lines[:5]:
        # Ignore lines with email, phone, web links, or resume headings
        if "@" in line or "http" in line or any(c.isdigit() for c in line):
            continue
        if re.search(r"\b(resume|curriculum|vitae|profile|summary|page)\b", line, re.I):
            continue

        words = line.split()
        # Typical name consists of 2-4 capitalized words
        if 2 <= len(words) <= 4 and all(w[0].isupper() for w in words if w.isalpha()):
            return " ".join(words)
    return None


def extract_email(text: str) -> Optional[str]:
    """Extract email address using regex."""
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", text)
    return match.group(0).lower() if match else None


def extract_phone(text: str) -> Optional[str]:
    """Extract phone number."""
    match = re.search(
        r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}", text
    )
    return match.group(0).strip() if match else None


def extract_skills(text: str) -> Tuple[List[str], List[str]]:
    """Extract technical and soft skills using word boundary matching against taxonomy."""
    text_lower = f" {text.lower()} "

    technical_matches = set()
    for skill in TECHNICAL_SKILLS_TAXONOMY:
        # Match with word boundaries
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            technical_matches.add(skill)

    soft_matches = set()
    for skill in SOFT_SKILLS_TAXONOMY:
        pattern = r"\b" + re.escape(skill.lower()) + r"\b"
        if re.search(pattern, text_lower):
            soft_matches.add(skill)

    return sorted(list(technical_matches)), sorted(list(soft_matches))


def extract_education_details(text: str) -> Tuple[Optional[str], Optional[str], Optional[int]]:
    """Extract highest degree qualification, university name, and graduation year."""
    detected_degree = None
    for pattern, degree_label in DEGREE_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            detected_degree = degree_label
            break

    detected_university = None
    for pattern in UNIVERSITY_PATTERNS:
        match = re.search(pattern, text)
        if match:
            clean_uni = match.group(1).strip()
            # Discard false positives that are excessively long
            if len(clean_uni) <= 80:
                detected_university = clean_uni
                break

    # Look for 4-digit graduation year near education keywords or general years between 1980 and 2030
    grad_year = None
    year_match = re.search(r"\b(20[0-2]\d|19[8-9]\d)\b", text)
    if year_match:
        try:
            grad_year = int(year_match.group(1))
        except ValueError:
            pass

    return detected_degree, detected_university, grad_year


def extract_experience_info(text: str) -> Tuple[Optional[str], List[str]]:
    """Extract estimated years of experience and detected professional roles."""
    years_str = None
    exp_match = re.search(r"(\d{1,2})\+?\s*(?:years|yrs)\b(?:\s*of\s*experience)?", text, re.IGNORECASE)
    if exp_match:
        years_str = f"{exp_match.group(1)}+ years"

    # Detect common role titles
    detected_roles = set()
    common_roles = [
        "Software Engineer", "Backend Developer", "Frontend Developer", "Full Stack Developer",
        "Full Stack Engineer", "DevOps Engineer", "Cloud Architect", "Data Scientist",
        "Machine Learning Engineer", "Product Manager", "Tech Lead", "Engineering Manager",
        "QA Engineer", "Database Administrator", "Systems Architect",
    ]
    for role in common_roles:
        if re.search(r"\b" + re.escape(role) + r"\b", text, re.IGNORECASE):
            detected_roles.add(role)

    return years_str, sorted(list(detected_roles))


def extract_projects_and_certifications(text: str) -> Tuple[List[str], List[str]]:
    """Extract project highlights and industry certifications."""
    certs = []
    for cert in CERTIFICATION_PATTERNS:
        if re.search(r"\b" + re.escape(cert) + r"\b", text, re.IGNORECASE):
            certs.append(cert)

    # Simple project identifier from 'Projects' or 'Project Highlights' section
    projects = []
    project_section = re.search(r"(?:Projects|Personal Projects|Key Projects)[\s:\n]+(.*?)(?=\n\n[A-Z]|\Z)", text, re.DOTALL | re.IGNORECASE)
    if project_section:
        lines = [l.strip("-•* \t") for l in project_section.group(1).split("\n") if l.strip()]
        for line in lines[:5]:
            if 10 <= len(line) <= 120:
                projects.append(line)

    return projects, certs


def parse_resume_text(raw_text: str) -> Dict[str, Any]:
    """Convert raw resume text into structured candidate resume JSON."""
    if not raw_text or not raw_text.strip():
        return {
            "name": None,
            "email": None,
            "phone": None,
            "technical_skills": [],
            "soft_skills": [],
            "education": None,
            "college_university": None,
            "graduation_year": None,
            "experience_years": None,
            "work_experience": [],
            "projects": [],
            "certifications": [],
        }

    name = extract_candidate_name(raw_text)
    email = extract_email(raw_text)
    phone = extract_phone(raw_text)
    tech_skills, soft_skills = extract_skills(raw_text)
    degree, university, grad_year = extract_education_details(raw_text)
    exp_years, roles = extract_experience_info(raw_text)
    projects, certs = extract_projects_and_certifications(raw_text)

    return {
        "name": name,
        "email": email,
        "phone": phone,
        "technical_skills": tech_skills,
        "soft_skills": soft_skills,
        "education": degree,
        "college_university": university,
        "graduation_year": grad_year,
        "experience_years": exp_years,
        "work_experience": roles,
        "projects": projects,
        "certifications": certs,
    }
