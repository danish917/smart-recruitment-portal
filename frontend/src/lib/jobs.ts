/**
 * Job management API client utilities for Recruiter module.
 */

import { getStoredToken } from "./auth";
import type { JobApplication, ApplicationStatus, ScreeningEvaluation } from "./candidate";

export type JobStatus = "DRAFT" | "ACTIVE" | "ARCHIVED";
export type EmploymentType =
  | "FULL_TIME"
  | "PART_TIME"
  | "CONTRACT"
  | "INTERNSHIP"
  | "REMOTE";

export interface Job {
  id: number;
  recruiter_id: number;
  title: string;
  company_name: string;
  description: string;
  required_skills: string;
  qualification: string;
  experience_years: string;
  employment_type: EmploymentType;
  work_location: string;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency: string;
  deadline?: string | null;
  status: JobStatus;
  is_indexed: boolean;
  created_at: string;
  updated_at: string;
}

export interface RecruiterDashboardStats {
  total_jobs: number;
  active_jobs: number;
  draft_jobs: number;
  archived_jobs: number;
  total_applications: number;
  recent_jobs: Job[];
}

export interface JobCreateInput {
  title: string;
  company_name: string;
  description: string;
  required_skills: string;
  qualification: string;
  experience_years: string;
  employment_type: EmploymentType;
  work_location: string;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string;
  deadline?: string | null;
  status?: JobStatus;
}

export interface JobUpdateInput {
  title?: string;
  company_name?: string;
  description?: string;
  required_skills?: string;
  qualification?: string;
  experience_years?: string;
  employment_type?: EmploymentType;
  work_location?: string;
  salary_min?: number | null;
  salary_max?: number | null;
  salary_currency?: string;
  deadline?: string | null;
  status?: JobStatus;
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

export async function fetchRecruiterStats(): Promise<RecruiterDashboardStats> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/dashboard/stats`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to load dashboard metrics.");
  }
  return res.json();
}

export async function fetchRecruiterJobs(statusFilter?: JobStatus): Promise<Job[]> {
  const url = new URL(`${API_BASE_URL}/api/recruiter/jobs`);
  if (statusFilter) {
    url.searchParams.append("status", statusFilter);
  }
  const res = await fetch(url.toString(), {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to retrieve job postings.");
  }
  return res.json();
}

export async function fetchJobDetails(jobId: number): Promise<Job> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/jobs/${jobId}`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Failed to retrieve job #${jobId}.`);
  }
  return res.json();
}

export async function createJob(payload: JobCreateInput): Promise<Job> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/jobs`, {
    method: "POST",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const errorMsg =
      typeof data.detail === "string"
        ? data.detail
        : data.detail?.[0]?.msg || "Failed to create job posting.";
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function updateJob(jobId: number, payload: JobUpdateInput): Promise<Job> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/jobs/${jobId}`, {
    method: "PUT",
    headers: authHeaders(),
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    const errorMsg =
      typeof data.detail === "string"
        ? data.detail
        : data.detail?.[0]?.msg || "Failed to update job posting.";
    throw new Error(errorMsg);
  }
  return res.json();
}

export async function publishJob(jobId: number): Promise<Job> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/jobs/${jobId}/publish`, {
    method: "PATCH",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to publish job.");
  }
  return res.json();
}

export async function archiveJob(jobId: number): Promise<Job> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/jobs/${jobId}/archive`, {
    method: "PATCH",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to archive job.");
  }
  return res.json();
}

export async function deleteJob(jobId: number): Promise<{ message: string }> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/jobs/${jobId}`, {
    method: "DELETE",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to delete job.");
  }
  return res.json();
}

// -------------------------------------------------------------------------
// Recruiter Applicant Management & AI Screening
// -------------------------------------------------------------------------

export async function fetchJobApplicants(
  jobId: number,
  sortBy: string = "date"
): Promise<JobApplication[]> {
  const url = new URL(`${API_BASE_URL}/api/recruiter/jobs/${jobId}/applications`);
  if (sortBy) {
    url.searchParams.append("sort_by", sortBy);
  }
  const res = await fetch(url.toString(), {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Failed to fetch applicants for job #${jobId}.`);
  }
  return res.json();
}

