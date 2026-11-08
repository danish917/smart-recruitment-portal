"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  EmploymentType,
  JobStatus,
  fetchJobDetails,
  updateJob,
} from "@/lib/jobs";

function EditJobContent() {
  const params = useParams();
  const router = useRouter();
  const jobId = Number(params?.id);

  const [initialLoading, setInitialLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form state
  const [title, setTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [description, setDescription] = useState("");
  const [requiredSkills, setRequiredSkills] = useState("");
  const [qualification, setQualification] = useState("");
  const [experienceYears, setExperienceYears] = useState("");
  const [employmentType, setEmploymentType] =
    useState<EmploymentType>("FULL_TIME");
  const [workLocation, setWorkLocation] = useState("");
  const [salaryMin, setSalaryMin] = useState<string>("");
  const [salaryMax, setSalaryMax] = useState<string>("");
  const [salaryCurrency, setSalaryCurrency] = useState("USD");
  const [deadline, setDeadline] = useState("");
  const [status, setStatus] = useState<JobStatus>("ACTIVE");

  useEffect(() => {
    async function loadInitial() {
      if (!jobId || isNaN(jobId)) {
        setError("Invalid Job ID.");
        setInitialLoading(false);
        return;
      }
      try {
        const job = await fetchJobDetails(jobId);
        setTitle(job.title);
        setCompanyName(job.company_name);
        setDescription(job.description);
        setRequiredSkills(job.required_skills);
        setQualification(job.qualification);
        setExperienceYears(job.experience_years);
        setEmploymentType(job.employment_type);
        setWorkLocation(job.work_location);
        setSalaryMin(job.salary_min != null ? String(job.salary_min) : "");
        setSalaryMax(job.salary_max != null ? String(job.salary_max) : "");
        setSalaryCurrency(job.salary_currency || "USD");
        if (job.deadline) {
          const d = new Date(job.deadline);
          const yyyy = d.getFullYear();
          const mm = String(d.getMonth() + 1).padStart(2, "0");
          const dd = String(d.getDate()).padStart(2, "0");
          setDeadline(`${yyyy}-${mm}-${dd}`);
        }
        setStatus(job.status);
      } catch (err: unknown) {
        setError(
          err instanceof Error ? err.message : "Failed to load job details."
        );
      } finally {
        setInitialLoading(false);
      }
    }
    loadInitial();
  }, [jobId]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!title.trim() || !companyName.trim() || !description.trim()) {
      setError("Please fill in all required fields (Title, Company, Description).");
      return;
    }
    if (!requiredSkills.trim() || !qualification.trim() || !experienceYears.trim()) {
      setError("Please specify required skills, qualification, and experience.");
      return;
    }

    setSubmitting(true);
    try {
      await updateJob(jobId, {
        title,
        company_name: companyName,
        description,
        required_skills: requiredSkills,
        qualification,
        experience_years: experienceYears,
        employment_type: employmentType,
        work_location: workLocation,
        salary_min: salaryMin ? parseFloat(salaryMin) : null,
        salary_max: salaryMax ? parseFloat(salaryMax) : null,
        salary_currency: salaryCurrency,
        deadline: deadline ? new Date(deadline).toISOString() : null,
        status,
      });
      router.push(`/recruiter/jobs/${jobId}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to update job.");
      setSubmitting(false);
    }
  };

  if (initialLoading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 font-medium">Loading job information...</p>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Header */}
      <div>
        <Link
          href={`/recruiter/jobs/${jobId}`}
          className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold inline-flex items-center gap-1.5 transition"
        >
          <span>&larr;</span> Back to job details
        </Link>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
          Edit Job Posting
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Update requisition requirements, status, or compensation details.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3 shadow-sm">
          <span className="h-2 w-2 rounded-full bg-rose-500 mt-1.5 shrink-0"></span>
          <div>
            <p className="font-semibold text-rose-900">Error</p>
            <p className="text-xs text-rose-700 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Form Container */}
      <form
        onSubmit={handleSubmit}
        className="space-y-6 bg-white border border-slate-200 p-6 sm:p-8 rounded-2xl shadow-sm"
      >
        {/* Core Info */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Job Title *
            </label>
            <input
              type="text"
              required
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Company Name *
            </label>
            <input
              type="text"
              required
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>
        </div>

        {/* Status & Work Details */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Lifecycle Status
            </label>
            <select
              value={status}
              onChange={(e) => setStatus(e.target.value as JobStatus)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            >
              <option value="ACTIVE">ACTIVE (Published)</option>
              <option value="DRAFT">DRAFT (Hidden)</option>
              <option value="ARCHIVED">ARCHIVED (Closed)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Employment Type
            </label>
            <select
              value={employmentType}
              onChange={(e) => setEmploymentType(e.target.value as EmploymentType)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            >
              <option value="FULL_TIME">Full-time</option>
              <option value="PART_TIME">Part-time</option>
              <option value="CONTRACT">Contract</option>
              <option value="INTERNSHIP">Internship</option>
              <option value="REMOTE">Remote</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Location *
            </label>
            <input
              type="text"
              required
              value={workLocation}
              onChange={(e) => setWorkLocation(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>
        </div>

        {/* Candidate Criteria */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Experience Level *
            </label>
            <input
              type="text"
              required
              value={experienceYears}
              onChange={(e) => setExperienceYears(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Minimum Qualification *
            </label>
            <input
              type="text"
              required
              value={qualification}
              onChange={(e) => setQualification(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>
        </div>

        {/* Skills */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Required Skills (comma-separated) *
          </label>
          <input
            type="text"
            required
            value={requiredSkills}
            onChange={(e) => setRequiredSkills(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
          />
        </div>

        {/* Job Description */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Job Description *
          </label>
          <textarea
            required
            rows={6}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition resize-y font-sans shadow-sm"
          ></textarea>
        </div>

        {/* Compensation & Deadline */}
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-5 pt-2 border-t border-slate-100">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Min Salary
            </label>
            <input
              type="number"
              min="0"
              value={salaryMin}
              onChange={(e) => setSalaryMin(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Max Salary
            </label>
            <input
              type="number"
              min="0"
              value={salaryMax}
              onChange={(e) => setSalaryMax(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Currency
            </label>
            <input
              type="text"
              value={salaryCurrency}
              onChange={(e) => setSalaryCurrency(e.target.value.toUpperCase())}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Deadline
            </label>
            <input
              type="date"
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>
        </div>

        {/* Buttons */}
        <div className="flex items-center justify-end gap-3 pt-4 border-t border-slate-100">
          <Link
            href={`/recruiter/jobs/${jobId}`}
            className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 transition shadow-sm"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={submitting}
            className="px-6 py-2.5 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50 cursor-pointer shadow-sm shadow-emerald-600/20"
          >
            {submitting ? "Saving Updates..." : "Save Changes"}
          </button>
        </div>
      </form>
    </div>
  );
}

export default function EditJobPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500 font-medium">Loading editor...</p>
        </div>
      }
    >
      <EditJobContent />
    </Suspense>
  );
}
