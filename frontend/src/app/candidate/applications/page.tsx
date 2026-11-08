"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ApplicationStatus,
  JobApplication,
  fetchCandidateApplications,
} from "@/lib/candidate";

export default function CandidateApplicationsPage() {
  const [applications, setApplications] = useState<JobApplication[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [statusFilter, setStatusFilter] = useState<ApplicationStatus | "ALL">("ALL");

  useEffect(() => {
    async function loadApps() {
      try {
        const data = await fetchCandidateApplications();
        setApplications(data);
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load application history."
        );
      } finally {
        setLoading(false);
      }
    }
    loadApps();
  }, []);

  const filteredApps =
    statusFilter === "ALL"
      ? applications
      : applications.filter((a) => a.status === statusFilter);

  const getScoreBadge = (score: number) => {
    if (score >= 80) return "text-emerald-700 border-emerald-200 bg-emerald-50";
    if (score >= 60) return "text-emerald-800 border-emerald-200 bg-emerald-50";
    if (score >= 40) return "text-amber-800 border-amber-200 bg-amber-50";
    return "text-slate-600 border-slate-200 bg-slate-50";
  };

  return (
    <div className="space-y-8">
      {/* Header */}
      <div>
        <Link
          href="/candidate/dashboard"
          className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold inline-flex items-center gap-1.5 transition"
        >
          <span>&larr;</span> Back to Candidate Dashboard
        </Link>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
          My Job Applications
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Review your submission history, tracking statuses, and AI match advisory scores in real time.
        </p>
      </div>

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-3 overflow-x-auto text-xs">
        {(["ALL", "APPLIED", "UNDER_REVIEW", "SHORTLISTED", "REJECTED"] as const).map(
          (tab) => {
            const count =
              tab === "ALL"
                ? applications.length
                : applications.filter((a) => a.status === tab).length;

            return (
              <button
                key={tab}
                onClick={() => setStatusFilter(tab)}
                className={`px-3.5 py-2 rounded-xl font-semibold transition cursor-pointer shrink-0 ${
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

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm shadow-sm">
          <p className="font-semibold text-rose-900">Error</p>
          <p className="text-xs text-rose-700 mt-0.5">{error}</p>
        </div>
      )}

      {/* List / Table */}
      {loading ? (
        <div className="flex flex-col items-center justify-center py-20 gap-3">
          <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500 font-medium">Loading your applications...</p>
        </div>
      ) : filteredApps.length === 0 ? (
        <div className="p-12 rounded-2xl bg-white border border-slate-200 text-center space-y-3 shadow-sm">
          <h2 className="text-base font-bold text-slate-900">No Applications Found</h2>
          <p className="text-xs text-slate-500 max-w-sm mx-auto">
            {statusFilter === "ALL"
              ? "You haven't submitted any job applications yet. Browse active opportunities to get started."
              : `No applications with status ${statusFilter.replace("_", " ")}.`}
          </p>
          <Link
            href="/candidate/jobs"
            className="inline-block px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition mt-2 shadow-sm shadow-emerald-600/20"
          >
            Browse Open Jobs &rarr;
          </Link>
        </div>
      ) : (
        <div className="space-y-5">
          {filteredApps.map((app) => (
            <div
              key={app.id}
              className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-emerald-300 hover:shadow-md transition flex flex-col md:flex-row md:items-start justify-between gap-5 shadow-sm"
            >
              <div className="space-y-3 flex-1">
                <div className="flex items-center gap-3 flex-wrap">
                  <h3 className="text-base sm:text-lg font-bold text-slate-900">
                    {app.job?.title || `Job #${app.job_id}`}
                  </h3>
                  <span
                    className={`text-xs px-3 py-0.5 rounded-full font-bold uppercase tracking-wider border ${
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

                  {app.semantic_score !== null && app.semantic_score !== undefined && (
                    <span className="text-xs px-2.5 py-0.5 rounded-full font-bold border bg-emerald-50 border-emerald-200 text-emerald-800">
                      Semantic AI: {Math.round(app.semantic_score)}%
                    </span>
                  )}

                  {app.screening && (
                    <span
                      className={`text-xs px-3 py-0.5 rounded-full font-bold border ${getScoreBadge(
                        app.screening.screening_score
                      )}`}
                    >
                      Screening: {Math.round(app.screening.screening_score)}%
                    </span>
                  )}
                </div>

                <p className="text-xs text-slate-500">
                  <strong className="text-slate-800">{app.job?.company_name}</strong> &bull;{" "}
                  {app.job?.work_location} &bull; Type: {app.job?.employment_type.replace("_", " ")}
                </p>

                {app.cover_letter && (
                  <p className="text-xs text-slate-700 bg-slate-50 p-3 rounded-xl border border-slate-200 italic">
                    &ldquo;{app.cover_letter}&rdquo;
                  </p>
                )}

                {/* AI Screening Insights */}
                {app.screening && (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <div className="flex items-center justify-between text-xs">
                      <span className="font-bold text-slate-800">
                        AI Screening Advisory Breakdown:
                      </span>
                      <span className="text-[11px] text-slate-500">
                        Advisory only &bull; No automated rejection
                      </span>
                    </div>

                    {app.screening.matched_skills && app.screening.matched_skills.length > 0 && (
                      <div className="flex items-center gap-1.5 flex-wrap pt-1">
                        <span className="text-[11px] text-emerald-700 font-semibold mr-1">
                          Matched Skills:
                        </span>
                        {app.screening.matched_skills.map((skill, idx) => (
                          <span
                            key={idx}
                            className="px-2 py-0.5 text-[11px] rounded bg-emerald-50 border border-emerald-200 text-emerald-800 font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    )}

                    {app.screening.explanation && (
                      <p className="text-xs text-slate-600 line-clamp-2 pt-1 border-t border-slate-200">
                        {app.screening.explanation}
                      </p>
                    )}
                  </div>
                )}

                <div className="flex items-center gap-4 text-[11px] text-slate-500 pt-1">
                  <span>Applied on: {new Date(app.applied_at).toLocaleDateString()}</span>
                  {app.resume_id && (
                    <span className="text-emerald-700 font-semibold">&bull; Resume Attached</span>
                  )}
                  <span>Requisition #{app.job_id}</span>
                </div>
              </div>

              <div className="flex items-center gap-3 shrink-0 pt-3 md:pt-0 border-t md:border-t-0 border-slate-100">
                {app.job && (
                  <Link
                    href={`/candidate/jobs/${app.job.id}`}
                    className="px-4 py-2 text-xs font-semibold rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition shadow-sm"
                  >
                    View Job Details
                  </Link>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
