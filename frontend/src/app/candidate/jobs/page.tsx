"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { EmploymentType, Job } from "@/lib/jobs";
import {
  JobRecommendation,
  fetchActiveJobs,
  fetchRecommendedJobs,
} from "@/lib/candidate";

type ViewMode = "ALL" | "RECOMMENDED";

export default function CandidateJobsDiscoveryPage() {
  const [viewMode, setViewMode] = useState<ViewMode>("ALL");
  const [jobs, setJobs] = useState<Job[]>([]);
  const [recommendations, setRecommendations] = useState<JobRecommendation[]>([]);
  const [loading, setLoading] = useState(true);
  const [recsLoading, setRecsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [locationFilter, setLocationFilter] = useState("");
  const [employmentFilter, setEmploymentFilter] = useState<EmploymentType | "">("");

  const searchJobs = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchActiveJobs({
        q: searchQuery.trim() || undefined,
        location: locationFilter.trim() || undefined,
        employment_type: employmentFilter || undefined,
      });
      setJobs(data);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to search active jobs."
      );
    } finally {
      setLoading(false);
    }
  };

  const loadRecommendations = async () => {
    setRecsLoading(true);
    setError(null);
    try {
      const data = await fetchRecommendedJobs(15);
      setRecommendations(data);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load semantic job recommendations."
      );
    } finally {
      setRecsLoading(false);
    }
  };

  useEffect(() => {
    searchJobs();
  }, []);

  const handleTabChange = (mode: ViewMode) => {
    setViewMode(mode);
    setError(null);
    if (mode === "RECOMMENDED" && recommendations.length === 0) {
      loadRecommendations();
    }
  };

  const handleFilterSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    searchJobs();
  };

  const handleReset = () => {
    setSearchQuery("");
    setLocationFilter("");
    setEmploymentFilter("");
    fetchActiveJobs().then(setJobs).catch(() => {});
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
          Discover Career Opportunities
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Explore verified active job openings or discover AI-recommended roles powered by dense vector semantic matching.
        </p>
      </div>

      {/* Discovery Mode Switcher */}
      <div className="flex items-center gap-3 border-b border-slate-200 pb-3">
        <button
          onClick={() => handleTabChange("ALL")}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition cursor-pointer flex items-center gap-2 ${
            viewMode === "ALL"
              ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/20"
              : "text-slate-600 hover:text-slate-900 hover:bg-slate-100"
          }`}
        >
          <span>All Openings</span>
          <span className="text-[11px] opacity-80">({jobs.length})</span>
        </button>

        <button
          onClick={() => handleTabChange("RECOMMENDED")}
          className={`px-4 py-2 text-xs font-semibold rounded-xl transition cursor-pointer flex items-center gap-2 ${
            viewMode === "RECOMMENDED"
              ? "bg-emerald-600 text-white shadow-sm shadow-emerald-600/20"
              : "text-slate-600 hover:text-emerald-700 hover:bg-emerald-50"
          }`}
        >
          <span className="h-2 w-2 rounded-full bg-emerald-300 animate-pulse"></span>
          <span>Recommended for You (AI Semantic Match)</span>
        </button>
      </div>

      {/* Search & Filter Bar (Shown in "ALL" Mode) */}
      {viewMode === "ALL" && (
        <form
          onSubmit={handleFilterSubmit}
          className="p-5 rounded-2xl bg-white border border-slate-200 shadow-sm grid grid-cols-1 sm:grid-cols-4 gap-3.5"
        >
          <div className="sm:col-span-2">
            <input
              type="text"
              placeholder="Search by job title, company name, or skills..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>

          <div>
            <input
              type="text"
              placeholder="Location (e.g. Remote, Austin)"
              value={locationFilter}
              onChange={(e) => setLocationFilter(e.target.value)}
              className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            />
          </div>

          <div className="flex gap-2">
            <select
              value={employmentFilter}
              onChange={(e) => setEmploymentFilter(e.target.value as EmploymentType | "")}
              className="w-full px-3 py-2.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-700 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm"
            >
              <option value="">All Types</option>
              <option value="FULL_TIME">Full Time</option>
              <option value="PART_TIME">Part Time</option>
              <option value="CONTRACT">Contract</option>
              <option value="INTERNSHIP">Internship</option>
              <option value="REMOTE">Remote</option>
            </select>

            <button
              type="submit"
              className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition cursor-pointer shrink-0 shadow-sm shadow-emerald-600/20"
            >
              Filter
            </button>
            {(searchQuery || locationFilter || employmentFilter) && (
              <button
                type="button"
                onClick={handleReset}
                className="px-3 py-2.5 text-xs font-semibold rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition cursor-pointer shrink-0 shadow-sm"
                title="Reset Filters"
              >
                Reset
              </button>
            )}
          </div>
        </form>
      )}

      {/* Semantic Matching Info Banner (Shown in "RECOMMENDED" Mode) */}
      {viewMode === "RECOMMENDED" && (
        <div className="p-5 rounded-2xl bg-emerald-50 border border-emerald-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4 text-xs shadow-sm">
          <div>
            <p className="font-bold text-emerald-900 flex items-center gap-2 text-sm">
              <span>⚡</span> Dense Vector Candidate-to-Job Matching
            </p>
            <p className="text-emerald-700 mt-1 max-w-2xl leading-relaxed">
              These active job openings are ranked based on cosine similarity computed by Qdrant against your AI-parsed resume and skills taxonomy.
            </p>
          </div>
          <button
            onClick={loadRecommendations}
            disabled={recsLoading}
            className="px-3.5 py-1.5 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50 cursor-pointer self-start sm:self-auto shrink-0 shadow-sm shadow-emerald-600/20"
          >
            {recsLoading ? "Recomputing..." : "Refresh Recommendations"}
          </button>
        </div>
      )}

      {/* Error Alert */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm shadow-sm">
          <p className="font-semibold text-rose-900">Notice</p>
          <p className="text-xs text-rose-700 mt-0.5">{error}</p>
        </div>
      )}

      {/* Recommended Mode Listings */}
      {viewMode === "RECOMMENDED" && (
        <div>
          {recsLoading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-sm text-slate-500 font-medium">Computing dense vector semantic similarity...</p>
            </div>
          ) : recommendations.length === 0 ? (
            <div className="p-12 rounded-2xl bg-white border border-slate-200 text-center space-y-3 shadow-sm">
              <div className="h-12 w-12 rounded-2xl bg-emerald-50 border border-emerald-200 text-emerald-700 flex items-center justify-center mx-auto text-xl font-bold">
                🎯
              </div>
              <h2 className="text-base font-bold text-slate-900">No Semantic Matches Yet</h2>
              <p className="text-xs text-slate-500 max-w-md mx-auto">
                Please ensure you have uploaded and parsed your resume in the Resume Manager so our embedding engine can match you to active job requisitions.
              </p>
              <Link
                href="/candidate/resume"
                className="inline-block px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition mt-2 shadow-sm shadow-emerald-600/20"
              >
                Go to Resume Manager &rarr;
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {recommendations.map(({ job, similarity_score, match_tier }) => {
                const skillsList = job.required_skills
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean)
                  .slice(0, 5);

                return (
                  <div
                    key={job.id}
                    className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-emerald-300 hover:shadow-md transition flex flex-col md:flex-row md:items-center justify-between gap-5 group shadow-sm"
                  >
                    <div className="space-y-3 flex-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h3 className="text-base sm:text-lg font-bold text-slate-900 group-hover:text-emerald-700 transition">
                          {job.title}
                        </h3>

                        {/* Semantic Match Badge */}
                        <span className="text-xs px-3 py-0.5 rounded-full font-bold border bg-emerald-50 border-emerald-200 text-emerald-700">
                          {Math.round(similarity_score)}% &bull; {match_tier}
                        </span>

                        <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-slate-100 text-slate-600 border border-slate-200 font-semibold uppercase tracking-wider">
                          {job.employment_type.replace("_", " ")}
                        </span>
                      </div>

                      <p className="text-xs text-slate-500">
                        <strong className="text-slate-800">{job.company_name}</strong> &bull;{" "}
                        {job.work_location} &bull; Experience: {job.experience_years} &bull; Qualification: {job.qualification}
                      </p>

                      <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                        {job.description}
                      </p>

                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {skillsList.map((skill, idx) => (
                          <span
                            key={idx}
                            className="px-2.5 py-0.5 rounded-md bg-slate-50 text-slate-700 border border-slate-200 text-[11px] font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>

                    <div className="flex flex-row md:flex-col items-center md:items-end justify-between gap-3 pt-3 md:pt-0 border-t md:border-t-0 border-slate-100 shrink-0">
                      <div className="text-left md:text-right">
                        <span className="text-xs font-semibold text-slate-800 block">
                          {job.salary_min || job.salary_max
                            ? `${job.salary_currency} ${job.salary_min?.toLocaleString() ?? 0} - ${
                                job.salary_max?.toLocaleString() ?? "Open"
                              }`
                            : "Competitive"}
                        </span>
                        <span className="text-[11px] text-slate-500">
                          {job.deadline
                            ? `Closes ${new Date(job.deadline).toLocaleDateString()}`
                            : "Open Requisition"}
                        </span>
                      </div>

                      <Link
                        href={`/candidate/jobs/${job.id}`}
                        className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-sm shadow-emerald-600/20"
                      >
                        View & Apply &rarr;
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}

      {/* Standard "ALL" Mode Listings */}
      {viewMode === "ALL" && (
        <div>
          {loading ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
              <p className="text-sm text-slate-500 font-medium">Searching active opportunities...</p>
            </div>
          ) : jobs.length === 0 ? (
            <div className="p-12 rounded-2xl bg-white border border-slate-200 text-center space-y-3 shadow-sm">
              <h2 className="text-base font-bold text-slate-900">No Matching Jobs Found</h2>
              <p className="text-xs text-slate-500 max-w-sm mx-auto">
                Try broadening your search term or clearing location and employment type filters.
              </p>
            </div>
          ) : (
            <div className="grid grid-cols-1 gap-4">
              {jobs.map((job) => {
                const skillsList = job.required_skills
                  .split(",")
                  .map((s) => s.trim())
                  .filter(Boolean)
                  .slice(0, 5);

                return (
                  <div
                    key={job.id}
                    className="p-6 rounded-2xl bg-white border border-slate-200 hover:border-emerald-300 hover:shadow-md transition flex flex-col md:flex-row md:items-center justify-between gap-5 group shadow-sm"
                  >
                    <div className="space-y-3 flex-1">
                      <div className="flex items-center gap-3 flex-wrap">
                        <h3 className="text-base sm:text-lg font-bold text-slate-900 group-hover:text-emerald-700 transition">
                          {job.title}
                        </h3>
                        <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 font-semibold uppercase tracking-wider">
                          {job.employment_type.replace("_", " ")}
                        </span>
                      </div>

                      <p className="text-xs text-slate-500">
                        <strong className="text-slate-800">{job.company_name}</strong> &bull;{" "}
                        {job.work_location} &bull; Experience: {job.experience_years} &bull; Qualification: {job.qualification}
                      </p>

                      <p className="text-xs text-slate-600 line-clamp-2 leading-relaxed">
                        {job.description}
                      </p>

                      <div className="flex flex-wrap gap-1.5 pt-1">
                        {skillsList.map((skill, idx) => (
                          <span
                            key={idx}
                            className="px-2.5 py-0.5 rounded-md bg-slate-50 text-slate-700 border border-slate-200 text-[11px] font-medium"
                          >
                            {skill}
                          </span>
                        ))}
                        {job.required_skills.split(",").length > 5 && (
                          <span className="text-[11px] text-slate-500 self-center">
                            +{job.required_skills.split(",").length - 5} more
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex flex-row md:flex-col items-center md:items-end justify-between gap-3 pt-3 md:pt-0 border-t md:border-t-0 border-slate-100 shrink-0">
                      <div className="text-left md:text-right">
                        <span className="text-xs font-semibold text-slate-800 block">
                          {job.salary_min || job.salary_max
                            ? `${job.salary_currency} ${job.salary_min?.toLocaleString() ?? 0} - ${
                                job.salary_max?.toLocaleString() ?? "Open"
                              }`
                            : "Competitive"}
                        </span>
                        <span className="text-[11px] text-slate-500">
                          {job.deadline
                            ? `Closes ${new Date(job.deadline).toLocaleDateString()}`
                            : "Open Requisition"}
                        </span>
                      </div>

                      <Link
                        href={`/candidate/jobs/${job.id}`}
                        className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition shadow-sm shadow-emerald-600/20"
                      >
                        View Details & Apply &rarr;
                      </Link>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
