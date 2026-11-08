"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  RecruiterAnalyticsResponse,
  fetchRecruiterAnalytics,
} from "@/lib/jobs";

export default function RecruiterDashboardPage() {
  const [analytics, setAnalytics] = useState<RecruiterAnalyticsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        const data = await fetchRecruiterAnalytics();
        setAnalytics(data);
      } catch (err: unknown) {
        setError(err instanceof Error ? err.message : "Failed to load recruiter analytics.");
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
        <p className="text-sm font-medium text-slate-500">Loading recruiter analytics & pipeline metrics...</p>
      </div>
    );
  }

  if (error || !analytics) {
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

  const dist = analytics.status_distribution;
  const totalApps = analytics.total_applications;

  // Percentage calculations for distribution bar
  const pctApplied = totalApps > 0 ? Math.round((dist.applied / totalApps) * 100) : 0;
  const pctReview = totalApps > 0 ? Math.round((dist.under_review / totalApps) * 100) : 0;
  const pctShortlisted = totalApps > 0 ? Math.round((dist.shortlisted / totalApps) * 100) : 0;
  const pctRejected = totalApps > 0 ? Math.round((dist.rejected / totalApps) * 100) : 0;

  return (
    <div className="space-y-8">
      {/* 1. Welcome Section & Prominent "Post a Job" Action */}
      <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs font-semibold">
              <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
              <span>Recruiter Management & Talent Hub</span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Recruitment Workspace & Pipeline
            </h1>
            <p className="text-sm text-slate-500 max-w-xl">
              Monitor active requisitions, evaluate AI screening results, and review inbound applicants in real time.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Link
              href="/recruiter/jobs/create"
              className="px-5 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold shadow-sm flex items-center gap-2 transition cursor-pointer"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
              </svg>
              <span>Post a Job</span>
            </Link>
            <Link
              href="/recruiter/jobs"
              className="px-4 py-2.5 rounded-xl bg-slate-50 hover:bg-slate-100 border border-slate-300 text-slate-700 text-sm font-semibold transition"
            >
              Manage Postings
            </Link>
          </div>
        </div>
      </div>

      {/* 2. Recruitment Statistics: 3. Active Jobs, 4. Total Apps, 5. Shortlisted, 6. Awaiting Review */}
      <div>
        <h2 className="text-xs font-bold uppercase tracking-wider text-slate-500 mb-3">Live Pipeline Performance</h2>
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-500">Active Postings</span>
              <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                </svg>
              </div>
            </div>
            <p className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
              {analytics.active_jobs}
            </p>
            <span className="text-xs text-slate-400 mt-1 block">
              {analytics.total_jobs} total requisitions ({analytics.draft_jobs} draft)
            </span>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-slate-500">Total Applications</span>
              <div className="h-8 w-8 rounded-lg bg-blue-50 text-blue-600 flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
            </div>
            <p className="text-2xl sm:text-3xl font-extrabold text-slate-900 font-mono">
              {totalApps}
            </p>
            <span className="text-xs text-slate-400 mt-1 block">Inbound candidate applications</span>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-emerald-700">Shortlisted Candidates</span>
              <div className="h-8 w-8 rounded-lg bg-emerald-50 text-emerald-600 flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M5 13l4 4L19 7" />
                </svg>
              </div>
            </div>
            <p className="text-2xl sm:text-3xl font-extrabold text-emerald-600 font-mono">
              {analytics.shortlisted_candidates}
            </p>
            <span className="text-xs text-slate-400 mt-1 block">High-potential candidate tier</span>
          </div>

          <div className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-semibold text-amber-700">Awaiting Review</span>
              <div className="h-8 w-8 rounded-lg bg-amber-50 text-amber-600 flex items-center justify-center">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
            <p className="text-2xl sm:text-3xl font-extrabold text-amber-600 font-mono">
              {analytics.applications_under_review + dist.applied}
            </p>
            <span className="text-xs text-slate-400 mt-1 block">Pending recruiter screening</span>
          </div>
        </div>
      </div>

      {/* 8. AI Screening Insights, 9. Semantic Matching Insights & Skill Coverage */}
      <div id="screening" className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Avg. AI Screening Score
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200">
              Rule-Based
            </span>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 mt-3 font-mono">
            {analytics.average_screening_score !== null ? `${analytics.average_screening_score}/100` : "N/A"}
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2.5 mt-3 overflow-hidden">
            <div
              className="bg-emerald-600 h-2.5 rounded-full transition-all duration-500"
              style={{ width: `${analytics.average_screening_score || 0}%` }}
            ></div>
          </div>
          <p className="text-xs text-slate-500 mt-2.5">
            Transparent composite across skills (40%), qualification (20%), and experience (20%).
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Avg. Skill Coverage
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200">
              Deterministic
            </span>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 mt-3 font-mono">
            {analytics.average_skill_coverage !== null ? `${analytics.average_skill_coverage}%` : "N/A"}
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2.5 mt-3 overflow-hidden">
            <div
              className="bg-emerald-500 h-2.5 rounded-full transition-all duration-500"
              style={{ width: `${analytics.average_skill_coverage || 0}%` }}
            ></div>
          </div>
          <p className="text-xs text-slate-500 mt-2.5">
            Exact mathematical ratio of required job skills satisfied by applicant resumes.
          </p>
        </div>

        <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-bold uppercase tracking-wider text-slate-500">
              Avg. Semantic Similarity
            </span>
            <span className="text-[11px] px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-semibold border border-emerald-200">
              Qdrant Dense
            </span>
          </div>
          <div className="text-3xl font-extrabold text-slate-900 mt-3 font-mono">
            {analytics.average_semantic_score !== null ? `${analytics.average_semantic_score}%` : "N/A"}
          </div>
          <div className="w-full bg-slate-100 rounded-full h-2.5 mt-3 overflow-hidden">
            <div
              className="bg-teal-500 h-2.5 rounded-full transition-all duration-500"
              style={{ width: `${analytics.average_semantic_score || 0}%` }}
            ></div>
          </div>
          <p className="text-xs text-slate-500 mt-2.5">
            Dense 384-dim FastEmbed vector alignment between candidates and role context.
          </p>
        </div>
      </div>

      {/* 10. Recruitment Analytics: Pipeline Distribution Progress Bar */}
      <div id="analytics" className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">Application Pipeline Stage Distribution</h2>
            <p className="text-xs text-slate-500">
              Breakdown across all {totalApps} candidate applications by current stage
            </p>
          </div>
          <span className="text-xs font-semibold px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-700 font-mono">
            {totalApps} Total Inbound
          </span>
        </div>

        {totalApps === 0 ? (
          <div className="py-8 text-center text-sm text-slate-500">
            No applications received yet. Publish job postings to start receiving candidates.
          </div>
        ) : (
          <div className="space-y-3">
            {/* Multi-segment Progress Bar */}
            <div className="h-3 w-full bg-slate-100 rounded-full flex overflow-hidden">
              <div
                style={{ width: `${pctShortlisted}%` }}
                className="bg-emerald-500 transition-all duration-500"
                title={`Shortlisted: ${dist.shortlisted} (${pctShortlisted}%)`}
              ></div>
              <div
                style={{ width: `${pctReview}%` }}
                className="bg-amber-400 transition-all duration-500"
                title={`Under Review: ${dist.under_review} (${pctReview}%)`}
              ></div>
              <div
                style={{ width: `${pctApplied}%` }}
                className="bg-blue-400 transition-all duration-500"
                title={`Applied: ${dist.applied} (${pctApplied}%)`}
              ></div>
              <div
                style={{ width: `${pctRejected}%` }}
                className="bg-slate-300 transition-all duration-500"
                title={`Rejected: ${dist.rejected} (${pctRejected}%)`}
              ></div>
            </div>

            {/* Legend */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 pt-2 text-xs">
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-emerald-500"></span>
                <span className="font-semibold text-slate-800">{dist.shortlisted}</span>
                <span className="text-slate-500">Shortlisted ({pctShortlisted}%)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-amber-400"></span>
                <span className="font-semibold text-slate-800">{dist.under_review}</span>
                <span className="text-slate-500">Under Review ({pctReview}%)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-blue-400"></span>
                <span className="font-semibold text-slate-800">{dist.applied}</span>
                <span className="text-slate-500">New Applied ({pctApplied}%)</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="h-2.5 w-2.5 rounded-full bg-slate-300"></span>
                <span className="font-semibold text-slate-800">{dist.rejected}</span>
                <span className="text-slate-500">Not Selected ({pctRejected}%)</span>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Two Column Layout: Top Requisitions & 7. Recent Applicants */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Requisitions (2 cols) */}
        <div className="lg:col-span-2 rounded-2xl bg-white border border-slate-200 shadow-sm overflow-hidden flex flex-col justify-between">
          <div>
            <div className="p-6 border-b border-slate-100 flex items-center justify-between">
              <div>
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">Active Requisitions by Applicant Volume</h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  Track applicant counts and candidate fit per posting
                </p>
              </div>
              <Link
                href="/recruiter/jobs"
                className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
              >
                All Jobs ({analytics.total_jobs}) &rarr;
              </Link>
            </div>

            {analytics.top_jobs.length === 0 ? (
              <div className="py-12 text-center text-sm text-slate-500">
                No job postings created yet.
              </div>
            ) : (
              <div className="overflow-x-auto">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 text-slate-600 text-xs uppercase font-semibold border-b border-slate-200">
                    <tr>
                      <th className="py-3 px-6">Requisition</th>
                      <th className="py-3 px-4 text-center">Applicants</th>
                      <th className="py-3 px-4 text-center">Shortlisted</th>
                      <th className="py-3 px-4 text-center">Avg. Skill Coverage</th>
                      <th className="py-3 px-6 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100">
                    {analytics.top_jobs.map((job) => (
                      <tr key={job.job_id} className="hover:bg-slate-50/80 transition">
                        <td className="py-3.5 px-6">
                          <Link
                            href={`/recruiter/jobs/${job.job_id}`}
                            className="font-semibold text-slate-900 hover:text-emerald-600 transition"
                          >
                            {job.job_title}
                          </Link>
                          <span className="block text-xs text-slate-500 mt-0.5">
                            {job.company_name} &bull;{" "}
                            <span className={job.status === "ACTIVE" ? "text-emerald-700 font-semibold" : "text-slate-500"}>
                              {job.status}
                            </span>
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-center font-mono font-bold text-slate-800">
                          {job.applicant_count}
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          <span className="px-2 py-0.5 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono">
                            {job.shortlisted_count}
                          </span>
                        </td>
                        <td className="py-3.5 px-4 text-center">
                          {job.average_skill_coverage !== null ? (
                            <span className="px-2 py-0.5 rounded-md text-xs font-bold bg-slate-100 text-slate-800 font-mono">
                              {job.average_skill_coverage}%
                            </span>
                          ) : (
                            <span className="text-xs text-slate-400">N/A</span>
                          )}
                        </td>
                        <td className="py-3.5 px-6 text-right">
                          <Link
                            href={`/recruiter/jobs/${job.job_id}/applications`}
                            className="text-xs font-semibold text-emerald-600 hover:text-emerald-700"
                          >
                            Review Applicants &rarr;
                          </Link>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>

        {/* 7. Recent Applicants & Recruitment Activity Feed (1 col) */}
        <div className="rounded-2xl bg-white border border-slate-200 shadow-sm p-6 space-y-4 flex flex-col justify-between">
          <div>
            <div className="flex items-center justify-between pb-3 border-b border-slate-100">
              <div>
                <h2 className="text-lg font-bold text-slate-900 tracking-tight">Recent Applicants</h2>
                <p className="text-xs text-slate-500">Live candidate activity stream</p>
              </div>
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-mono">
                {analytics.recent_activity.length} Event(s)
              </span>
            </div>

            {analytics.recent_activity.length === 0 ? (
              <div className="py-12 text-center text-xs text-slate-500">
                No recent applicant activity recorded yet.
              </div>
            ) : (
              <div className="space-y-3 pt-2">
                {analytics.recent_activity.map((item, idx) => (
                  <div key={idx} className="p-3.5 rounded-xl bg-slate-50 border border-slate-100 space-y-1.5">
                    <div className="flex items-start justify-between gap-2">
                      <p className="text-xs font-bold text-slate-900">{item.candidate_name}</p>
                      <span className="text-[10px] text-slate-400 font-mono">
                        {new Date(item.timestamp).toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}
                      </span>
                    </div>
                    <p className="text-xs text-slate-600">
                      Applied for <span className="font-semibold text-slate-800">{item.job_title}</span>
                    </p>
                    {item.metric_value !== null && item.metric_value !== undefined && (
                      <div className="flex items-center gap-1.5 pt-1 text-[11px] font-semibold text-emerald-700 font-mono">
                        <span>Match: {item.metric_value}%</span>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
