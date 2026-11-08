"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  Job,
  JobStatus,
  archiveJob,
  deleteJob,
  fetchRecruiterJobs,
  publishJob,
} from "@/lib/jobs";

export default function RecruiterJobsPage() {
  const [jobs, setJobs] = useState<Job[]>([]);
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState<JobStatus | "ALL">("ALL");
  const [actionMessage, setActionMessage] = useState<string | null>(null);
  const [actionError, setActionError] = useState<string | null>(null);

  const loadJobs = async (filter: JobStatus | "ALL") => {
    setLoading(true);
    setActionError(null);
    try {
      const data = await fetchRecruiterJobs(
        filter === "ALL" ? undefined : filter
      );
      setJobs(data);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to load jobs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJobs(statusFilter);
  }, [statusFilter]);

  const handlePublish = async (jobId: number) => {
    try {
      await publishJob(jobId);
      setActionMessage(`Job #${jobId} published successfully.`);
      loadJobs(statusFilter);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to publish job.");
    }
  };

  const handleArchive = async (jobId: number) => {
    try {
      await archiveJob(jobId);
      setActionMessage(`Job #${jobId} archived.`);
      loadJobs(statusFilter);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to archive job.");
    }
  };

  const handleDelete = async (jobId: number) => {
    if (!confirm(`Are you sure you want to permanently delete job #${jobId}?`)) {
      return;
    }
    try {
      await deleteJob(jobId);
      setActionMessage(`Job #${jobId} deleted permanently.`);
      loadJobs(statusFilter);
    } catch (err: unknown) {
      setActionError(err instanceof Error ? err.message : "Failed to delete job.");
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Title & Post Button */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
            Job Requisitions
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Manage your organization&apos;s active openings, review drafts, and track applicants.
          </p>
        </div>
        <Link
          href="/recruiter/jobs/create"
          className="px-4 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold shadow-sm shadow-emerald-600/20 flex items-center gap-2 transition self-start sm:self-auto"
        >
          <span>+</span>
          <span>Post New Job</span>
        </Link>
      </div>

      {/* Notifications */}
      {actionMessage && (
        <div className="p-3.5 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between shadow-sm">
          <span>{actionMessage}</span>
          <button
            onClick={() => setActionMessage(null)}
            className="text-emerald-700 hover:text-emerald-900 font-bold ml-2 cursor-pointer"
          >
            &times;
          </button>
        </div>
      )}

      {actionError && (
        <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between shadow-sm">
          <span>{actionError}</span>
          <button
            onClick={() => setActionError(null)}
            className="text-rose-700 hover:text-rose-900 font-bold ml-2 cursor-pointer"
          >
            &times;
          </button>
        </div>
      )}

      {/* Filter Tabs */}
      <div className="flex items-center gap-2 border-b border-slate-200 pb-3 text-xs font-semibold">
        {(["ALL", "ACTIVE", "DRAFT", "ARCHIVED"] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setStatusFilter(tab)}
            className={`px-3.5 py-1.5 rounded-xl transition cursor-pointer ${
              statusFilter === tab
                ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/20"
                : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
            }`}
          >
            {tab}
          </button>
        ))}
      </div>

      {/* Job Table */}
      <div className="rounded-2xl bg-white border border-slate-200 overflow-hidden shadow-sm">
        {loading ? (
          <div className="flex flex-col items-center justify-center py-20 gap-3">
            <div className="h-7 w-7 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
            <p className="text-xs text-slate-500 font-medium">Loading postings...</p>
          </div>
        ) : jobs.length === 0 ? (
          <div className="py-16 text-center text-sm text-slate-500">
            <p>No job postings found matching &ldquo;{statusFilter}&rdquo;.</p>
            <Link
              href="/recruiter/jobs/create"
              className="mt-3 inline-block text-xs font-semibold text-emerald-600 hover:text-emerald-700 underline underline-offset-4"
            >
              Post a new job now &rarr;
            </Link>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="bg-slate-50 text-slate-500 text-xs uppercase tracking-wider border-b border-slate-200">
                <tr>
                  <th className="py-3.5 px-6">Job Title & Company</th>
                  <th className="py-3.5 px-6">Location</th>
                  <th className="py-3.5 px-6">Type</th>
                  <th className="py-3.5 px-6">Status</th>
                  <th className="py-3.5 px-6">Posted On</th>
                  <th className="py-3.5 px-6 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {jobs.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50/70 transition">
                    <td className="py-4 px-6">
                      <Link
                        href={`/recruiter/jobs/${job.id}`}
                        className="font-bold text-slate-900 hover:text-emerald-700 transition"
                      >
                        {job.title}
                      </Link>
                      <span className="block text-xs text-slate-500">
                        {job.company_name}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-slate-600 text-xs">
                      {job.work_location}
                    </td>
                    <td className="py-4 px-6 text-xs text-slate-600 font-mono">
                      {job.employment_type}
                    </td>
                    <td className="py-4 px-6">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${
                          job.status === "ACTIVE"
                            ? "bg-emerald-50 text-emerald-700 border border-emerald-200"
                            : job.status === "DRAFT"
                            ? "bg-amber-50 text-amber-700 border border-amber-200"
                            : "bg-slate-100 text-slate-600 border border-slate-200"
                        }`}
                      >
                        {job.status}
                      </span>
                    </td>
                    <td className="py-4 px-6 text-xs text-slate-500">
                      {new Date(job.created_at).toLocaleDateString()}
                    </td>
                    <td className="py-4 px-6 text-right space-x-2 text-xs">
                      <Link
                        href={`/recruiter/jobs/${job.id}/applications`}
                        className="text-emerald-700 hover:text-emerald-800 font-semibold"
                      >
                        Applicants
                      </Link>
                      <Link
                        href={`/recruiter/jobs/${job.id}`}
                        className="text-slate-600 hover:text-slate-900 font-medium"
                      >
                        View
                      </Link>
                      <Link
                        href={`/recruiter/jobs/${job.id}/edit`}
                        className="text-emerald-600 hover:text-emerald-700 font-medium"
                      >
                        Edit
                      </Link>

                      {job.status === "DRAFT" && (
                        <button
                          onClick={() => handlePublish(job.id)}
                          className="text-emerald-700 hover:text-emerald-800 font-semibold cursor-pointer"
                        >
                          Publish
                        </button>
                      )}

                      {job.status === "ACTIVE" && (
                        <button
                          onClick={() => handleArchive(job.id)}
                          className="text-amber-700 hover:text-amber-800 font-medium cursor-pointer"
                        >
                          Archive
                        </button>
                      )}

                      <button
                        onClick={() => handleDelete(job.id)}
                        className="text-rose-600 hover:text-rose-700 font-medium cursor-pointer"
                      >
                        Delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
