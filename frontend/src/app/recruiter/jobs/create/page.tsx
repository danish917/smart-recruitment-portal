"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { EmploymentType, JobStatus, createJob } from "@/lib/jobs";

export default function CreateJobPage() {
  const router = useRouter();
  const [title, setTitle] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [description, setDescription] = useState("");
  const [requiredSkills, setRequiredSkills] = useState("");
  const [qualification, setQualification] = useState("");
  const [experienceYears, setExperienceYears] = useState("");
  const [employmentType, setEmploymentType] = useState<EmploymentType>("FULL_TIME");
  const [workLocation, setWorkLocation] = useState("Remote");
  const [salaryMin, setSalaryMin] = useState<string>("");
  const [salaryMax, setSalaryMax] = useState<string>("");
  const [salaryCurrency, setSalaryCurrency] = useState("USD");
  const [deadline, setDeadline] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (targetStatus: JobStatus) => {
    setError(null);

    if (!title.trim() || !companyName.trim() || !description.trim()) {
      setError("Please fill in all required fields (Title, Company, Description).");
      return;
    }
    if (!requiredSkills.trim() || !qualification.trim() || !experienceYears.trim()) {
      setError("Please specify required skills, qualification, and experience.");
      return;
    }

    setLoading(true);
    try {
      const created = await createJob({
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
        status: targetStatus,
      });
      router.push(`/recruiter/jobs/${created.id}`);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to post job.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Page Title */}
      <div>
        <Link
          href="/recruiter/jobs"
          className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold inline-flex items-center gap-1.5 transition"
        >
          &larr; Back to all jobs
        </Link>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
          Post a New Job
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Create an active requisition for candidate applications or save as draft for team review.
        </p>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3 shadow-sm">
          <span className="h-2 w-2 rounded-full bg-rose-500 mt-1.5 shrink-0"></span>
          <div>
            <p className="font-semibold text-rose-900">Validation Error</p>
            <p className="text-xs text-rose-700 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {/* Form Container */}
      <form
        onSubmit={(e) => {
          e.preventDefault();
          handleSubmit("ACTIVE");
        }}
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
              placeholder="e.g. Senior Machine Learning Engineer"
              className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
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
              placeholder="e.g. Acme AI Corp"
              className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
            />
          </div>
        </div>

        {/* Location & Employment Type */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Work Location *
            </label>
            <input
              type="text"
              required
              value={workLocation}
              onChange={(e) => setWorkLocation(e.target.value)}
              placeholder="e.g. Remote, Hybrid - London, or On-site - NYC"
              className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Employment Type *
            </label>
            <select
              value={employmentType}
              onChange={(e) => setEmploymentType(e.target.value as EmploymentType)}
              className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
            >
              <option value="FULL_TIME">Full Time</option>
              <option value="PART_TIME">Part Time</option>
              <option value="CONTRACT">Contract</option>
              <option value="INTERNSHIP">Internship</option>
              <option value="REMOTE">Remote Contract</option>
            </select>
          </div>
        </div>

        {/* Experience & Qualification */}
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Experience Requirements *
            </label>
            <input
              type="text"
              required
              value={experienceYears}
              onChange={(e) => setExperienceYears(e.target.value)}
              placeholder="e.g. 3-5 years"
              className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
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
              placeholder="e.g. Bachelor's in CS or equivalent"
              className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
            />
          </div>
        </div>

        {/* Required Skills */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Required Skills * <span className="text-slate-400 lowercase">(comma-separated)</span>
          </label>
          <input
            type="text"
            required
            value={requiredSkills}
            onChange={(e) => setRequiredSkills(e.target.value)}
            placeholder="e.g. Python, FastAPI, PostgreSQL, Docker, Qdrant"
            className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
          />
        </div>

        {/* Compensation & Deadline */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Min Salary <span className="text-slate-400 lowercase">(optional)</span>
            </label>
            <input
              type="number"
              min="0"
              value={salaryMin}
              onChange={(e) => setSalaryMin(e.target.value)}
              placeholder="90000"
              className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Max Salary <span className="text-slate-400 lowercase">(optional)</span>
            </label>
            <input
              type="number"
              min="0"
              value={salaryMax}
              onChange={(e) => setSalaryMax(e.target.value)}
              placeholder="130000"
              className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
            />
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
              Application Deadline
            </label>
            <input
              type="date"
              value={deadline}
              onChange={(e) => setDeadline(e.target.value)}
              className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-200 text-slate-900 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
            />
          </div>
        </div>

        {/* Job Description */}
        <div>
          <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
            Job Description & Responsibilities *
          </label>
          <textarea
            required
            rows={6}
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Detailed overview of the role, day-to-day duties, team mission, and benefits..."
            className="w-full px-4 py-3 rounded-xl bg-white border border-slate-200 text-slate-900 placeholder-slate-400 text-sm focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 shadow-sm"
          ></textarea>
        </div>

        {/* Actions Bar */}
        <div className="pt-4 border-t border-slate-100 flex flex-wrap items-center justify-end gap-3">
          <Link
            href="/recruiter/jobs"
            className="px-5 py-2.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-200 text-slate-700 text-sm font-semibold transition shadow-sm"
          >
            Cancel
          </Link>
          <button
            type="button"
            disabled={loading}
            onClick={() => handleSubmit("DRAFT")}
            className="px-5 py-2.5 rounded-xl bg-white hover:bg-amber-50 text-amber-700 border border-amber-200 text-sm font-semibold transition cursor-pointer shadow-sm"
          >
            Save as Draft
          </button>
          <button
            type="submit"
            disabled={loading}
            className="px-6 py-2.5 rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white text-sm font-semibold shadow-sm shadow-emerald-600/20 transition cursor-pointer"
          >
            {loading ? "Publishing..." : "Publish Job Posting"}
          </button>
        </div>
      </form>
    </div>
  );
}
