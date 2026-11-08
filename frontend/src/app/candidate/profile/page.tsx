"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  CandidateProfile,
  fetchCandidateProfile,
  updateCandidateProfile,
} from "@/lib/candidate";

export default function CandidateProfilePage() {
  const [profile, setProfile] = useState<CandidateProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  // Form states
  const [fullName, setFullName] = useState("");
  const [phoneNumber, setPhoneNumber] = useState("");
  const [education, setEducation] = useState("");
  const [collegeUniversity, setCollegeUniversity] = useState("");
  const [graduationYear, setGraduationYear] = useState<string>("");
  const [skills, setSkills] = useState("");
  const [experience, setExperience] = useState("");
  const [location, setLocation] = useState("");
  const [professionalSummary, setProfessionalSummary] = useState("");

  useEffect(() => {
    async function loadProfile() {
      try {
        const data = await fetchCandidateProfile();
        setProfile(data);
        setFullName(data.full_name || "");
        setPhoneNumber(data.phone_number || "");
        setEducation(data.education || "");
        setCollegeUniversity(data.college_university || "");
        setGraduationYear(data.graduation_year ? String(data.graduation_year) : "");
        setSkills(data.skills || "");
        setExperience(data.experience || "");
        setLocation(data.location || "");
        setProfessionalSummary(data.professional_summary || "");
      } catch (err: unknown) {
        setError(
          err instanceof Error ? err.message : "Failed to load candidate profile."
        );
      } finally {
        setLoading(false);
      }
    }
    loadProfile();
  }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);

    try {
      const updated = await updateCandidateProfile({
        full_name: fullName,
        phone_number: phoneNumber,
        education,
        college_university: collegeUniversity,
        graduation_year: graduationYear ? parseInt(graduationYear, 10) : null,
        skills,
        experience,
        location,
        professional_summary: professionalSummary,
      });
      setProfile(updated);
      setSuccess("Your candidate profile has been successfully updated.");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to update profile."
      );
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 font-medium">Loading your profile data...</p>
      </div>
    );
  }

  const skillList = skills
    ? skills.split(",").map((s) => s.trim()).filter(Boolean)
    : [];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <Link
            href="/candidate/dashboard"
            className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold inline-flex items-center gap-1.5 transition"
          >
            <span>&larr;</span> Back to Candidate Dashboard
          </Link>
          <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
            My Professional Profile
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Maintain your contact details, academic credentials, and core competencies for AI matching.
          </p>
        </div>

        {profile && (
          <div className="text-left sm:text-right text-xs text-slate-500 space-y-1 bg-white p-3 rounded-xl border border-slate-200 shadow-sm">
            <div>Profile ID: <span className="text-slate-900 font-mono font-semibold">#{profile.id}</span></div>
            <div>Last Updated: <span className="text-slate-900 font-medium">{new Date(profile.updated_at).toLocaleDateString()}</span></div>
          </div>
        )}
      </div>

      {/* Alerts */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3 shadow-sm">
          <span className="h-2 w-2 rounded-full bg-rose-500 mt-1.5 shrink-0"></span>
          <div>
            <p className="font-semibold text-rose-900">Error</p>
            <p className="text-xs text-rose-700 mt-0.5">{error}</p>
          </div>
        </div>
      )}

      {success && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-sm flex items-start gap-3 shadow-sm">
          <span className="h-2 w-2 rounded-full bg-emerald-500 mt-1.5 shrink-0"></span>
          <div>
            <p className="font-semibold text-emerald-900">Success</p>
            <p className="text-xs text-emerald-700 mt-0.5">{success}</p>
          </div>
        </div>
      )}

      {/* Profile Form */}
      <form
        onSubmit={handleSubmit}
        className="space-y-6 bg-white border border-slate-200 p-6 sm:p-8 rounded-2xl shadow-sm"
      >
        {/* Contact Info Section */}
        <div>
          <h2 className="text-base font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-600"></span>
            Personal & Contact Information
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Full Name *
              </label>
              <input
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm placeholder-slate-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Email Address
              </label>
              <input
                type="email"
                disabled
                value={profile?.email || ""}
                className="w-full px-3.5 py-2.5 rounded-xl bg-slate-50 border border-slate-200 text-sm text-slate-500 cursor-not-allowed shadow-sm"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Phone Number
              </label>
              <input
                type="tel"
                placeholder="+1 (555) 000-0000"
                value={phoneNumber}
                onChange={(e) => setPhoneNumber(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm placeholder-slate-400"
              />
            </div>
          </div>
        </div>

        {/* Location & Experience */}
        <div>
          <h2 className="text-base font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-600"></span>
            Location & Seniority
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Current Location
              </label>
              <input
                type="text"
                placeholder="e.g. San Francisco, CA or Remote"
                value={location}
                onChange={(e) => setLocation(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm placeholder-slate-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Experience Level
              </label>
              <input
                type="text"
                placeholder="e.g. 4+ Years, Senior Software Engineer"
                value={experience}
                onChange={(e) => setExperience(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm placeholder-slate-400"
              />
            </div>
          </div>
        </div>

        {/* Education Credentials */}
        <div>
          <h2 className="text-base font-bold text-slate-900 mb-4 pb-2 border-b border-slate-100 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-600"></span>
            Education & Academic Credentials
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Degree / Program
              </label>
              <input
                type="text"
                placeholder="e.g. B.S. in Computer Science"
                value={education}
                onChange={(e) => setEducation(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm placeholder-slate-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                College / University
              </label>
              <input
                type="text"
                placeholder="e.g. Stanford University"
                value={collegeUniversity}
                onChange={(e) => setCollegeUniversity(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm placeholder-slate-400"
              />
            </div>

            <div>
              <label className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2">
                Graduation Year
              </label>
              <input
                type="number"
                min="1960"
                max="2035"
                placeholder="e.g. 2024"
                value={graduationYear}
                onChange={(e) => setGraduationYear(e.target.value)}
                className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm placeholder-slate-400"
              />
            </div>
          </div>
        </div>

        {/* Skills */}
        <div>
          <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-600"></span>
            Technical & Professional Skills
          </h2>
          <p className="text-xs text-slate-500 mb-3">
            Provide skills separated by commas. These will be indexed by AI screening and matched against recruiter requisitions.
          </p>
          <input
            type="text"
            placeholder="e.g. Python, FastAPI, React, TypeScript, PostgreSQL, Docker, AWS"
            value={skills}
            onChange={(e) => setSkills(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition shadow-sm placeholder-slate-400"
          />

          {skillList.length > 0 && (
            <div className="mt-3 flex flex-wrap gap-1.5">
              {skillList.map((skill, idx) => (
                <span
                  key={idx}
                  className="px-2.5 py-1 rounded-lg bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-medium"
                >
                  {skill}
                </span>
              ))}
            </div>
          )}
        </div>

        {/* Professional Summary */}
        <div>
          <h2 className="text-base font-bold text-slate-900 mb-2 flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-600"></span>
            Professional Summary
          </h2>
          <textarea
            rows={4}
            placeholder="Brief overview of your professional career, key achievements, and role preferences..."
            value={professionalSummary}
            onChange={(e) => setProfessionalSummary(e.target.value)}
            className="w-full px-3.5 py-2.5 rounded-xl bg-white border border-slate-200 text-sm text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-emerald-500 transition resize-y shadow-sm"
          ></textarea>
        </div>

        {/* Action Buttons */}
        <div className="flex items-center justify-end gap-3 pt-5 border-t border-slate-100">
          <Link
            href="/candidate/dashboard"
            className="px-4 py-2.5 text-xs font-semibold rounded-xl bg-white border border-slate-200 text-slate-700 hover:bg-slate-50 transition shadow-sm"
          >
            Cancel
          </Link>
          <button
            type="submit"
            disabled={saving}
            className="px-6 py-2.5 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50 cursor-pointer shadow-sm shadow-emerald-600/20"
          >
            {saving ? "Saving Changes..." : "Save Profile"}
          </button>
        </div>
      </form>
    </div>
  );
}
