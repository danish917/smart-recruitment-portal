"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import {
  Job,
  fetchJobDetails,
  fetchJobApplicants,
  updateApplicantStatus,
  downloadApplicantResume,
  triggerApplicantScreening,
  indexJobVector,
} from "@/lib/jobs";
import type { JobApplication, ApplicationStatus } from "@/lib/candidate";

type SortOption = "SKILL_COVERAGE" | "SEMANTIC" | "SCREENING" | "DATE";

function JobApplicantsContent() {
  const params = useParams();
  const jobId = Number(params?.id);

  const [job, setJob] = useState<Job | null>(null);
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [actionMessage, setActionMessage] = useState<{
    type: "success" | "error";
    text: string;
  } | null>(null);
  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | "ALL">("ALL");
  const [sortOption, setSortOption] = useState<SortOption>("SKILL_COVERAGE");
  const [expandedAppId, setExpandedAppId] = useState<number | null>(null);
  const [operatingAppId, setOperatingAppId] = useState<number | null>(null);
  const [indexingVector, setIndexingVector] = useState(false);

  const loadData = async () => {
    if (!jobId || isNaN(jobId)) {
      setError("Invalid Job Requisition ID.");
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const [jobData, appsData] = await Promise.all([
        fetchJobDetails(jobId),
        fetchJobApplicants(jobId),
      ]);
      setJob(jobData);
      setApplications(appsData);
    } catch (err: unknown) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load job details and applicants."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [jobId]);

  const handleStatusChange = async (
    applicationId: number,
    newStatus: ApplicationStatus
  ) => {
    setOperatingAppId(applicationId);
    setActionMessage(null);
    try {
      const updated = await updateApplicantStatus(applicationId, newStatus);
      setApplications((prev) =>
        prev.map((app) => (app.id === applicationId ? updated : app))
      );
      setActionMessage({
        type: "success",
        text: `Applicant status updated to ${newStatus.replace("_", " ")}.`,
      });
    } catch (err: unknown) {
      setActionMessage({
        type: "error",
        text:
          err instanceof Error
            ? err.message
            : "Failed to update applicant status.",
      });
    } finally {
      setOperatingAppId(null);
    }
  };

  const handleDownloadResume = async (
    applicationId: number,
    candidateName?: string
  ) => {
    setOperatingAppId(applicationId);
    setActionMessage(null);
    try {
      const blob = await downloadApplicantResume(applicationId);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `${(candidateName || "candidate").replace(/\s+/g, "_")}_resume.pdf`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      setActionMessage({
        type: "error",
        text:
          err instanceof Error
            ? err.message
            : "Failed to download candidate resume.",
      });
    } finally {
      setOperatingAppId(null);
    }
  };

  const handleScreenApplication = async (applicationId: number) => {
    setOperatingAppId(applicationId);
    setActionMessage(null);
    try {
      const screeningResult = await triggerApplicantScreening(applicationId);
      setApplications((prev) =>
        prev.map((app) =>
          app.id === applicationId
            ? {
                ...app,
                screening: screeningResult,
                semantic_score: screeningResult.semantic_score ?? app.semantic_score,
                skill_coverage: screeningResult.skill_coverage ?? app.skill_coverage,
              }
            : app
        )
      );
      setActionMessage({
        type: "success",
        text: `AI Screening & Skill Gap completed! Skill Coverage: ${Math.round(
          screeningResult.skill_coverage ?? 0
        )}% | Semantic Match: ${Math.round(
          screeningResult.semantic_score ?? 0
        )}% | Rule Score: ${Math.round(screeningResult.screening_score)}%`,
      });
    } catch (err: unknown) {
      setActionMessage({
        type: "error",
        text:
          err instanceof Error
            ? err.message
            : "Failed to evaluate AI screening.",
      });
    } finally {
      setOperatingAppId(null);
    }
  };

  const handleIndexJobVector = async () => {
    if (!job) return;
    setIndexingVector(true);
    setActionMessage(null);
    try {
      const updatedJob = await indexJobVector(job.id);
      setJob(updatedJob);
      setActionMessage({
        type: "success",
        text: "Job dense vector embedding successfully indexed in Qdrant Vector DB.",
      });
    } catch (err: unknown) {
      setActionMessage({
        type: "error",
        text:
          err instanceof Error
            ? err.message
            : "Failed to index job vector in Qdrant.",
      });
    } finally {
      setIndexingVector(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 font-medium">Loading applicants, vector embeddings & skill insights...</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center space-y-4">
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm shadow-sm">
          <p className="font-semibold text-rose-900">Error Loading Requisition</p>
          <p className="mt-1">{error || "Job requisition not found."}</p>
        </div>
        <Link
          href="/recruiter/jobs"
          className="inline-block px-4 py-2 text-xs font-semibold rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 transition shadow-sm"
        >
          &larr; Back to Job List
        </Link>
      </div>
    );
  }

  // Filter & sort applications
  const filteredApps = applications.filter((app) =>
    statusFilter === "ALL" ? true : app.status === statusFilter
  );

  const sortedApps = [...filteredApps].sort((a, b) => {
    if (sortOption === "SKILL_COVERAGE") {
      const scoreA = a.skill_coverage ?? a.screening?.skill_coverage ?? -1;
      const scoreB = b.skill_coverage ?? b.screening?.skill_coverage ?? -1;
      if (scoreB !== scoreA) return scoreB - scoreA;
    } else if (sortOption === "SEMANTIC") {
      const scoreA = a.semantic_score ?? a.screening?.semantic_score ?? -1;
      const scoreB = b.semantic_score ?? b.screening?.semantic_score ?? -1;
      if (scoreB !== scoreA) return scoreB - scoreA;
    } else if (sortOption === "SCREENING") {
      const scoreA = a.screening?.screening_score ?? -1;
      const scoreB = b.screening?.screening_score ?? -1;
      if (scoreB !== scoreA) return scoreB - scoreA;
    }
    return new Date(b.applied_at).getTime() - new Date(a.applied_at).getTime();
  });

  const getScoreBadge = (score: number) => {
    if (score >= 80) {
      return {
        bg: "bg-emerald-50 border-emerald-200 text-emerald-800",
        label: "Strong Match",
      };
    }
    if (score >= 60) {
      return {
        bg: "bg-emerald-50 border-emerald-200 text-emerald-700",
        label: "Good Match",
      };
    }
    if (score >= 40) {
      return {
        bg: "bg-amber-50 border-amber-200 text-amber-800",
        label: "Moderate Match",
      };
    }
    return {
      bg: "bg-rose-50 border-rose-200 text-rose-800",
      label: "Limited Match",
    };
  };

  return (
    <div className="space-y-8">
      {/* Breadcrumb & Requisition Header */}
      <div>
        <div className="flex items-center gap-2 text-xs text-emerald-600 font-semibold">
          <Link href="/recruiter/jobs" className="hover:text-emerald-700">
            Job Postings
          </Link>
          <span className="text-slate-400">/</span>
          <Link href={`/recruiter/jobs/${job.id}`} className="hover:text-emerald-700">
            {job.title}
          </Link>
          <span className="text-slate-400">/</span>
          <span className="text-slate-500">Applicants & Multi-Factor Intelligence</span>
        </div>

        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mt-3">
          <div>
            <div className="flex items-center gap-3 flex-wrap">
              <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
                {job.title} &mdash; Applicants
              </h1>
              <span
                className={`text-xs px-2.5 py-0.5 rounded-full font-semibold border ${
                  job.status === "ACTIVE"
                    ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                    : job.status === "DRAFT"
                    ? "bg-amber-50 text-amber-700 border-amber-200"
                    : "bg-slate-100 text-slate-600 border-slate-200"
                }`}
              >
                {job.status}
              </span>

              {job.is_indexed ? (
                <span className="text-[11px] px-2.5 py-0.5 rounded-full font-semibold bg-emerald-50 border border-emerald-200 text-emerald-800 flex items-center gap-1.5">
                  <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                  Qdrant Vector Indexed
                </span>
              ) : (
                <span className="text-[11px] px-2.5 py-0.5 rounded-full font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                  Vector Not Indexed
                </span>
              )}
            </div>
            <p className="text-xs text-slate-500 mt-1">
              {job.company_name} &bull; {job.work_location} &bull; Requisition #{job.id}
            </p>
          </div>

          <div className="flex items-center gap-2">
            {!job.is_indexed && job.status === "ACTIVE" && (
              <button
                onClick={handleIndexJobVector}
                disabled={indexingVector}
                className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50 cursor-pointer shadow-sm shadow-emerald-600/20"
              >
                {indexingVector ? "Indexing..." : "Index in Qdrant"}
              </button>
            )}

            <Link
              href={`/recruiter/jobs/${job.id}`}
              className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition shadow-sm"
            >
              View Job Requisition
            </Link>
          </div>
        </div>

        {/* Requisition Criteria Snapshot */}
        <div className="mt-4 p-4 rounded-2xl bg-white border border-slate-200 shadow-sm flex flex-wrap items-center gap-4 text-xs text-slate-700">
          <div>
            <span className="text-slate-500 mr-1.5 font-medium">Required Skills:</span>
            <span className="text-slate-900 font-bold">{job.required_skills}</span>
          </div>
          <div className="h-4 w-px bg-slate-200 hidden sm:block"></div>
          <div>
            <span className="text-slate-500 mr-1.5 font-medium">Experience:</span>
            <span className="text-slate-900 font-bold">{job.experience_years} years</span>
          </div>
          <div className="h-4 w-px bg-slate-200 hidden sm:block"></div>
          <div>
            <span className="text-slate-500 mr-1.5 font-medium">Qualification:</span>
            <span className="text-slate-900 font-bold">{job.qualification}</span>
          </div>
        </div>
      </div>

      {/* Action Notification */}
      {actionMessage && (
        <div
          className={`p-4 rounded-xl text-xs flex items-center justify-between border shadow-sm ${
            actionMessage.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}
        >
          <span className="font-medium">{actionMessage.text}</span>
          <button
            onClick={() => setActionMessage(null)}
            className="text-base font-bold px-2 hover:opacity-75 cursor-pointer ml-2"
          >
            &times;
          </button>
        </div>
      )}

      {/* Triple Intelligence Legend Banner (Phase 5 + Phase 6 + Phase 7) */}
      <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm grid grid-cols-1 md:grid-cols-3 gap-5 text-xs">
        <div className="flex items-start gap-2.5">
          <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-emerald-50 border border-emerald-200 text-emerald-800 shrink-0">
            Skill Coverage %
          </span>
          <p className="text-slate-600 leading-relaxed">
            <strong className="text-slate-900">Phase 7 Gap Analysis</strong>: Mathematical percentage of required technical skills matched via canonical taxonomies.
          </p>
        </div>
        <div className="flex items-start gap-2.5">
          <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-emerald-50 border border-emerald-200 text-emerald-800 shrink-0">
            Semantic AI
          </span>
          <p className="text-slate-600 leading-relaxed">
            <strong className="text-slate-900">Phase 6 Qdrant Vectors</strong>: Dense 384-d sentence embeddings capturing holistic domain context and experience.
          </p>
        </div>
        <div className="flex items-start gap-2.5">
          <span className="px-2.5 py-1 rounded-lg text-[11px] font-bold bg-emerald-50 border border-emerald-200 text-emerald-800 shrink-0">
            Screening Score
          </span>
          <p className="text-slate-600 leading-relaxed">
            <strong className="text-slate-900">Phase 5 Heuristics</strong>: Multi-factor rule evaluation: Skills (40%), Degree (20%), Experience (20%), and Relevance (20%).
          </p>
        </div>
      </div>

      {/* Filter and Sort Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-200 pb-4">
        {/* Status Filter Tabs */}
        <div className="flex items-center gap-2 overflow-x-auto text-xs">
          {(["ALL", "SHORTLISTED", "UNDER_REVIEW", "APPLIED", "REJECTED"] as const).map(
            (tab) => {
              const count =
                tab === "ALL"
                  ? applications.length
                  : applications.filter((a) => a.status === tab).length;

              return (
                <button
                  key={tab}
                  onClick={() => setStatusFilter(tab)}
                  className={`px-3 py-1.5 rounded-xl font-semibold transition cursor-pointer shrink-0 ${
                    statusFilter === tab
                      ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/20"
                      : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
                  }`}
                >
                  {tab.replace("_", " ")} ({count})
                </button>
              );
            }
          )}
        </div>

        {/* Sort Options */}
        <div className="flex items-center gap-2 text-xs flex-wrap">
          <span className="text-slate-500 font-medium">Sort by:</span>
          <button
            onClick={() => setSortOption("SKILL_COVERAGE")}
            className={`px-3 py-1.5 rounded-xl font-semibold border transition cursor-pointer ${
              sortOption === "SKILL_COVERAGE"
                ? "bg-emerald-50 border-emerald-300 text-emerald-800 shadow-sm"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            Skill Coverage &darr;
          </button>
          <button
            onClick={() => setSortOption("SEMANTIC")}
            className={`px-3 py-1.5 rounded-xl font-semibold border transition cursor-pointer ${
              sortOption === "SEMANTIC"
                ? "bg-emerald-50 border-emerald-300 text-emerald-800 shadow-sm"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            Semantic Match &darr;
          </button>
          <button
            onClick={() => setSortOption("SCREENING")}
            className={`px-3 py-1.5 rounded-xl font-semibold border transition cursor-pointer ${
              sortOption === "SCREENING"
                ? "bg-emerald-50 border-emerald-300 text-emerald-800 shadow-sm"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            Screening Score &darr;
          </button>
          <button
            onClick={() => setSortOption("DATE")}
            className={`px-3 py-1.5 rounded-xl font-semibold border transition cursor-pointer ${
              sortOption === "DATE"
                ? "bg-slate-800 text-white border-slate-800 shadow-sm"
                : "bg-white border-slate-200 text-slate-600 hover:bg-slate-50"
            }`}
          >
            Date Applied &darr;
          </button>
        </div>
      </div>

      {/* Applicants List */}
      {sortedApps.length === 0 ? (
        <div className="p-12 rounded-2xl bg-white border border-slate-200 text-center space-y-2 shadow-sm">
          <p className="text-sm font-bold text-slate-900">No applicants found</p>
          <p className="text-xs text-slate-500">
            {statusFilter === "ALL"
              ? "No candidates have applied for this job posting yet."
              : `No applicants currently under status "${statusFilter.replace("_", " ")}".`}
          </p>
        </div>
      ) : (
        <div className="space-y-4">
          {sortedApps.map((app) => {
            const isOperating = operatingAppId === app.id;
            const isExpanded = expandedAppId === app.id;
            const screening = app.screening;
            const semanticScore = app.semantic_score ?? screening?.semantic_score;
            const coverage = app.skill_coverage ?? screening?.skill_coverage;
            const badge = screening
              ? getScoreBadge(screening.screening_score)
              : null;

            return (
              <div
                key={app.id}
                className="rounded-2xl bg-white border border-slate-200 hover:border-emerald-200 hover:shadow-md transition overflow-hidden shadow-sm"
              >
                {/* Main Applicant Row */}
                <div className="p-6 flex flex-col lg:flex-row lg:items-center justify-between gap-6">
                  {/* Candidate Bio & Multi-Factor Intelligence Scores */}
                  <div className="space-y-2.5 flex-1">
                    <div className="flex items-center gap-3 flex-wrap">
                      <h3 className="text-base font-bold text-slate-900">
                        {app.candidate_name || `Applicant #${app.candidate_id}`}
                      </h3>

                      <span
                        className={`text-xs px-2.5 py-0.5 rounded-full font-bold uppercase tracking-wider border ${
                          app.status === "SHORTLISTED"
                            ? "bg-emerald-50 text-emerald-700 border-emerald-200"
                            : app.status === "REJECTED"
                            ? "bg-rose-50 text-rose-700 border-rose-200"
                            : app.status === "UNDER_REVIEW"
                            ? "bg-amber-50 text-amber-700 border-amber-200"
                            : "bg-blue-50 text-blue-700 border-blue-200"
                        }`}
                      >
                        {app.status.replace("_", " ")}
                      </span>

                      {/* Phase 7 Skill Coverage Pill */}
                      {coverage !== null && coverage !== undefined && (
                        <div className="flex items-center gap-1 px-3 py-0.5 rounded-full text-xs font-bold border bg-emerald-50 border-emerald-200 text-emerald-800">
                          <span>Skill Coverage: {Math.round(coverage)}%</span>
                        </div>
                      )}

                      {/* Phase 6 Semantic Dense Vector Score Pill */}
                      {semanticScore !== null && semanticScore !== undefined && (
                        <div className="flex items-center gap-1 px-3 py-0.5 rounded-full text-xs font-bold border bg-emerald-50 border-emerald-200 text-emerald-800">
                          <span>Semantic AI: {Math.round(semanticScore)}%</span>
                        </div>
                      )}

                      {/* Phase 5 Rule-Based Screening Pill */}
                      {badge && screening && (
                        <div
                          className={`flex items-center gap-1.5 px-3 py-0.5 rounded-full text-xs font-bold border ${badge.bg}`}
                        >
                          <span>Screening: {Math.round(screening.screening_score)}%</span>
                          <span>&bull;</span>
                          <span>{badge.label}</span>
                        </div>
                      )}
                    </div>

                    <div className="flex items-center gap-4 text-xs text-slate-500 flex-wrap">
                      {app.candidate_email && (
                        <span>Email: <strong className="text-slate-800">{app.candidate_email}</strong></span>
                      )}
                      <span>Applied: {new Date(app.applied_at).toLocaleDateString()}</span>
                      {app.resume_id && (
                        <span className="text-emerald-700 font-semibold">&bull; PDF Resume Available</span>
                      )}
                    </div>

                    {/* Quick Skills Overlap Pills */}
                    {screening && (
                      <div className="pt-1 flex flex-wrap items-center gap-1.5">
                        {screening.matched_skills && screening.matched_skills.length > 0 ? (
                          screening.matched_skills.map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-emerald-50 border border-emerald-200 text-emerald-800"
                            >
                              ✓ {skill}
                            </span>
                          ))
                        ) : (
                          <span className="text-[11px] text-slate-500 italic">No direct required skill matches.</span>
                        )}

                        {screening.missing_skills && screening.missing_skills.length > 0 && (
                          screening.missing_skills.map((skill, idx) => (
                            <span
                              key={idx}
                              className="px-2 py-0.5 rounded-md text-[11px] font-medium bg-rose-50 border border-rose-200 text-rose-700"
                            >
                              ✕ {skill}
                            </span>
                          ))
                        )}
                      </div>
                    )}
                  </div>

                  {/* Actions Bar */}
                  <div className="flex flex-col sm:flex-row lg:flex-col items-stretch lg:items-end gap-2.5 shrink-0">
                    <div className="flex items-center gap-2">
                      {app.resume_id && (
                        <button
                          onClick={() => handleDownloadResume(app.id, app.candidate_name)}
                          disabled={isOperating}
                          className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50 cursor-pointer shadow-sm shadow-emerald-600/20"
                        >
                          Download Resume
                        </button>
                      )}

                      <button
                        onClick={() => handleScreenApplication(app.id)}
                        disabled={isOperating || !app.resume_id}
                        className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition disabled:opacity-40 cursor-pointer shadow-sm"
                        title="Re-run dense vector matching, skill gap and screening heuristics"
                      >
                        {screening ? "Re-Screen & Analyze" : "Run AI Screen"}
                      </button>

                      {screening && (
                        <button
                          onClick={() => setExpandedAppId(isExpanded ? null : app.id)}
                          className="px-3 py-1.5 text-xs font-semibold rounded-xl bg-white hover:bg-emerald-50 text-emerald-700 border border-slate-200 transition cursor-pointer shadow-sm"
                        >
                          {isExpanded ? "Hide Details ▲" : "View Breakdown ▼"}
                        </button>
                      )}
                    </div>

                    {/* Status Decision Buttons */}
                    <div className="flex items-center gap-1.5 self-end pt-1">
                      <span className="text-[11px] text-slate-500 mr-1 font-medium">Move to:</span>
                      {app.status !== "SHORTLISTED" && (
                        <button
                          onClick={() => handleStatusChange(app.id, "SHORTLISTED")}
                          disabled={isOperating}
                          className="px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 text-emerald-700 transition disabled:opacity-50 cursor-pointer"
                        >
                          Shortlist
                        </button>
                      )}
                      {app.status !== "UNDER_REVIEW" && (
                        <button
                          onClick={() => handleStatusChange(app.id, "UNDER_REVIEW")}
                          disabled={isOperating}
                          className="px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-amber-50 hover:bg-amber-100 border border-amber-200 text-amber-700 transition disabled:opacity-50 cursor-pointer"
                        >
                          Review
                        </button>
                      )}
                      {app.status !== "REJECTED" && (
                        <button
                          onClick={() => handleStatusChange(app.id, "REJECTED")}
                          disabled={isOperating}
                          className="px-2.5 py-1 text-[11px] font-semibold rounded-lg bg-rose-50 hover:bg-rose-100 border border-rose-200 text-rose-700 transition disabled:opacity-50 cursor-pointer"
                        >
                          Reject
                        </button>
                      )}
                    </div>
                  </div>
                </div>

                {/* Expanded Detailed Multi-Factor Breakdown Accordion */}
                {isExpanded && screening && (
                  <div className="p-6 bg-slate-50 border-t border-slate-200 space-y-6">
                    <div className="flex items-center justify-between text-xs">
                      <h4 className="font-bold text-slate-900 uppercase tracking-wider">
                        Transparent AI, Vector & Skill-Gap Breakdown
                      </h4>
                      <span className="text-slate-500">
                        Evaluated: {new Date(screening.screened_at).toLocaleString()}
                      </span>
                    </div>

                    {/* 3-Pillar Intelligence Cards */}
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      {/* 1. Phase 7 Skill Coverage Card */}
                      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1.5">
                        <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">
                          Phase 7 Skill Coverage
                        </span>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-black text-slate-900">
                            {coverage !== null && coverage !== undefined
                              ? `${Math.round(coverage)}%`
                              : "N/A"}
                          </span>
                          <span className="text-xs text-emerald-700 font-semibold">Requirement Match</span>
                        </div>
                        <p className="text-[11px] text-slate-500 leading-relaxed">
                          Deterministic mathematical overlap across {screening.matched_skills.length} matched and {screening.missing_skills.length} missing skill(s).
                        </p>
                      </div>

                      {/* 2. Phase 6 Vector Semantic Match Card */}
                      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1.5">
                        <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">
                          Qdrant Dense Vector Similarity
                        </span>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-black text-slate-900">
                            {semanticScore !== null && semanticScore !== undefined
                              ? `${Math.round(semanticScore)}%`
                              : "Not Computed"}
                          </span>
                          <span className="text-xs text-emerald-700 font-semibold">Cosine Distance</span>
                        </div>
                        <p className="text-[11px] text-slate-500 leading-relaxed">
                          Computed using 384-dimensional embeddings comparing candidate projects, experience depth, and requisition context.
                        </p>
                      </div>

                      {/* 3. Phase 5 Rule-Based Compliance Card */}
                      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-1.5">
                        <span className="text-[11px] font-bold text-emerald-800 uppercase tracking-wider">
                          Rule-Based Screening Score
                        </span>
                        <div className="flex items-baseline gap-2">
                          <span className="text-2xl font-black text-slate-900">
                            {Math.round(screening.screening_score)}%
                          </span>
                          <span className="text-xs text-emerald-700 font-semibold">Multi-Factor Compliance</span>
                        </div>
                        <p className="text-[11px] text-slate-500 leading-relaxed">
                          Synthesized across Skills (40%), Degree Tier (20%), Experience Threshold (20%), and Description Relevance (20%).
                        </p>
                      </div>
                    </div>

                    {/* Skill Breakdown & Candidate Strengths */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      {/* Matched Skills */}
                      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-2">
                        <span className="text-xs font-bold text-emerald-800 block">
                          &check; Verified Required Skills ({screening.matched_skills.length})
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {screening.matched_skills.length > 0 ? (
                            screening.matched_skills.map((s, i) => (
                              <span
                                key={i}
                                className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200"
                              >
                                {s}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-slate-500">None identified.</span>
                          )}
                        </div>
                      </div>

                      {/* Missing Skills */}
                      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-2">
                        <span className="text-xs font-bold text-rose-800 block">
                          &times; Missing Job Requirements ({screening.missing_skills.length})
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {screening.missing_skills.length > 0 ? (
                            screening.missing_skills.map((s, i) => (
                              <span
                                key={i}
                                className="px-2.5 py-1 rounded-md text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200"
                              >
                                {s}
                              </span>
                            ))
                          ) : (
                            <span className="text-xs text-emerald-700 font-semibold">All required skills matched!</span>
                          )}
                        </div>
                      </div>
                    </div>

                    {/* Additional Candidate Strengths if any */}
                    {screening.skill_gap_analysis?.additional_skills?.length > 0 && (
                      <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm space-y-2">
                        <span className="text-xs font-bold text-slate-800 block">
                          ★ Additional Candidate Strengths & Bonus Capabilities
                        </span>
                        <div className="flex flex-wrap gap-1.5">
                          {screening.skill_gap_analysis.additional_skills.map((s: string, i: number) => (
                            <span
                              key={i}
                              className="px-2.5 py-1 rounded-md text-xs font-medium bg-slate-50 text-slate-700 border border-slate-200"
                            >
                              {s}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}

                    {/* Rule-Based Score Component Breakdown */}
                    {screening.score_breakdown && (
                      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm text-center">
                          <span className="text-[11px] text-slate-500 block">Skills Overlap (40%)</span>
                          <span className="text-base font-bold text-slate-900 mt-1 block">
                            {screening.score_breakdown.skills_score} / 40
                          </span>
                        </div>
                        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm text-center">
                          <span className="text-[11px] text-slate-500 block">Education Match (20%)</span>
                          <span className="text-base font-bold text-slate-900 mt-1 block">
                            {screening.score_breakdown.qualification_score} / 20
                          </span>
                        </div>
                        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm text-center">
                          <span className="text-[11px] text-slate-500 block">Experience Match (20%)</span>
                          <span className="text-base font-bold text-slate-900 mt-1 block">
                            {screening.score_breakdown.experience_score} / 20
                          </span>
                        </div>
                        <div className="p-3 rounded-xl bg-white border border-slate-200 shadow-sm text-center">
                          <span className="text-[11px] text-slate-500 block">Job Relevance (20%)</span>
                          <span className="text-base font-bold text-slate-900 mt-1 block">
                            {screening.score_breakdown.relevance_score} / 20
                          </span>
                        </div>
                      </div>
                    )}

                    {/* Criteria Checkmarks */}
                    <div className="flex items-center gap-6 text-xs text-slate-700">
                      <div className="flex items-center gap-2">
                        <span className={`h-2.5 w-2.5 rounded-full ${screening.qualification_match ? "bg-emerald-500" : "bg-slate-300"}`}></span>
                        <span>Qualification Match: <strong className="text-slate-900">{screening.qualification_match ? "Met" : "Not Confirmed"}</strong></span>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className={`h-2.5 w-2.5 rounded-full ${screening.experience_match ? "bg-emerald-500" : "bg-slate-300"}`}></span>
                        <span>Experience Requirement: <strong className="text-slate-900">{screening.experience_match ? "Met" : "Below Baseline"}</strong></span>
                      </div>
                    </div>

                    {/* Evaluation Narrative */}
                    <div className="p-4 rounded-xl bg-white border border-slate-200 shadow-sm text-xs text-slate-700 space-y-2">
                      <p className="font-bold text-slate-900">Evaluation Narrative:</p>
                      <p className="leading-relaxed whitespace-pre-line text-slate-600">
                        {screening.explanation}
                      </p>
                    </div>

                    {/* Responsible AI Disclaimer */}
                    <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-800">
                      <strong className="font-bold">Responsible AI Disclaimer:</strong> All scores and gap recommendations are strictly advisory and generated to assist recruiter review. Hiring and progression decisions remain solely with human recruitment personnel.
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}

export default function JobApplicantsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500 font-medium">Loading applicants...</p>
        </div>
      }
    >
      <JobApplicantsContent />
    </Suspense>
  );
}