export async function updateApplicantStatus(
  applicationId: number,
  status: ApplicationStatus
): Promise<JobApplication> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/applications/${applicationId}/status`, {
    method: "PATCH",
    headers: authHeaders(),
    body: JSON.stringify({ status }),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to update applicant status.");
  }
  return res.json();
}

export async function downloadApplicantResume(applicationId: number): Promise<Blob> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/applications/${applicationId}/resume`, {
    headers: authHeaders(false),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to download applicant resume.");
  }
  return res.blob();
}

export async function triggerApplicantScreening(applicationId: number): Promise<ScreeningEvaluation> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/applications/${applicationId}/screen`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to trigger AI resume screening.");
  }
  return res.json();
}

export interface SemanticApplicantMatch {
  application_id: number;
  candidate_id: number;
  candidate_name?: string | null;
  candidate_email?: string | null;
  semantic_score: number;
  screening_score?: number | null;
  skill_coverage?: number | null;
  matched_skills: string[];
  missing_skills: string[];
  status: string;
  applied_at: string;
}

export async function fetchJobSemanticMatches(jobId: number): Promise<SemanticApplicantMatch[]> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/jobs/${jobId}/semantic-matches`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to retrieve semantic applicant rankings.");
  }
  return res.json();
}

export interface RecruiterApplicantSkillInsight {
  application_id: number;
  candidate_id: number;
  candidate_name?: string | null;
  candidate_email?: string | null;
  skill_coverage: number;
  screening_score?: number | null;
  semantic_score?: number | null;
  matched_skills: string[];
  missing_skills: string[];
  additional_skills: string[];
  partial_skills: {
    required_skill: string;
    candidate_related_skill: string;
    relationship: string;
  }[];
  status: string;
  applied_at: string;
}

export async function fetchJobSkillInsights(
  jobId: number,
  sortBy: string = "skill_coverage"
): Promise<RecruiterApplicantSkillInsight[]> {
  const url = new URL(`${API_BASE_URL}/api/recruiter/jobs/${jobId}/skill-insights`);
  if (sortBy) {
    url.searchParams.append("sort_by", sortBy);
  }
  const res = await fetch(url.toString(), {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || `Failed to fetch skill insights for job #${jobId}.`);
  }
  return res.json();
}

export async function indexJobVector(jobId: number): Promise<Job> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/jobs/${jobId}/index-vector`, {
    method: "POST",
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to index job vector in Qdrant.");
  }
  return res.json();
}

// ----------------------------------------------------------------------------
// Phase 8: Recruiter Pipeline Analytics
// ----------------------------------------------------------------------------

export interface StatusDistribution {
  applied: number;
  under_review: number;
  shortlisted: number;
  rejected: number;
  total: number;
}

export interface RecentActivityItem {
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

export interface JobPerformanceMetric {
  job_id: number;
  job_title: string;
  company_name: string;
  status: string;
  applicant_count: number;
  average_skill_coverage?: number | null;
  average_semantic_score?: number | null;
  shortlisted_count: number;
}

export interface RecruiterAnalyticsResponse {
  total_jobs: number;
  active_jobs: number;
  draft_jobs: number;
  archived_jobs: number;
  total_applications: number;
  applications_under_review: number;
  shortlisted_candidates: number;
  rejected_applications: number;
  average_skill_coverage?: number | null;
  average_semantic_score?: number | null;
  average_screening_score?: number | null;
  status_distribution: StatusDistribution;
  recent_activity: RecentActivityItem[];
  top_jobs: JobPerformanceMetric[];
}

export async function fetchRecruiterAnalytics(): Promise<RecruiterAnalyticsResponse> {
  const res = await fetch(`${API_BASE_URL}/api/recruiter/analytics`, {
    headers: authHeaders(),
  });
  if (!res.ok) {
    const data = await res.json().catch(() => ({}));
    throw new Error(data.detail || "Failed to fetch recruiter analytics.");
  }
  return res.json();
}
