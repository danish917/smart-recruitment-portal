"""Explainable AI Resume Screening Engine.

Evaluates candidate resume against job requisition criteria:
1. Skills Match (40%): Overlap between required skills and candidate technical/soft skills.
2. Education Match (20%): Highest degree vs. minimum qualification requirement.
3. Experience Match (20%): Candidate years/level vs. experience requirement.
4. Job Description Relevance (20%): Token/keyword alignment with role expectations.

Features:
- Transparent score breakdown with factor-by-factor explanations.
- Advisory recommendation tier: Strong Match (>=80), Good Match (>=60), Moderate Match (>=40), Limited Match (<40).
- Responsible AI Guardrails: Zero use of protected characteristics; strictly advisory (no auto-rejection).
"""

import re
from typing import Any, Dict, List, Set, Tuple


def normalize_skill(skill: str) -> str:
    """Normalize skill strings for robust case/punctuation matching."""
    s = skill.lower().strip()
    s = re.sub(r"[.\-_]", "", s)
    return s


def compute_skills_overlap(
    required_skills_raw: str,
    candidate_skills: List[str],
    resume_text: str,
) -> Tuple[List[str], List[str], float]:
    """Compare required skills from job vs candidate skills and raw text."""
    if not required_skills_raw:
        return [], [], 40.0

    # Parse required skills by comma, semicolon, or newline
    required_list = [
        s.strip()
        for s in re.split(r"[,;\n]", required_skills_raw)
        if s.strip()
    ]
    if not required_list:
        return [], [], 40.0

    normalized_candidate_skills = {normalize_skill(s) for s in candidate_skills}
    text_lower = resume_text.lower() if resume_text else ""

    matched = []
    missing = []

    for req in required_list:
        norm_req = normalize_skill(req)
        # Check direct normalized match or word boundary in resume text
        if norm_req in normalized_candidate_skills or re.search(
            r"\b" + re.escape(req.lower()) + r"\b", text_lower
        ):
            matched.append(req)
        else:
            missing.append(req)

    match_ratio = len(matched) / len(required_list)
    score = round(match_ratio * 40.0, 1)
    return matched, missing, score


def compute_education_match(
    required_qual: str,
    candidate_degree: str,
) -> Tuple[bool, float, str]:
    """Evaluate whether candidate's education meets minimum required qualification."""
    if not required_qual or not required_qual.strip():
        return True, 20.0, "No strict minimum qualification specified by job."

    req_lower = required_qual.lower()
    if not candidate_degree:
        return False, 5.0, "Candidate education not specified on resume."

    cand_lower = candidate_degree.lower()

    # Degree hierarchy
    def get_tier(text: str) -> int:
        if any(d in text for d in ["ph.d", "doctorate", "phd"]):
            return 4
        if any(d in text for d in ["master", "m.s", "m.tech", "mba", "msc"]):
            return 3
        if any(d in text for d in ["bachelor", "b.s", "b.tech", "b.e", "bsc", "b.a"]):
            return 2
        if any(d in text for d in ["associate", "diploma"]):
            return 1
        return 0

    req_tier = get_tier(req_lower)
    cand_tier = get_tier(cand_lower)

    if cand_tier >= req_tier and cand_tier > 0:
        return True, 20.0, f"Candidate degree ({candidate_degree}) meets or exceeds requirement ({required_qual})."
    elif cand_tier > 0:
        return False, 10.0, f"Candidate degree ({candidate_degree}) is below preferred tier ({required_qual})."
    else:
        # Partial match heuristic
        return True, 15.0, f"Candidate degree listed: {candidate_degree}."


def compute_experience_match(
    required_exp_raw: str,
    candidate_exp_str: str,
    candidate_roles: List[str],
) -> Tuple[bool, float, str]:
    """Evaluate candidate experience against job requirements."""
    if not required_exp_raw or not required_exp_raw.strip():
        return True, 20.0, "No specific experience requirement specified."

    # Extract required numeric years if any
    req_match = re.search(r"(\d+)", required_exp_raw)
    req_years = int(req_match.group(1)) if req_match else 0

    cand_years = 0
    if candidate_exp_str:
        cand_match = re.search(r"(\d+)", candidate_exp_str)
        if cand_match:
            cand_years = int(cand_match.group(1))

    # Bonus if candidate has roles matching tech/engineering
    role_count = len(candidate_roles)

    if req_years == 0:
        return True, 20.0, "Experience criteria satisfied."

    if cand_years >= req_years:
        return (
            True,
            20.0,
            f"Candidate has {cand_years}+ years of experience, meeting target of {req_years}+ years.",
        )
    elif cand_years > 0:
        gap = req_years - cand_years
        score = max(5.0, round(20.0 - (gap * 4.0), 1))
        return (
            False,
            score,
            f"Candidate has ~{cand_years} years; position prefers {req_years}+ years.",
        )
    elif role_count > 0:
        return (
            True,
            15.0,
            f"Candidate demonstrates relevant past roles ({', '.join(candidate_roles[:2])}).",
        )
    else:
        return (
            False,
            8.0,
            "Experience duration could not be definitively confirmed from resume text.",
        )


