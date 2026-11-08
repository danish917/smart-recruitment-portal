/**
 * Candidate API client utilities for Profile, Resume, Discovery, and Applications.
 */

import { getStoredToken } from "./auth";
import { Job, EmploymentType } from "./jobs";
export type { Job, EmploymentType };

export interface CandidateProfile {
  id: number;
  user_id: number;
  full_name?: string | null;
  phone_number?: string | null;
  email?: string | null;
  education?: string | null;
  college_university?: string | null;
  graduation_year?: number | null;
  skills?: string | null;
  experience?: string | null;
  location?: string | null;
  professional_summary?: string | null;
  created_at: string;
  updated_at: string;
  has_resume: boolean;
}

export interface CandidateProfileUpdateInput {
  full_name?: string;
  phone_number?: string;
  education?: string;
  college_university?: string;
  graduation_year?: number | null;
  skills?: string;
  experience?: string;
  location?: string;
  professional_summary?: string;
}

export type ParsingStatus =
  | "PENDING"
  | "PARSED"
  | "FAILED"
  | "OCR_REQUIRED";

export interface ParsedResumeData {
  name?: string | null;
  email?: string | null;
  phone?: string | null;
  technical_skills: string[];
  soft_skills: string[];
  education?: string | null;
  college_university?: string | null;
  graduation_year?: number | null;
  experience_years?: string | null;
  work_experience: string[];
  projects: string[];
  certifications: string[];
}

export interface ParsedResume {
  id: number;
  resume_id: number;
  candidate_id: number;
  status: ParsingStatus;
  extracted_data?: ParsedResumeData | null;
  error_message?: string | null;
  is_indexed: boolean;
  indexed_at?: string | null;
  parsed_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ResumeMetadata {
  id: number;
  candidate_id: number;
  original_filename: string;
  file_size: number;
  content_type: string;
  created_at: string;
  updated_at: string;
  parsed_resume?: ParsedResume | null;
}

export interface CandidateDashboardStats {
  profile_completion_percentage: number;
  total_applications: number;
  pending_applications: number;
  shortlisted_applications: number;
  rejected_applications: number;
  has_resume: boolean;
  recent_jobs: Job[];
}

export type ApplicationStatus =
  | "APPLIED"
  | "UNDER_REVIEW"
  | "SHORTLISTED"
  | "REJECTED";

export interface ScreeningEvaluation {
  id: number;
  application_id: number;
  screening_score: number;
  semantic_score?: number | null;
  skill_coverage?: number | null;
  matched_skills: string[];
  missing_skills: string[];
  qualification_match: boolean;
  experience_match: boolean;
  explanation: string;
  score_breakdown?: {
    skills_score: number;
    qualification_score: number;
    experience_score: number;
    relevance_score: number;
  };
  skill_gap_analysis?: any;
  screened_at: string;
}

export interface JobApplication {
  id: number;
  candidate_id: number;
  job_id: number;
  status: ApplicationStatus;
  cover_letter?: string | null;
  resume_id?: number | null;
  applied_at: string;
  updated_at: string;
  job?: Job;
  candidate_name?: string;
  candidate_email?: string;
  screening?: ScreeningEvaluation | null;
  semantic_score?: number | null;
  skill_coverage?: number | null;
}

export interface JobRecommendation {
  job: Job;
  similarity_score: number;
  match_tier: string;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

function authHeaders(isJson: boolean = true): HeadersInit {
  const token = getStoredToken();
  if (!token) {
    throw new Error("Authentication required. Please sign in.");
  }
  const headers: Record<string, string> = {
    Authorization: `Bearer ${token}`,
  };
  if (isJson) {
    headers["Content-Type"] = "application/json";
  }
  return headers;
}

// -------------------------------------------------------------------------
// Candidate Profile
// -------------------------------------------------------------------------

export async function fetchCandidateProfile(): Promise<CandidateProfile> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/profile`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to load candidate profile.");
  }
  return res.json();
}

export async function updateCandidateProfile(
  payload: CandidateProfileUpdateInput
): Promise<CandidateProfile> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/profile`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to update profile.");
  }
  return res.json();
}

// -------------------------------------------------------------------------
// Resume Management
// -------------------------------------------------------------------------

export async function fetchResumeMetadata(): Promise<ResumeMetadata | null> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/resume`, {
    headers: authHeaders(),
  });
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch resume information.");
  }
  return res.json();
}

export async function uploadResumeFile(file: File): Promise<ResumeMetadata> {
  const formData = new FormData();
  formData.append("file", file);

  const res = await fetch(`${API_BASE_URL}/api/candidate/resume/upload`, {
    method: "POST",
    headers: authHeaders(false), // Let browser set boundary
    body: formData,
  });

  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to upload resume.");
  }
  return res.json();
}

export async function downloadResumeFile(): Promise<Blob> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/resume/download`, {
    headers: authHeaders(false),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to download resume.");
  }
  return res.blob();
}

export async function deleteResumeFile(): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/resume`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to delete resume.");
  }
  return res.json();
}

export async function fetchParsedResume(): Promise<ParsedResume | null> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/resume/parsed`, {
    headers: authHeaders(),
  });
  if (res.status === 404) {
    return null;
  }
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch parsed resume information.");
  }
  return res.json();
}

export async function reparseResume(): Promise<ParsedResume> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/resume/reparse`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to trigger resume re-parsing.");
  }
  return res.json();
}

// -------------------------------------------------------------------------
// Candidate Dashboard
// -------------------------------------------------------------------------

export async function fetchCandidateStats(): Promise<CandidateDashboardStats> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/dashboard/stats`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to retrieve candidate dashboard statistics.");
  }
  return res.json();
}

