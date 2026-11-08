"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CandidateAnalyticsResponse,
  CandidateDashboardStats,
  JobApplication,
  JobRecommendation,
  ResumeMetadata,
  fetchCandidateAnalytics,
  fetchCandidateApplications,
  fetchCandidateStats,
  fetchRecommendedJobs,
  fetchResumeMetadata,
} from "@/lib/candidate";

export default function CandidateDashboardPage() {
  const [stats, setStats] = useState<CandidateDashboardStats | null>(null);
  const [analytics, setAnalytics] = useState<CandidateAnalyticsResponse | null>(null);
  const [resume, setResume] = useState<ResumeMetadata | null>(null);
  const [recommendedJobs, setRecommendedJobs] = useState<JobRecommendation[]>([]);
  const [recentApplications, setRecentApplications] = useState<JobApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const [statsData, analyticsData, resumeData, recsData, appsData] = await Promise.all([
          fetchCandidateStats().catch(() => null),
          fetchCandidateAnalytics().catch(() => null),
          fetchResumeMetadata().catch(() => null),
          fetchRecommendedJobs(3).catch(() => []),
          fetchCandidateApplications().catch(() => []),
        ]);
        setStats(statsData);
        setAnalytics(analyticsData);
        setResume(resumeData);
        setRecommendedJobs(recsData);
        setRecentApplications(appsData.slice(0, 5));
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load dashboard metrics.");
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="h-8 w-8 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm font-medium text-slate-500">Loading your candidate workspace...</p>
      </div>
    );
  }

  if (error || !stats) {
    return (
      <div className="p-6 rounded-2xl bg-white border border-rose-200 text-slate-800 shadow-sm">
        <div className="flex items-center gap-3 mb-2">
          <div className="h-8 w-8 rounded-full bg-rose-100 text-rose-600 flex items-center justify-center">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <h2 className="text-base font-bold text-slate-900">Dashboard Unavailable</h2>
        </div>
        <p className="text-sm text-slate-600 mb-4">{error || "Could not retrieve live metrics."}</p>
        <button
          onClick={() => window.location.reload()}
          className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  const totalApps = analytics?.total_applications ?? stats.total_applications;
  const underReview = analytics?.applications_under_review ?? stats.pending_applications;
  const shortlisted = analytics?.shortlisted_applications ?? stats.shortlisted_applications;
  const rejected = analytics?.rejected_applications ?? stats.rejected_applications;
  const parsedData = resume?.parsed_resume?.extracted_data;

  return (
    <div className="space-y-8">
      {/* 1. Welcome Section & 2. Profile Completion */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
              <span>Candidate Career Hub</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Welcome back to your Career Portal
            </h1>
            <p className="text-sm text-slate-500 max-w-xl">
              Track your live job applications, discover AI-recommended roles, and monitor verified skill progression.
            </p>
          </div>

          {/* Profile Completion Meter */}
          <div className="p-5 rounded-xl bg-slate-50 border border-slate-200 w-full lg:w-80 space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="font-semibold text-slate-700">Profile Completeness</span>
              <span className="font-bold text-emerald-600 font-mono text-sm">
                {stats.profile_completion_percentage}%
              </span>
            </div>
            <div className="w-full bg-slate-200 rounded-full h-2.5 overflow-hidden">
              <div
                className="bg-emerald-600 h-2.5 rounded-full transition-all duration-500"
                style={{ width: `${stats.profile_completion_percentage}%` }}
              ></div>
            </div>
            <div className="flex items-center justify-between text-xs text-slate-500 pt-1">
              <span>
                {stats.has_resume ? (
                  <span className="text-emerald-700 font-medium flex items-center gap-1">
                    <svg className="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                    </svg>
                    Resume Active
                  </span>
                ) : (
                  <span className="text-amber-600 font-medium">No resume attached</span>
                )}
              </span>
              <Link
                href="/candidate/profile"
                className="text-emerald-600 hover:text-emerald-700 font-semibold"
              >
                Edit Profile &rarr;
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* 6. Application Statistics Cards */}
      <div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Application Pipeline Statistics</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-500">Total Applied</span>
              <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
            <p className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">{totalApps}</p>
            <span className="text-xs text-slate-400 mt-1 block">Submitted applications</span>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-amber-700">Under Review</span>
              <div className="h-8 w-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <p className="text-2xl sm:text-3xl font-extrabold text-amber-600 font-mono">{underReview}</p>
            <span className="text-xs text-slate-400 mt-1 block">Awaiting recruiter review</span>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-emerald-700">Shortlisted</span>
              <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <p className="text-2xl sm:text-3xl font-extrabold text-emerald-600 font-mono">{shortlisted}</p>
            <span className="text-xs text-slate-400 mt-1 block">Shortlisted for interviews</span>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-500">Not Selected</span>
              <div className="h-8 w-8 rounded-lg bg-slate-100 text-slate-500 flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                </svg>
              </div>
            </div>
            <p className="text-2xl sm:text-3xl font-extrabold text-slate-700 font-mono">{rejected}</p>
            <span className="text-xs text-slate-400 mt-1 block">Closed applications</span>
          </div>
        </div>
      </div>

      {/* 3. Resume Upload & Resume Parsing Status Card */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Active Resume & NLP Parsing
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Parsed with rule-based heuristics & indexed in Qdrant for semantic matching
            </p>
          </div>
          <div className="flex items-center gap-2">
            <Link
              href="/candidate/resume"
              className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition"
            >
              {resume ? "Manage Resume" : "Upload Resume (PDF)"}
            </Link>
          </div>
        </div>

        {resume ? (
          <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center font-bold text-xs shrink-0">
                  PDF
                </div>
                <div>
                  <p className="text-sm font-semibold text-slate-800">{resume.original_filename}</p>
                  <p className="text-xs text-slate-500">
                    Size: {(resume.file_size / 1024).toFixed(1)} KB &bull; Uploaded: {new Date(resume.created_at).toLocaleDateString()}
                  </p>
                </div>
              </div>
              <span className="px-2.5 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200">
                Status: {resume.parsed_resume?.status || "PARSED"}
              </span>
            </div>

            {parsedData && (
              <div className="pt-3 border-t border-slate-200/60">
                <span className="text-xs font-semibold text-slate-700 block mb-2">Extracted Technical Skills:</span>
                <div className="flex flex-wrap gap-1.5">
                  {parsedData.technical_skills && parsedData.technical_skills.length > 0 ? (
                    parsedData.technical_skills.map((skill, idx) => (
                      <span
                        key={idx}
                        className="px-2.5 py-0.5 rounded-lg bg-emerald-50 text-emerald-800 border border-emerald-200/80 text-xs font-medium"
                      >
                        {skill}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-400">No skills detected.</span>
                  )}
                </div>
              </div>
            )}
          </div>
        ) : (
          <div className="p-6 rounded-xl bg-slate-50 border border-dashed border-slate-300 text-center space-y-3">
            <p className="text-sm text-slate-600">No active resume uploaded. Upload a PDF resume to unlock AI matching & screening.</p>
            <Link
              href="/candidate/resume"
              className="inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition"
            >
              Upload PDF Resume Now
            </Link>
          </div>
        )}
      </div>

      {/* 4. Recommended Jobs & 5. Available Jobs */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Recommended Jobs */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">AI Recommended Roles</h2>
                <p className="text-xs text-slate-500">Ranked by Qdrant dense vector similarity</p>
              </div>
              <Link href="/candidate/jobs" className="text-xs font-semibold text-emerald-600 hover:text-emerald-700">
                View All &rarr;
              </Link>
            </div>

            {recommendedJobs.length > 0 ? (
              <div className="space-y-3">
                {recommendedJobs.map((rec) => (
                  <div
                    key={rec.job.id}
                    className="p-4 rounded-xl border border-slate-200 hover:border-emerald-300 hover:bg-emerald-50/20 transition space-y-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <Link
                          href={`/candidate/jobs/${rec.job.id}`}
                          className="text-sm font-bold text-slate-900 hover:text-emerald-600 transition"
                        >
                          {rec.job.title}
                        </Link>
                        <p className="text-xs text-slate-500 mt-0.5">{rec.job.company_name} &bull; {rec.job.work_location || "Remote"}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 font-mono">
                        {rec.similarity_score}% match
                      </span>
                    </div>
                    <div className="flex items-center justify-between pt-1">
                      <span className="text-xs text-slate-500">{rec.job.employment_type}</span>
                      <Link
                        href={`/candidate/jobs/${rec.job.id}`}
                        className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
                      >
                        Inspect & Apply &rarr;
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                Upload your resume to receive AI semantic match recommendations.
              </div>
            )}
          </div>
        </div>

        {/* Available Jobs */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">Recent Opportunities</h2>
                <p className="text-xs text-slate-500">Active job postings open for application</p>
              </div>
              <Link href="/candidate/jobs" className="text-xs font-semibold text-emerald-600 hover:text-emerald-700">
                Explore Jobs &rarr;
              </Link>
            </div>

            {stats.recent_jobs && stats.recent_jobs.length > 0 ? (
              <div className="space-y-3">
                {stats.recent_jobs.slice(0, 3).map((job) => (
                  <div
                    key={job.id}
                    className="p-4 rounded-xl border border-slate-200 hover:border-slate-300 transition space-y-2"
                  >
                    <div className="flex items-start justify-between gap-2">
                      <div>
                        <Link
                          href={`/candidate/jobs/${job.id}`}
                          className="text-sm font-bold text-slate-900 hover:text-emerald-600 transition"
                        >
                          {job.title}
                        </Link>
                        <p className="text-xs text-slate-500 mt-0.5">{job.company_name} &bull; {job.work_location || "Remote"}</p>
                      </div>
                      <span className="px-2 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-700">
                        {job.employment_type}
                      </span>
                    </div>
                    <div className="flex items-center justify-between pt-1">
                      <span className="text-xs text-slate-500">
                        Required: {job.required_skills?.split(",").slice(0, 3).join(", ")}
                      </span>
                      <Link
                        href={`/candidate/jobs/${job.id}`}
                        className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
                      >
                        View &rarr;
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="p-8 text-center text-xs text-slate-500">
                No active jobs currently posted.
              </div>
            )}
          </div>
        </div>
      </div>

      {/* 8. Skill Coverage & 9. Skill-Gap Recommendations */}
      {analytics && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Skill Coverage Metric Card */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                Average Skill Coverage
              </h3>
              <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200">
                Deterministic Ratio
              </span>
            </div>
            <div className="text-4xl font-extrabold text-slate-900 mt-2 font-mono">
              {analytics.average_skill_coverage !== null ? `${analytics.average_skill_coverage}%` : "N/A"}
            </div>
            <div className="w-full bg-slate-100 rounded-full h-3 mt-3 overflow-hidden">
              <div
                className="bg-emerald-600 h-3 rounded-full transition-all duration-500"
                style={{ width: `${analytics.average_skill_coverage || 0}%` }}
              ></div>
            </div>
            <p className="text-xs text-slate-500 mt-3 leading-relaxed">
              Calculated as exact percentage of job requirements satisfied across all your submitted applications.
            </p>
          </div>

          {/* Skill-Gap Hub Quick Link */}
          <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
                  Intelligent Skill-Gap Roadmaps
                </h3>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200">
                  Advisory AI
                </span>
              </div>
              <p className="text-sm text-slate-600 mt-2 leading-relaxed">
                Discover your identified competency gaps, bridge precursor skills, and follow free, curated official study paths to maximize hiring match rates.
              </p>
            </div>
            <div className="mt-4 pt-4 border-t border-slate-100 flex items-center justify-between">
              <span className="text-xs text-slate-500">Actionable career guidance</span>
              <Link
                href="/candidate/skill-gap"
                className="px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-xs font-semibold shadow-sm transition"
              >
                Launch Skill-Gap Analysis &rarr;
              </Link>
            </div>
          </div>
        </div>
      )}

      {/* 7. Recent Applications & Their Statuses */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">Recent Applications</h2>
            <p className="text-xs text-slate-500">Track application progression and screening results</p>
          </div>
          <Link href="/candidate/applications" className="text-xs font-semibold text-emerald-600 hover:text-emerald-700">
            View All ({totalApps}) &rarr;
          </Link>
        </div>

        {recentApplications.length > 0 ? (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-3 px-4">Role & Company</th>
                  <th className="py-3 px-4">Applied Date</th>
                  <th className="py-3 px-4">Status</th>
                  <th className="py-3 px-4">Skill Match</th>
                  <th className="py-3 px-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {recentApplications.map((app) => (
                  <tr key={app.id} className="hover:bg-slate-50/80 transition">
                    <td className="py-3.5 px-4">
                      <p className="font-semibold text-slate-900">{app.job?.title || `Requisition #${app.job_id}`}</p>
                      <p className="text-xs text-slate-500">{app.job?.company_name || "Company"}</p>
                    </td>
                    <td className="py-3.5 px-4 text-xs text-slate-500 font-mono">
                      {new Date(app.applied_at).toLocaleDateString()}
                    </td>
                    <td className="py-3.5 px-4">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          app.status === "SHORTLISTED"
                            ? "bg-emerald-100 text-emerald-800"
                            : app.status === "UNDER_REVIEW"
                            ? "bg-amber-100 text-amber-800"
                            : app.status === "REJECTED"
                            ? "bg-slate-100 text-slate-600"
                            : "bg-blue-100 text-blue-800"
                        }`}
                      >
                        {app.status}
                      </span>
                    </td>
                    <td className="py-3.5 px-4 text-xs font-mono font-bold text-slate-700">
                      {app.screening?.skill_coverage !== undefined && app.screening?.skill_coverage !== null
                        ? `${app.screening.skill_coverage}%`
                        : "N/A"}
                    </td>
                    <td className="py-3.5 px-4 text-right">
                      <Link
                        href={`/candidate/jobs/${app.job_id}`}
                        className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
                      >
                        View Job &rarr;
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div className="p-8 text-center text-xs text-slate-500">
            No applications submitted yet. Browse jobs to begin applying.
          </div>
        )}
      </div>

      {/* 10. Candidate Analytics: Historical Progression */}
      {analytics && analytics.skill_progress_history && analytics.skill_progress_history.length > 0 && (
        <div id="analytics" className="bg-white rounded-2xl border border-slate-200 p-6 shadow-sm space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-bold text-slate-900 tracking-tight">Verified Qualification Progression</h2>
              <p className="text-xs text-slate-500">Historical performance across sequential job submissions</p>
            </div>
            <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono">
              {analytics.skill_progress_history.length} Record(s)
            </span>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-b border-slate-200">
                <tr>
                  <th className="py-2.5 px-4">Applied Role</th>
                  <th className="py-2.5 px-4">Date</th>
                  <th className="py-2.5 px-4">Skill Coverage</th>
                  <th className="py-2.5 px-4">Semantic Alignment</th>
                  <th className="py-2.5 px-4">Screening Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 font-mono text-xs">
                {analytics.skill_progress_history.map((pt, idx) => (
                  <tr key={idx} className="hover:bg-slate-50 transition">
                    <td className="py-3 px-4 font-sans font-medium text-slate-800">{pt.job_title}</td>
                    <td className="py-3 px-4 text-slate-500">{new Date(pt.applied_at).toLocaleDateString()}</td>
                    <td className="py-3 px-4 font-bold text-emerald-700">{pt.skill_coverage !== null ? `${pt.skill_coverage}%` : "—"}</td>
                    <td className="py-3 px-4 text-slate-700">{pt.semantic_score !== null ? `${pt.semantic_score}%` : "—"}</td>
                    <td className="py-3 px-4 text-slate-700">{pt.screening_score !== null ? `${pt.screening_score}/100` : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}