def compute_description_relevance(
    job_description: str,
    resume_text: str,
) -> float:
    """Evaluate keyword & domain alignment between job description and resume."""
    if not job_description or not resume_text:
        return 10.0

    # Extract informative keywords (>3 characters, alpha)
    stopwords = {
        "and", "the", "for", "with", "that", "this", "from", "have", "will", "your",
        "our", "team", "work", "role", "looking", "candidate", "must", "experience",
        "skills", "responsibilities", "requirements", "about", "company",
    }
    job_words = {
        w.lower()
        for w in re.findall(r"\b[A-Za-z]{4,}\b", job_description)
        if w.lower() not in stopwords
    }
    resume_words = {
        w.lower()
        for w in re.findall(r"\b[A-Za-z]{4,}\b", resume_text)
        if w.lower() not in stopwords
    }

    if not job_words:
        return 20.0

    intersection = job_words.intersection(resume_words)
    ratio = len(intersection) / len(job_words)
    # Scale to 20% weight
    return round(min(20.0, ratio * 40.0), 1)


def screen_candidate_resume(
    job_title: str,
    job_description: str,
    required_skills: str,
    qualification: str,
    experience_years: str,
    parsed_data: Dict[str, Any],
    raw_text: str,
) -> Dict[str, Any]:
    """Perform preliminary job-specific AI resume screening.

    Returns:
    - screening_score: float (0.0 to 100.0)
    - matched_skills: List[str]
    - missing_skills: List[str]
    - qualification_match: bool
    - experience_match: bool
    - explanation: str
    - score_breakdown: dict
    """
    candidate_skills = (parsed_data.get("technical_skills") or []) + (
        parsed_data.get("soft_skills") or []
    )
    candidate_degree = parsed_data.get("education") or ""
    candidate_exp = parsed_data.get("experience_years") or ""
    candidate_roles = parsed_data.get("work_experience") or []

    # 1. Skills overlap (40 pts)
    matched_skills, missing_skills, skills_score = compute_skills_overlap(
        required_skills_raw=required_skills,
        candidate_skills=candidate_skills,
        resume_text=raw_text,
    )

    # 2. Education match (20 pts)
    qual_match, qual_score, qual_expl = compute_education_match(
        required_qual=qualification,
        candidate_degree=candidate_degree,
    )

    # 3. Experience match (20 pts)
    exp_match, exp_score, exp_expl = compute_experience_match(
        required_exp_raw=experience_years,
        candidate_exp_str=candidate_exp,
        candidate_roles=candidate_roles,
    )

    # 4. Description relevance (20 pts)
    relevance_score = compute_description_relevance(
        job_description=job_description,
        resume_text=raw_text,
    )

    # Total score calculation
    total_score = min(
        100.0,
        max(0.0, round(skills_score + qual_score + exp_score + relevance_score, 1)),
    )

    # Generate recommendation tier
    if total_score >= 80.0:
        recommendation = "Strong Match"
    elif total_score >= 60.0:
        recommendation = "Good Match"
    elif total_score >= 40.0:
        recommendation = "Moderate Match"
    else:
        recommendation = "Limited Match"

    explanation_lines = [
        f"Overall Assessment: {recommendation} ({total_score}/100)",
        f"- Skills Overlap: Matched {len(matched_skills)} required skill(s) ({skills_score}/40 pts).",
    ]
    if matched_skills:
        explanation_lines.append(f"  • Matched: {', '.join(matched_skills)}")
    if missing_skills:
        explanation_lines.append(f"  • Missing: {', '.join(missing_skills)}")
    explanation_lines.append(f"- Qualification Match: {qual_expl} ({qual_score}/20 pts).")
    explanation_lines.append(f"- Experience Match: {exp_expl} ({exp_score}/20 pts).")
    explanation_lines.append(
        f"- Domain Content Relevance: {relevance_score}/20 pts alignment with role description."
    )
    explanation_lines.append(
        "Note: This score is advisory. Hiring recruiters make all interview and progression decisions."
    )

    return {
        "screening_score": total_score,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "qualification_match": qual_match,
        "experience_match": exp_match,
        "explanation": "\n".join(explanation_lines),
        "score_breakdown": {
            "skills_score": skills_score,
            "qualification_score": qual_score,
            "experience_score": exp_score,
            "relevance_score": relevance_score,
        },
    }