// -------------------------------------------------------------------------
// Job Discovery
// -------------------------------------------------------------------------

export async function fetchActiveJobs(params?: {
  q?: string;
  location?: string;
  employment_type?: EmploymentType;
}): Promise<Job[]> {
  const url = new URL(`${API_BASE_URL}/api/jobs`);
  if (params?.q) url.searchParams.append("q", params.q);
  if (params?.location) url.searchParams.append("location", params.location);
  if (params?.employment_type)
    url.searchParams.append("employment_type", params.employment_type);

  const res = await fetch(url.toString());
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to discover active jobs.");
  }
  return res.json();
}

export async function fetchActiveJobDetails(jobId: number): Promise<Job> {
  const res = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`);
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Job #${jobId} not found or no longer active.`);
  }
  return res.json();
}

// -------------------------------------------------------------------------
// Job Applications
// -------------------------------------------------------------------------

export async function submitJobApplication(
  jobId: number,
  coverLetter?: string
): Promise<JobApplication> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/applications`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify({
      job_id: jobId,
      cover_letter: coverLetter || null,
    }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to submit job application.");
  }
  return res.json();
}

export async function fetchCandidateApplications(): Promise<JobApplication[]> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/applications`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to retrieve application history.");
  }
  return res.json();
}

// -------------------------------------------------------------------------
// Semantic AI Recommendations & Vector Indexing
// -------------------------------------------------------------------------

export async function fetchRecommendedJobs(limit: number = 10): Promise<JobRecommendation[]> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/jobs/recommended?limit=${limit}`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to retrieve semantic job recommendations.");
  }
  return res.json();
}

export async function indexResumeVector(): Promise<ParsedResume> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/resume/index-vector`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to index resume vector in Qdrant.");
  }
  return res.json();
}

// -------------------------------------------------------------------------
// Phase 7: Skill-Gap Analysis & Intelligent Recommendations
// -------------------------------------------------------------------------

export interface DocumentationLink {
  title: string;
  url: string;
}

export interface LearningRecommendation {
  skill_name: string;
  required_skill?: string | null;
  category: string;
  difficulty: "beginner" | "intermediate" | "advanced" | string;
  estimated_hours: number;
  priority: "HIGH" | "MEDIUM" | "LOW" | string;
  note?: string | null;
  core_concepts: string[];
  learning_objectives: string[];
  documentation_links: DocumentationLink[];
  practice_project?: string | null;
}

export interface PartialSkillMatch {
  required_skill: string;
  candidate_related_skill: string;
  relationship: string;
}

export interface SkillGapAnalysisReport {
  job_id: number;
  job_title: string;
  coverage_percentage: number;
  match_tier: string;
  total_required_count: number;
  matched_count: number;
  missing_count: number;
  matched_skills: string[];
  missing_skills: string[];
  partial_skills: PartialSkillMatch[];
  additional_skills: string[];
  skills_to_improve: string[];
  learning_recommendations: LearningRecommendation[];
  strengths_summary: string;
  growth_summary: string;
  advisory_note: string;
}

export interface CandidateSkillGapSummary {
  candidate_id: number;
  candidate_name?: string | null;
  total_skills_detected: number;
  detected_skills: string[];
  total_applications_analyzed: number;
  average_skill_coverage: number;
  top_market_skill_gaps: string[];
  recommended_learning_roadmaps: LearningRecommendation[];
  advisory_note: string;
}

export async function fetchJobSkillGap(jobId: number): Promise<SkillGapAnalysisReport> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/jobs/${jobId}/skill-gap`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Failed to evaluate skill gap for job #${jobId}.`);
  }
  return res.json();
}

export async function fetchCandidateSkillGapSummary(): Promise<CandidateSkillGapSummary> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/skill-gap/summary`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to load candidate skill-gap summary.");
  }
  return res.json();
}

// ----------------------------------------------------------------------------
// Phase 8: Candidate Pipeline & Progression Analytics
// ----------------------------------------------------------------------------

export interface CandidateStatusDistribution {
  applied: number;
  under_review: number;
  shortlisted: number;
  rejected: number;
  total: number;
}

export interface CandidateRecentActivityItem {
  id: number;
  activity_type: string;
  title: string;
  description: string;
  timestamp: string;
  status?: string | null;
  job_id?: number | null;
  job_title?: string | null;
  candidate_name?: string | null;
  metric_value?: number | null;
}

export interface SkillProgressPoint {
  application_id: number;
  job_id: number;
  job_title: string;
  applied_at: string;
  skill_coverage?: number | null;
  semantic_score?: number | null;
  screening_score?: number | null;
  status: string;
}

export interface CandidateAnalyticsResponse {
  total_applications: number;
  applications_under_review: number;
  shortlisted_applications: number;
  rejected_applications: number;
  status_distribution: CandidateStatusDistribution;
  average_skill_coverage?: number | null;
  average_semantic_score?: number | null;
  profile_completion_percentage: number;
  has_resume: boolean;
  recent_activity: CandidateRecentActivityItem[];
  skill_progress_history: SkillProgressPoint[];
  recommended_jobs_count: number;
}

export async function fetchCandidateAnalytics(): Promise<CandidateAnalyticsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/candidate/analytics`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch candidate analytics.");
  }
  return res.json();
}
