"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import {
  CandidateSkillGapSummary,
  SkillGapAnalysisReport,
  fetchActiveJobs,
  fetchCandidateSkillGapSummary,
  fetchJobSkillGap,
} from "@/lib/candidate";
import { Job } from "@/lib/jobs";

function CandidateSkillGapContent() {
  const [summary, setSummary] = useState<CandidateSkillGapSummary | null>(null);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [selectedJobId, setSelectedJobId] = useState<number | null>(null);
  const [jobReport, setJobReport] = useState<SkillGapAnalysisReport | null>(null);
  const [loading, setLoading] = useState(true);
  const [reportLoading, setReportLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadInitial() {
      setLoading(true);
      setError(null);
      try {
        const [sumData, activeJobs] = await Promise.all([
          fetchCandidateSkillGapSummary(),
          fetchActiveJobs(),
        ]);
        setSummary(sumData);
        setJobs(activeJobs);
        if (activeJobs.length > 0) {
          setSelectedJobId(activeJobs[0].id);
        }
      } catch (err: unknown) {
        setError(
          err instanceof Error
            ? err.message
            : "Failed to load skill-gap analysis data."
        );
      } finally {
        setLoading(false);
      }
    }
    loadInitial();
  }, []);

  useEffect(() => {
    async function evaluateJob(id: number) {
      setReportLoading(true);
      try {
        const report = await fetchJobSkillGap(id);
        setJobReport(report);
      } catch {
        setJobReport(null);
      } finally {
        setReportLoading(false);
      }
    }

    if (selectedJobId) {
      evaluateJob(selectedJobId);
    }
  }, [selectedJobId]);

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 font-medium">Loading skill-gap insights & learning roadmaps...</p>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Page Title & Navigation */}
      <div>
        <div className="flex items-center gap-2 text-xs text-emerald-600 font-semibold">
          <Link href="/candidate/dashboard" className="hover:text-emerald-700">
            Dashboard
          </Link>
          <span className="text-slate-400">/</span>
          <span className="text-slate-500">Skill-Gap Analysis & Upskilling</span>
        </div>
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mt-3">
          <div>
            <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight">
              Skill-Gap Analysis & Intelligent Recommendations
            </h1>
            <p className="text-sm text-slate-500 mt-1">
              Personalized competency diagnostics, market demand alignment, and curated official learning roadmaps.
            </p>
          </div>
          <Link
            href="/candidate/jobs"
            className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition self-start sm:self-auto shadow-sm shadow-emerald-600/20"
          >
            Explore Active Jobs &rarr;
          </Link>
        </div>
      </div>

      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm shadow-sm">
          {error}
        </div>
      )}

      {/* Section 1: Candidate Competency Overview Cards */}
      {summary && (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {/* Card 1: Detected Skills */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-1 shadow-sm">
            <span className="text-xs text-slate-500 font-medium">Your Profile Competencies</span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-slate-900">{summary.total_skills_detected}</span>
              <span className="text-xs text-emerald-600 font-semibold">Identified</span>
            </div>
            <p className="text-[11px] text-slate-500 pt-1">
              Extracted from your verified PDF resume and profile.
            </p>
          </div>

          {/* Card 2: Applications Analyzed */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-1 shadow-sm">
            <span className="text-xs text-slate-500 font-medium">Applications Analyzed</span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-slate-900">{summary.total_applications_analyzed}</span>
              <span className="text-xs text-slate-500">Submissions</span>
            </div>
            <p className="text-[11px] text-slate-500 pt-1">
              Cross-referenced against recruiter criteria.
            </p>
          </div>

          {/* Card 3: Average Coverage */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-1 shadow-sm">
            <span className="text-xs text-slate-500 font-medium">Average Market Coverage</span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-emerald-600">{summary.average_skill_coverage}%</span>
              <span className="text-xs text-emerald-600 font-semibold">Skill Match</span>
            </div>
            <p className="text-[11px] text-slate-500 pt-1">
              Average required skill overlap across applied jobs.
            </p>
          </div>

          {/* Card 4: Top Market Gaps */}
          <div className="p-5 rounded-2xl bg-white border border-slate-200 space-y-1 shadow-sm">
            <span className="text-xs text-slate-500 font-medium">Priority Growth Areas</span>
            <div className="flex items-baseline gap-2">
              <span className="text-3xl font-black text-amber-600">{summary.top_market_skill_gaps.length}</span>
              <span className="text-xs text-amber-600 font-semibold">Skills</span>
            </div>
            <p className="text-[11px] text-slate-500 pt-1">
              Top skills appearing on target jobs you lack.
            </p>
          </div>
        </div>
      )}

      {/* Section 2: Detected Skills Chips */}
      {summary && summary.detected_skills.length > 0 && (
        <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-3 shadow-sm">
          <div className="flex items-center justify-between">
            <h2 className="text-sm font-bold text-slate-900 uppercase tracking-wider">
              Your Current Technical & Professional Skills
            </h2>
            <Link
              href="/candidate/resume"
              className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold"
            >
              Update Resume &rarr;
            </Link>
          </div>
          <div className="flex flex-wrap gap-2">
            {summary.detected_skills.map((skill, idx) => (
              <span
                key={idx}
                className="px-3 py-1 rounded-lg text-xs font-semibold bg-emerald-50 text-emerald-800 border border-emerald-200"
              >
                {skill}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Section 3: Interactive Requisition Diagnostic Tool */}
      <div className="p-6 rounded-2xl bg-white border border-slate-200 space-y-6 shadow-sm">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <h2 className="text-lg font-bold text-slate-900 tracking-tight">
              Interactive Job Skill-Gap Evaluator
            </h2>
            <p className="text-xs text-slate-500 mt-0.5">
              Select any live opportunity to simulate requirement coverage and review tailor-made learning paths.
            </p>
          </div>

          {jobs.length > 0 && (
            <div className="flex items-center gap-2">
              <label htmlFor="jobSelect" className="text-xs text-slate-600 font-medium shrink-0">
                Target Role:
              </label>
              <select
                id="jobSelect"
                value={selectedJobId || ""}
                onChange={(e) => setSelectedJobId(Number(e.target.value))}
                className="px-3 py-1.5 rounded-xl bg-white border border-slate-200 text-xs text-slate-800 focus:outline-none focus:ring-2 focus:ring-emerald-500 shadow-sm"
              >
                {jobs.map((j) => (
                  <option key={j.id} value={j.id}>
                    {j.title} &mdash; {j.company_name}
                  </option>
                ))}
              </select>
            </div>
          )}
        </div>

        {reportLoading ? (
          <div className="py-12 text-center text-slate-500 text-xs">
            Evaluating skill competencies against selected position...
          </div>
        ) : jobReport ? (
          <div className="space-y-6 pt-2">
            {/* Coverage Summary Bar */}
            <div className="p-5 rounded-2xl bg-slate-50 border border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <h3 className="text-base font-bold text-slate-900">{jobReport.job_title}</h3>
                  <span className="text-[11px] px-2.5 py-0.5 rounded-full font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                    {jobReport.match_tier}
                  </span>
                </div>
                <p className="text-xs text-slate-600">{jobReport.strengths_summary}</p>
              </div>

              <div className="text-left sm:text-right shrink-0">
                <span className="text-3xl font-black text-slate-900">
                  {Math.round(jobReport.coverage_percentage)}%
                </span>
                <span className="text-xs text-slate-500 block -mt-1 font-medium">
                  Required Skill Coverage
                </span>
              </div>
            </div>

            {/* Matched vs Missing Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Matched Skills */}
              <div className="p-4 rounded-xl bg-emerald-50/50 border border-emerald-200 space-y-2">
                <span className="text-xs font-bold text-emerald-800 block">
                  &check; Verified Required Skills ({jobReport.matched_count} of {jobReport.total_required_count})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {jobReport.matched_skills.length > 0 ? (
                    jobReport.matched_skills.map((s, i) => (
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
                  &times; Skills to Develop ({jobReport.missing_count})
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {jobReport.missing_skills.length > 0 ? (
                    jobReport.missing_skills.map((s, i) => (
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
            {(jobReport.partial_skills.length > 0 || jobReport.additional_skills.length > 0) && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {jobReport.partial_skills.length > 0 && (
                  <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 space-y-2">
                    <span className="text-xs font-bold text-amber-900 block">
                      ⚡ Foundational / Partial Matches ({jobReport.partial_skills.length})
                    </span>
                    <div className="space-y-1.5 text-xs text-amber-800">
                      {jobReport.partial_skills.map((p, i) => (
                        <p key={i} className="text-xs leading-relaxed">
                          • {p.relationship}
                        </p>
                      ))}
                    </div>
                  </div>
                )}

                {jobReport.additional_skills.length > 0 && (
                  <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-2">
                    <span className="text-xs font-bold text-slate-800 block">
                      ★ Your Bonus Capabilities ({jobReport.additional_skills.length})
                    </span>
                    <div className="flex flex-wrap gap-1.5">
                      {jobReport.additional_skills.slice(0, 6).map((s, i) => (
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
          </div>
        ) : (
          <div className="py-8 text-center text-slate-500 text-xs">
            Select a job requisition to preview your skill gap analysis.
          </div>
        )}
      </div>

      {/* Section 4: Curated Learning Objectives & Reputable Official Resources */}
      <div className="space-y-4">
        <div>
          <h2 className="text-lg font-bold text-slate-900 tracking-tight">
            Curated Learning Objectives & Free Official Resources
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            Structured study paths, hands-on practice projects, and verified documentation to close skill gaps.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {(jobReport?.learning_recommendations?.length
            ? jobReport.learning_recommendations
            : summary?.recommended_learning_roadmaps || []
          ).map((plan, idx) => (
            <div
              key={idx}
              className="p-5 rounded-2xl bg-white border border-slate-200 hover:border-emerald-300 hover:shadow-md transition flex flex-col justify-between space-y-4 shadow-sm"
            >
              <div className="space-y-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <h3 className="text-base font-bold text-slate-900">{plan.skill_name}</h3>
                    <span className="text-[10px] px-2 py-0.5 rounded font-semibold bg-slate-100 text-slate-700">
                      {plan.difficulty.toUpperCase()}
                    </span>
                  </div>
                  <span
                    className={`text-[10px] px-2 py-0.5 rounded font-bold uppercase ${
                      plan.priority === "HIGH"
                        ? "bg-rose-50 text-rose-700 border border-rose-200"
                        : "bg-amber-50 text-amber-700 border border-amber-200"
                    }`}
                  >
                    {plan.priority}
                  </span>
                </div>

                <div className="flex items-center gap-2 text-xs text-slate-500">
                  <span>Category: <strong className="text-slate-700">{plan.category}</strong></span>
                  <span>&bull;</span>
                  <span>Est. ~{plan.estimated_hours}h</span>
                </div>

                {plan.note && (
                  <p className="text-xs text-slate-600 leading-relaxed">{plan.note}</p>
                )}

                {/* Core Concepts */}
                {plan.core_concepts && plan.core_concepts.length > 0 && (
                  <div className="space-y-1.5 pt-1">
                    <span className="text-xs font-bold text-slate-700 block">
                      Core Concepts:
                    </span>
                    <ul className="text-xs text-slate-600 space-y-1 list-disc list-inside">
                      {plan.core_concepts.slice(0, 3).map((concept, cIdx) => (
                        <li key={cIdx}>{concept}</li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Practice Project */}
                {plan.practice_project && (
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200 text-xs space-y-1">
                    <span className="font-bold text-emerald-800 block">
                      Hands-on Practice Project:
                    </span>
                    <p className="text-slate-600 text-[11px] leading-relaxed">
                      {plan.practice_project}
                    </p>
                  </div>
                )}
              </div>

              {/* Documentation Links */}
              {plan.documentation_links && plan.documentation_links.length > 0 && (
                <div className="pt-3 border-t border-slate-100 flex flex-wrap gap-2">
                  {plan.documentation_links.map((link, lIdx) => (
                    <a
                      key={lIdx}
                      href={link.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-white hover:bg-emerald-50 text-emerald-700 border border-slate-200 transition inline-flex items-center gap-1.5 shadow-sm"
                    >
                      <span>{link.title}</span>
                      <span>&nearr;</span>
                    </a>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Responsible AI Notice */}
      <div className="p-4 rounded-2xl bg-white border border-slate-200 text-xs text-slate-500 flex items-start gap-3 shadow-sm">
        <span className="text-emerald-600 text-base font-bold shrink-0">ℹ</span>
        <div className="space-y-1">
          <p className="font-bold text-slate-800">Responsible AI & Transparency Guarantee</p>
          <p className="leading-relaxed">
            All skill-gap calculations, coverage percentages, and learning recommendations are strictly advisory.
            They are designed to guide candidate professional growth and help recruiters identify applicant strengths.
            Candidates are never automatically disqualified or rejected based on automated skill gap algorithms.
          </p>
        </div>
      </div>
    </div>
  );
}

export default function CandidateSkillGapPage() {
  return (
    <Suspense
      fallback={
        <div className="flex flex-col items-center justify-center py-24 gap-3">
          <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
          <p className="text-sm text-slate-500 font-medium">Loading skill-gap hub...</p>
        </div>
      }
    >
      <CandidateSkillGapContent />
    </Suspense>
  );
}
