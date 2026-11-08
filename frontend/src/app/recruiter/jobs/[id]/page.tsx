"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  Job,
  fetchJobDetails,
  publishJob,
  archiveJob,
  deleteJob,
} from "@/lib/jobs";

function JobDetailsContent() {
  const params = useParams();
  const router = useRouter();
  const jobId = Number(params?.id);

  const [job, setJob] = useState<Job | null>(null);
  const [loading, setLoading] = useState(true);
  const [actionLoading, setActionLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [feedback, setFeedback] = useState<{
    type: "success" | "error";
    message: string;
  } | null>(null);

  const loadJob = async () => {
    if (!jobId || isNaN(jobId)) {
      setError("Invalid Job ID.");
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchJobDetails(jobId);
      setJob(data);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load job details."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadJob();
  }, [jobId]);

  const handlePublish = async () => {
    if (!job) return;
    setActionLoading(true);
    setFeedback(null);
    try {
      const updated = await publishJob(job.id);
      setJob(updated);
      setFeedback({
        type: "success",
        message: "Job status has been successfully set to ACTIVE.",
      });
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        message:
          err instanceof Error ? err.message : "Failed to publish job.",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleArchive = async () => {
    if (!job) return;
    setActionLoading(true);
    setFeedback(null);
    try {
      const updated = await archiveJob(job.id);
      setJob(updated);
      setFeedback({
        type: "success",
        message: "Job has been archived and removed from public listings.",
      });
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        message:
          err instanceof Error ? err.message : "Failed to archive job.",
      });
    } finally {
      setActionLoading(false);
    }
  };

  const handleDelete = async () => {
    if (!job) return;
    const confirmed = window.confirm(
      `Are you sure you want to permanently delete "${job.title}"? This action cannot be undone.`
    );
    if (!confirmed) return;

    setActionLoading(true);
    setFeedback(null);
    try {
      await deleteJob(job.id);
      router.push("/recruiter/jobs");
    } catch (err: unknown) {
      setFeedback({
        type: "error",
        message: err instanceof Error ? err.message : "Failed to delete job.",
      });
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 font-medium">Loading job details...</p>
      </div>
    );
  }

  if (error || !job) {
    return (
      <div className="max-w-2xl mx-auto py-12 text-center space-y-4">
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm shadow-sm">
          <p className="font-semibold text-rose-900">Error Loading Job</p>
          <p className="mt-1">{error || "Job not found."}</p>
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

  const skillsList = job.required_skills
    .split(",")
    .map((s) => s.trim())
    .filter(Boolean);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Top Breadcrumb & Actions Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Link
            href="/recruiter/jobs"
            className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold inline-flex items-center gap-1.5 transition"
          >
            <span>&larr;</span> Back to all jobs
          </Link>
          <div className="flex items-center gap-3 mt-2 flex-wrap">
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              {job.title}
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
          </div>
          <p className="text-sm text-slate-500 mt-1">
            {job.company_name} &bull; {job.work_location} &bull;{" "}
            {job.employment_type.replace("_", " ")}
          </p>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2.5 flex-wrap">
          <Link
            href={`/recruiter/jobs/${job.id}/applications`}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-sm shadow-emerald-600/20"
          >
            View Applicants
          </Link>

          <Link
            href={`/recruiter/jobs/${job.id}/edit`}
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition shadow-sm"
          >
            Edit Job
          </Link>

          {job.status !== "ACTIVE" && (
            <button
              onClick={handlePublish}
              disabled={actionLoading}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50 cursor-pointer shadow-sm shadow-emerald-600/20"
            >
              Publish Job
            </button>
          )}

          {job.status === "ACTIVE" && (
            <button
              onClick={handleArchive}
              disabled={actionLoading}
              className="px-4 py-2 text-xs font-semibold rounded-xl bg-amber-600 hover:bg-amber-500 text-white transition disabled:opacity-50 cursor-pointer shadow-sm"
            >
              Archive Job
            </button>
          )}

          <button
            onClick={handleDelete}
            disabled={actionLoading}
            className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-white hover:bg-rose-50 border border-rose-200 text-rose-700 transition disabled:opacity-50 cursor-pointer shadow-sm"
            title="Delete this job"
          >
            Delete
          </button>
        </div>
      </div>

      {/* Feedback Alert */}
      {feedback && (
        <div
          className={`p-4 rounded-xl border text-sm flex items-start gap-2.5 shadow-sm ${
            feedback.type === "success"
              ? "bg-emerald-50 border-emerald-200 text-emerald-800"
              : "bg-rose-50 border-rose-200 text-rose-800"
          }`}
        >
          <span
            className={`h-2 w-2 rounded-full mt-1.5 shrink-0 ${
              feedback.type === "success" ? "bg-emerald-500" : "bg-rose-500"
            }`}
          ></span>
          <p className="font-medium">{feedback.message}</p>
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
              : "Not Specified"}
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

      {/* Main Details Body */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Description & Skills */}
        <div className="lg:col-span-2 space-y-6">
          {/* Job Description Card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              Job Description
            </h2>
            <div className="text-sm text-slate-600 leading-relaxed whitespace-pre-wrap">
              {job.description}
            </div>
          </div>

          {/* Required Skills Card */}
          <div className="p-6 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-4">
            <h2 className="text-base font-bold text-slate-900 tracking-tight">
              Required Skills
            </h2>
            <div className="flex flex-wrap gap-2">
              {skillsList.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-3 py-1 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200"
                >
                  {skill}
                </span>
              ))}
            </div>
          </div>
        </div>

        {/* Right: Qualifications & Metadata */}
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

          {/* Audit & System Info Card */}
          <div className="p-6 rounded-2xl bg-slate-50 border border-slate-200 text-xs text-slate-600 space-y-2.5 shadow-sm">
            <h3 className="font-bold text-slate-800 mb-3 text-xs uppercase tracking-wider">
              Posting Metadata
            </h3>
            <div className="flex justify-between">
              <span className="text-slate-500">Requisition ID:</span>
              <span className="font-mono text-slate-800 font-semibold">#{job.id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Owner ID:</span>
              <span className="font-mono text-slate-800 font-semibold">User #{job.recruiter_id}</span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Date Posted:</span>
              <span className="text-slate-800">
                {new Date(job.created_at).toLocaleDateString()}
              </span>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-500">Last Modified:</span>
              <span className="text-slate-800">
                {new Date(job.updated_at).toLocaleString()}
              </span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function JobDetailsPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500 font-medium">Loading job details...</p>
        </div>
      }
    >
      <JobDetailsContent />
    </Suspense>
  );
}
