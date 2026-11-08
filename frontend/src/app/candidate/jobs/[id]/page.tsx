"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import { Job } from "@/lib/jobs";
import {
  JobApplication,
  ResumeMetadata,
  SkillGapAnalysisReport,
  fetchActiveJobDetails,
  fetchCandidateApplications,
  fetchJobSkillGap,
  fetchResumeMetadata,
  submitJobApplication,
} from "@/lib/candidate";

function CandidateJobDetailsContent() {
  const params = useParams();
  const router = useRouter();
  const jobId = Number(params?.id);

  const [job, setJob] = useState<Job | null>(null);
  const [existingApp, setExistingApp] = useState<JobApplication | null>(null);
  const [resume, setResume] = useState<ResumeMetadata | null>(null);
  const [skillGap, setSkillGap] = useState<SkillGapAnalysisReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [coverLetter, setCoverLetter] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      if (!jobId || isNaN(jobId)) {
        setError("Invalid Job ID.");
        setLoading(false);
        return;
      }
      setLoading(true);
      setError(null);
      try {
        const [jobData, apps, resumeData] = await Promise.all([
          fetchActiveJobDetails(jobId),
          fetchCandidateApplications(),
          fetchResumeMetadata(),
        ]);
        setJob(jobData);
        setResume(resumeData);
        const match = apps.find((a) => a.job_id === jobId);
        if (match) {
          setExistingApp(match);
        }

        // Fetch deterministic Phase 7 skill-gap analysis
        try {
          const gapData = await fetchJobSkillGap(jobId);
          setSkillGap(gapData);
        } catch {
          // If unauthenticated or no profile yet, skillGap will stay null gracefully
        }
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load job requisition details."
        );
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, [jobId]);

  const handleApply = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!job) return;

    setSubmitting(true);
    setError(null);
    setSuccess(null);

    try {
      const createdApp = await submitJobApplication(job.id, coverLetter);
      setExistingApp(createdApp);
      setSuccess("Your application has been successfully submitted to the recruiter!");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to submit application."
      );
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 font-medium">Loading job details and AI skill analysis...</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center space-y-4">
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm shadow-sm">
          <p className="font-semibold text-rose-900">Requisition Unavailable</p>
          <p className="mt-1">{error || "Job not found or no longer active."}</p>
        </div>
        <Link
          href="/candidate/jobs"
          className="inline-block px-4 py-2 text-xs font-semibold rounded-xl bg-white border border-slate-200 hover:bg-slate-50 text-slate-700 transition shadow-sm"
        >
          &larr; Back to Job Discovery
        </Link>
      </div>
    );
  }

  const skillsList = job.required_skills
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Top Breadcrumb */}
      <div>
        <Link
          href="/candidate/jobs"
          className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold inline-flex items-center gap-1.5 transition"
        >
          <span>&larr;</span> Back to All Opportunities
        </Link>
        <div className="flex items-center gap-3 mt-2 flex-wrap">
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            {job.title}
          </h1>
          <span className="text-xs px-2.5 py-0.5 rounded-full font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
            ACTIVE
          </span>
        </div>
        <p className="text-sm text-slate-500 mt-1">
          <strong className="text-slate-800">{job.company_name}</strong> &bull;{" "}
          {job.work_location} &bull; {job.employment_type.replace("_", " ")}
        </p>
      </div>

      {/* Existing Application Status Banner */}
      {existingApp && (
        <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-sm">
          <div className="space-y-1">
            <span className="text-xs text-emerald-800 font-bold uppercase tracking-wider block">
              Application On File
            </span>
            <p className="text-sm text-slate-700">
              You applied for this position on{" "}
              <strong className="text-slate-900">{new Date(existingApp.applied_at).toLocaleDateString()}</strong>.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <span className="text-xs text-slate-600 font-medium">Current Status:</span>
            <span
              className={`text-xs px-3 py-1 rounded-full font-bold uppercase tracking-wider border ${
                existingApp.status === "SHORTLISTED"
                  ? "bg-emerald-100 text-emerald-800 border-emerald-300"
                  : existingApp.status === "REJECTED"
                  ? "bg-rose-100 text-rose-800 border-rose-300"
                  : existingApp.status === "UNDER_REVIEW"
                  ? "bg-amber-100 text-amber-800 border-amber-300"
                  : "bg-blue-100 text-blue-800 border-blue-300"
              }`}
            >
              {existingApp.status.replace("_", " ")}
            </span>
          </div>
        </div>
      )}

      {/* Success / Error Alerts */}
      {success && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm shadow-sm font-medium">
          {success}
        </div>
      )}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm shadow-sm">
          {error}
        </div>
      )}

      {/* Quick Summary Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 block mb-1">Employment</span>
          <span className="text-sm font-bold text-slate-900">
            {job.employment_type.replace("_", " ")}
          </span>
        </div>
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 block mb-1">Location</span>
          <span className="text-sm font-bold text-slate-900">
            {job.work_location}
          </span>
        </div>
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 block mb-1">Compensation</span>
          <span className="text-sm font-bold text-slate-900">
            {job.salary_min || job.salary_max
              ? `${job.salary_currency} ${
                  job.salary_min?.toLocaleString() ?? "0"
                } - ${job.salary_max?.toLocaleString() ?? "Open"}`
              : "Competitive"}
          </span>
        </div>
        <div className="p-4 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <span className="text-xs text-slate-500 block mb-1">Deadline</span>
          <span className="text-sm font-bold text-slate-900">
            {job.deadline
              ? new Date(job.deadline).toLocaleDateString()
              : "Ongoing"}
          </span>
        </div>
      </div>

      {/* Real-Time Skill-Gap & Readiness Analysis Section */}
      {skillGap && (
        <div className="p-6 rounded-2xl bg-white border border-emerald-200 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">
                  Intelligent Skill-Gap & Readiness Analysis
                </h2>
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Deterministic comparison of your profile competencies against this position&apos;s requirements.
              </p>
            </div>

            <div className="flex items-center gap-3">
              <span className="text-xs px-3 py-1 rounded-full font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                {skillGap.match_tier}
              </span>
              <div className="text-right">
                <span className="text-2xl font-black text-slate-900">
                  {Math.round(skillGap.coverage_percentage)}%
                </span>
                <span className="text-[11px] text-slate-500 block -mt-1 font-medium">
                  Skill Coverage
                </span>
              </div>
            </div>
          </div>

          {/* Progress Bar */}
          <div className="w-full bg-slate-100 rounded-full h-3 overflow-hidden p-0.5 border border-slate-200">
            <div
              className={`h-full rounded-full transition-all duration-700 ${
                skillGap.coverage_percentage >= 80
                  ? "bg-emerald-500"
                  : skillGap.coverage_percentage >= 50
                  ? "bg-emerald-400"
                  : "bg-amber-500"
              }`}
              style={{ width: `${Math.max(5, skillGap.coverage_percentage)}%` }}
            ></div>
          </div>

          {/* Skill Breakdown Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Matched Skills */}
            <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-200 space-y-2">
              <span className="text-xs font-bold text-emerald-800 block">
                &check; Verified Required Skills ({skillGap.matched_count} of {skillGap.total_required_count})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {skillGap.matched_skills.length > 0 ? (
                  skillGap.matched_skills.map((s, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-md text-xs font-medium bg-emerald-50 text-emerald-800 border border-emerald-200"
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-slate-500">No direct required matches found.</span>
                )}
              </div>
            </div>

            {/* Missing Skills */}
            <div className="p-4 rounded-xl bg-rose-50/50 border border-rose-200 space-y-2">
              <span className="text-xs font-bold text-rose-800 block">
                &times; Skills to Develop ({skillGap.missing_count})
              </span>
              <div className="flex flex-wrap gap-1.5">
                {skillGap.missing_skills.length > 0 ? (
                  skillGap.missing_skills.map((s, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-1 rounded-md text-xs font-medium bg-rose-50 text-rose-700 border border-rose-200"
                    >
                      {s}
                    </span>
                  ))
                ) : (
                  <span className="text-xs text-emerald-700 font-semibold">All listed requirements are covered!</span>
                )}
              </div>
            </div>
          </div>

          {/* Partial & Additional Skills */}
          {(skillGap.partial_skills.length > 0 || skillGap.additional_skills.length > 0) && (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {skillGap.partial_skills.length > 0 && (
                <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-2">
                  <span className="text-xs font-bold text-amber-900 block">
                    ⚡ Foundational / Partial Matches ({skillGap.partial_skills.length})
                  </span>
                  <div className="space-y-1.5 text-xs text-amber-800">
                    {skillGap.partial_skills.map((p, i) => (
                      <p key={i} className="text-xs leading-relaxed">
                        • {p.relationship}
                      </p>
                    ))}
                  </div>
                </div>
              )}

              {skillGap.additional_skills.length > 0 && (
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                  <span className="text-xs font-bold text-slate-800 block">
                    ★ Your Additional Strengths ({skillGap.additional_skills.length})
                  </span>
                  <div className="flex flex-wrap gap-1.5">
                    {skillGap.additional_skills.slice(0, 6).map((s, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 rounded-md text-xs font-medium bg-white text-slate-700 border border-slate-200 shadow-sm"
                      >
                        {s}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Actionable Learning Objectives & Roadmaps */}
          {skillGap.learning_recommendations.length > 0 && (
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between">
                <h3 className="text-xs font-bold uppercase tracking-wider text-slate-800">
                  Targeted Learning Roadmaps for this Role ({skillGap.learning_recommendations.length})
                </h3>
                <Link
                  href="/candidate/skill-gap"
                  className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold"
                >
                  View Full Upskilling Hub &rarr;
                </Link>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {skillGap.learning_recommendations.slice(0, 2).map((rec, i) => (
                  <div
                    key={i}
                    className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-slate-900">
                          {rec.skill_name}
                        </span>
                        <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-white border border-slate-200 text-slate-700">
                          {rec.difficulty.toUpperCase()}
                        </span>
                      </div>
                      <span
                        className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                          rec.priority === "HIGH"
                            ? "bg-rose-50 text-rose-700 border border-rose-200"
                            : "bg-amber-50 text-amber-700 border border-amber-200"
                        }`}
                      >
                        {rec.priority} PRIORITY
                      </span>
                    </div>

                    <p className="text-xs text-slate-600">{rec.note}</p>

                    <div>
                      <span className="text-[11px] font-bold text-slate-700 block mb-1">
                        Core Objectives:
                      </span>
                      <ul className="text-[11px] text-slate-600 space-y-1 list-disc list-inside">
                        {rec.core_concepts.slice(0, 2).map((c, j) => (
                          <li key={j}>{c}</li>
                        ))}
                      </ul>
                    </div>

                    {rec.documentation_links.length > 0 && (
                      <div className="pt-2 border-t border-slate-200 flex items-center justify-between text-xs">
                        <span className="text-slate-500 text-[11px]">
                          Est. ~{rec.estimated_hours}h
                        </span>
                        <a
                          href={rec.documentation_links[0].url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="text-emerald-600 hover:text-emerald-700 font-semibold inline-flex items-center gap-1"
                        >
                          Official Docs <span>&nearr;</span>
                        </a>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Advisory Notice */}
          <div className="p-3 rounded-xl bg-emerald-50 border border-emerald-200 text-[11px] text-emerald-800 flex items-start gap-2">
            <span className="text-emerald-600 font-bold shrink-0">ℹ</span>
            <span>{skillGap.advisory_note}</span>
          </div>
        </div>
      )}

      {/* Main Details Body */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Description & Skills */}
        <div className="lg:col-span-2 space-y-6">
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              Role Description
            </h2>
            <div className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">
              {job.description}
            </div>
          </div>

          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              Required Core Competencies
            </h2>
            <div className="flex flex-wrap gap-2">
              {skillsList.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Requirements & Application Submission Form */}
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-5">
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              Candidate Requirements
            </h2>

            <div>
              <span className="text-xs text-slate-500 block mb-1">
                Experience Level
              </span>
              <p className="text-sm font-semibold text-slate-800">
                {job.experience_years}
              </p>
            </div>

            <div className="pt-4 border-t border-slate-100">
              <span className="text-xs text-slate-500 block mb-1">
                Minimum Qualification
              </span>
              <p className="text-sm font-semibold text-slate-800">
                {job.qualification}
              </p>
            </div>
          </div>

          {/* Application Form Box */}
          {!existingApp ? (
            <form
              onSubmit={handleApply}
              className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4"
            >
              <h3 className="text-base font-bold text-slate-900 tracking-tight">
                Submit Your Application
              </h3>

              {/* Resume attachment status */}
              <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs">
                {resume ? (
                  <div className="flex items-center justify-between text-slate-700">
                    <span className="flex items-center gap-1.5 truncate">
                      <span className="h-2 w-2 rounded-full bg-emerald-500 shrink-0"></span>
                      Resume: <strong className="text-slate-900 truncate">{resume.original_filename}</strong>
                    </span>
                    <Link
                      href="/candidate/resume"
                      className="text-emerald-600 hover:text-emerald-700 font-semibold shrink-0 ml-2"
                    >
                      Change
                    </Link>
                  </div>
                ) : (
                  <div className="space-y-1">
                    <span className="text-amber-700 font-bold">
                      No resume uploaded
                    </span>
                    <p className="text-slate-500 text-[11px]">
                      We recommend uploading a PDF resume for automated parsing & matching.
                    </p>
                    <Link
                      href="/candidate/resume"
                      className="text-emerald-600 hover:text-emerald-700 text-xs font-semibold block pt-1"
                    >
                      Upload Resume &rarr;
                    </Link>
                  </div>
                )}
              </div>

              <div>
                <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                  Cover Letter / Note (Optional)
                </label>
                <textarea
                  rows={4}
                  placeholder="Introduce yourself and explain why you're a great fit for this role..."
                  value={coverLetter}
                  onChange={(e) => setCoverLetter(e.target.value)}
                  className="w-full px-3 py-2 rounded-xl bg-white border border-slate-200 text-xs text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 resize-y shadow-sm"
                ></textarea>
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white font-semibold text-xs transition disabled:opacity-50 cursor-pointer shadow-sm shadow-emerald-600/25"
              >
                {submitting ? "Submitting Application..." : "Apply For This Position"}
              </button>
            </form>
          ) : (
            <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm text-center space-y-3">
              <span className="text-xs text-emerald-700 font-bold block">
                &check; Application Submitted
              </span>
              <p className="text-xs text-slate-500">
                You have already applied for this position. The recruiter will review your profile and update your status.
              </p>
              <Link
                href="/candidate/applications"
                className="inline-block px-4 py-2 text-xs font-semibold rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 transition shadow-sm"
              >
                View in My Applications
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default function CandidateJobDetailsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500 font-medium">Loading opportunity details...</p>
        </div>
      }
    >
      <CandidateJobDetailsContent />
    </Suspense>
  );
}
