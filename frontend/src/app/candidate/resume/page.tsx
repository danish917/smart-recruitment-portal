"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  ResumeMetadata,
  ParsedResume,
  deleteResumeFile,
  downloadResumeFile,
  fetchResumeMetadata,
  fetchParsedResume,
  reparseResume,
  indexResumeVector,
  uploadResumeFile,
} from "@/lib/candidate";

export default function ResumeManagerPage() {
  const [resume, setResume] = useState<ResumeMetadata | null>(null);
  const [parsedResume, setParsedResume] = useState<ParsedResume | null>(null);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [downloading, setDownloading] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [reparsing, setReparsing] = useState(false);
  const [indexingVector, setIndexingVector] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  const loadResume = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await fetchResumeMetadata();
      setResume(data);
      if (data) {
        // Also load parsed resume data if present
        const parsed = await fetchParsedResume().catch(() => null);
        setParsedResume(parsed || data.parsed_resume || null);
      } else {
        setParsedResume(null);
      }
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to load resume details."
      );
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadResume();
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setError(null);
    setSuccess(null);
    const file = e.target.files?.[0];
    if (!file) return;

    if (!file.name.toLowerCase().endsWith(".pdf")) {
      setError("Only PDF files (.pdf) are supported.");
      return;
    }
    if (file.size > 5 * 1024 * 1024) {
      setError("File exceeds 5 MB size limit.");
      return;
    }
    setSelectedFile(file);
  };

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    setSuccess(null);

    try {
      const metadata = await uploadResumeFile(selectedFile);
      setResume(metadata);
      setParsedResume(metadata.parsed_resume || null);
      setSelectedFile(null);
      setSuccess("Resume successfully uploaded and automatically parsed with AI.");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to upload resume."
      );
    } finally {
      setUploading(false);
    }
  };

  const handleDownload = async () => {
    setDownloading(true);
    setError(null);
    try {
      const blob = await downloadResumeFile();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = resume?.original_filename || "resume.pdf";
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to download resume file."
      );
    } finally {
      setDownloading(false);
    }
  };

  const handleDelete = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to permanently delete your resume? Active job applications will lose this attachment."
    );
    if (!confirmed) return;

    setDeleting(true);
    setError(null);
    setSuccess(null);
    try {
      await deleteResumeFile();
      setResume(null);
      setParsedResume(null);
      setSuccess("Resume has been deleted.");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to delete resume."
      );
    } finally {
      setDeleting(false);
    }
  };

  const handleReparse = async () => {
    setReparsing(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await reparseResume();
      setParsedResume(result);
      setSuccess("Resume successfully re-parsed by AI engine.");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to re-parse resume."
      );
    } finally {
      setReparsing(false);
    }
  };

  const handleIndexVector = async () => {
    setIndexingVector(true);
    setError(null);
    setSuccess(null);
    try {
      const result = await indexResumeVector();
      setParsedResume(result);
      setSuccess("Resume dense vector embedding successfully indexed in Qdrant Vector DB.");
    } catch (err: unknown) {
      setError(
        err instanceof Error ? err.message : "Failed to index resume vector in Qdrant."
      );
    } finally {
      setIndexingVector(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-24 gap-3">
        <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <p className="text-sm text-slate-500 font-medium">Loading resume status...</p>
      </div>
    );
  }

  const extracted = parsedResume?.extracted_data;

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <Link
          href="/candidate/dashboard"
          className="text-xs text-emerald-600 hover:text-emerald-700 font-semibold inline-flex items-center gap-1.5 transition"
        >
          <span>&larr;</span> Back to Candidate Dashboard
        </Link>
        <h1 className="text-2xl sm:text-3xl font-bold text-slate-900 tracking-tight mt-2">
          Resume & AI Parsing
        </h1>
        <p className="text-sm text-slate-500 mt-1">
          Upload and manage your primary PDF resume for AI parsing, intelligent matching, and 1-click applications.
        </p>
      </div>

      {/* Alerts */}
      {error && (
        <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-sm flex items-start gap-3 shadow-sm">
          <span className="h-2 w-2 rounded-full bg-rose-500 mt-1.5 shrink-0"></span>
          <div>
            <p className="font-semibold text-rose-900">Notice</p>
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

      {/* Active Resume Status Card */}
      {resume ? (
        <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="h-12 w-12 rounded-xl bg-emerald-50 text-emerald-700 flex items-center justify-center font-bold text-sm border border-emerald-200">
                PDF
              </div>
              <div>
                <h2 className="text-base font-bold text-slate-900">
                  {resume.original_filename}
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  {(resume.file_size / 1024).toFixed(1)} KB &bull; Uploaded on{" "}
                  {new Date(resume.created_at).toLocaleDateString()}
                </p>
              </div>
            </div>

            <div className="flex items-center gap-2.5">
              <button
                onClick={handleDownload}
                disabled={downloading}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50 cursor-pointer shadow-sm shadow-emerald-600/20"
              >
                {downloading ? "Downloading..." : "Download File"}
              </button>
              <button
                onClick={handleDelete}
                disabled={deleting}
                className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-white hover:bg-rose-50 border border-rose-200 text-rose-700 transition disabled:opacity-50 cursor-pointer"
              >
                {deleting ? "Deleting..." : "Delete"}
              </button>
            </div>
          </div>

          <div className="pt-4 border-t border-slate-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs text-slate-500">
            <span>Security Status: <strong className="text-emerald-700 font-semibold">Encrypted & Private Storage</strong></span>
            <span>Attached to all subsequent job applications</span>
          </div>
        </div>
      ) : (
        <div className="p-8 rounded-2xl bg-white border-2 border-dashed border-slate-200 text-center space-y-3 shadow-sm">
          <div className="h-12 w-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mx-auto text-xl font-bold">
            📄
          </div>
          <h2 className="text-base font-bold text-slate-900">
            No Resume Uploaded Yet
          </h2>
          <p className="text-xs text-slate-500 max-w-md mx-auto">
            Upload your professional resume in PDF format to enable AI extraction, skill-gap analysis, and 1-click applications.
          </p>
        </div>
      )}

      {/* AI Parsed Resume Intelligence Section */}
      {resume && (
        <div className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-6">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2.5 flex-wrap">
                <h2 className="text-base font-bold text-slate-900">
                  AI Parsed Data & Skills
                </h2>
                {parsedResume?.status === "PARSED" && (
                  <>
                    <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-50 border border-emerald-200 text-emerald-700">
                      Parsed
                    </span>
                    {parsedResume.is_indexed ? (
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-100 border border-emerald-300 text-emerald-800">
                        Qdrant Vector Indexed
                      </span>
                    ) : (
                      <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                        Vector Not Indexed
                      </span>
                    )}
                  </>
                )}
                {parsedResume?.status === "OCR_REQUIRED" && (
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-50 border border-amber-200 text-amber-700">
                    OCR Required
                  </span>
                )}
                {parsedResume?.status === "FAILED" && (
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-rose-50 border border-rose-200 text-rose-700">
                    Failed
                  </span>
                )}
                {(!parsedResume || parsedResume.status === "PENDING") && (
                  <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-slate-100 text-slate-600 border border-slate-200">
                    Pending
                  </span>
                )}
              </div>
              <p className="text-xs text-slate-500 mt-1">
                Extracted via transparent rule-based NLP. No demographic or protected characteristics are collected.
              </p>
            </div>

            <div className="flex items-center gap-2 self-start sm:self-auto flex-wrap">
              {parsedResume?.status === "PARSED" && !parsedResume.is_indexed && (
                <button
                  onClick={handleIndexVector}
                  disabled={indexingVector}
                  className="px-3.5 py-2 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-50 cursor-pointer shadow-sm shadow-emerald-600/20"
                >
                  {indexingVector ? "Indexing..." : "Index in Vector DB"}
                </button>
              )}

              <button
                onClick={handleReparse}
                disabled={reparsing}
                className="px-4 py-2 text-xs font-semibold rounded-xl bg-white hover:bg-slate-50 text-slate-700 border border-slate-200 transition disabled:opacity-50 cursor-pointer shadow-sm"
              >
                {reparsing ? "Re-parsing..." : "Re-parse Resume"}
              </button>
            </div>
          </div>

          {/* OCR Required Banner */}
          {parsedResume?.status === "OCR_REQUIRED" && (
            <div className="p-4 rounded-xl bg-amber-50 border border-amber-200 text-amber-800 text-xs space-y-1">
              <p className="font-semibold text-amber-900 flex items-center gap-2">
                <span>⚠️</span> Scanned or Image-Based PDF Detected
              </p>
              <p className="text-amber-700 leading-relaxed">
                Direct text extraction could not find standard text streams in this document. If this is a scanned document, please upload a digital text-based PDF to enable automated skill matching.
              </p>
            </div>
          )}

          {/* Failed Banner */}
          {parsedResume?.status === "FAILED" && (
            <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs space-y-1">
              <p className="font-semibold text-rose-900">Parsing Could Not Be Completed</p>
              <p className="text-rose-700 leading-relaxed">
                {parsedResume.error_message || "The file could not be parsed. Please check if the PDF is corrupted or password-protected."}
              </p>
            </div>
          )}

          {/* Parsed Attributes Grid */}
          {parsedResume?.status === "PARSED" && extracted && (
            <div className="space-y-6 pt-2">
              {/* Technical Skills */}
              <div className="space-y-2">
                <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                  Technical Skills ({extracted.technical_skills?.length || 0})
                </h3>
                {extracted.technical_skills && extracted.technical_skills.length > 0 ? (
                  <div className="flex flex-wrap gap-1.5">
                    {extracted.technical_skills.map((skill, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 text-xs rounded-lg bg-emerald-50 border border-emerald-200 text-emerald-800 font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                ) : (
                  <p className="text-xs text-slate-500 italic">No technical skills detected.</p>
                )}
              </div>

              {/* Soft Skills */}
              {extracted.soft_skills && extracted.soft_skills.length > 0 && (
                <div className="space-y-2">
                  <h3 className="text-xs font-bold text-slate-700 uppercase tracking-wider">
                    Soft Skills ({extracted.soft_skills.length})
                  </h3>
                  <div className="flex flex-wrap gap-1.5">
                    {extracted.soft_skills.map((skill, i) => (
                      <span
                        key={i}
                        className="px-2.5 py-1 text-xs rounded-lg bg-slate-50 text-slate-700 border border-slate-200 font-medium"
                      >
                        {skill}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* Education & Experience Details */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 pt-4 border-t border-slate-100">
                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    Education & Degree
                  </span>
                  <p className="text-xs text-slate-900 font-semibold">
                    {extracted.education || "Not specified in resume"}
                  </p>
                  <p className="text-xs text-slate-500">
                    {extracted.college_university || "University not detected"}
                    {extracted.graduation_year ? ` (${extracted.graduation_year})` : ""}
                  </p>
                </div>

                <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1">
                  <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                    Identified Experience
                  </span>
                  <p className="text-xs text-slate-900 font-semibold">
                    {extracted.experience_years
                      ? `${extracted.experience_years} years estimated`
                      : extracted.work_experience?.length
                      ? `${extracted.work_experience.length} roles found`
                      : "Not explicitly stated"}
                  </p>
                  <p className="text-xs text-slate-500">
                    {extracted.work_experience && extracted.work_experience.length > 0
                      ? extracted.work_experience.slice(0, 2).join(", ")
                      : "No roles detected"}
                  </p>
                </div>
              </div>

              {/* Projects & Certifications */}
              {(extracted.projects?.length > 0 || extracted.certifications?.length > 0) && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                  {extracted.projects?.length > 0 && (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                        Key Projects ({extracted.projects.length})
                      </span>
                      <ul className="text-xs text-slate-700 space-y-1 list-disc list-inside">
                        {extracted.projects.map((proj, idx) => (
                          <li key={idx} className="truncate">{proj}</li>
                        ))}
                      </ul>
                    </div>
                  )}

                  {extracted.certifications?.length > 0 && (
                    <div className="p-4 rounded-xl bg-slate-50 border border-slate-200 space-y-1.5">
                      <span className="text-[11px] font-bold text-slate-500 uppercase tracking-wider">
                        Certifications ({extracted.certifications.length})
                      </span>
                      <ul className="text-xs text-slate-700 space-y-1 list-disc list-inside">
                        {extracted.certifications.map((cert, idx) => (
                          <li key={idx} className="truncate">{cert}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Upload / Replace Form */}
      <form
        onSubmit={handleUpload}
        className="p-6 sm:p-8 rounded-2xl bg-white border border-slate-200 shadow-sm space-y-5"
      >
        <h2 className="text-base font-bold text-slate-900 tracking-tight">
          {resume ? "Replace Current Resume" : "Upload New Resume"}
        </h2>
        <p className="text-xs text-slate-500">
          Supported file format: <strong className="text-slate-700">.pdf</strong> (max 5 MB). Uploaded files are stored private and never indexed or accessible publicly without authentication.
        </p>

        <div className="flex flex-col sm:flex-row items-center gap-4">
          <input
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
            className="w-full text-xs text-slate-600 file:mr-4 file:py-2.5 file:px-4 file:rounded-xl file:border-0 file:text-xs file:font-semibold file:bg-emerald-50 file:text-emerald-700 hover:file:bg-emerald-100 cursor-pointer border border-slate-200 rounded-xl p-2 bg-white"
          />

          <button
            type="submit"
            disabled={!selectedFile || uploading}
            className="w-full sm:w-auto px-6 py-2.5 text-xs font-semibold rounded-xl bg-emerald-600 hover:bg-emerald-500 text-white transition disabled:opacity-40 cursor-pointer shrink-0 shadow-sm shadow-emerald-600/20"
          >
            {uploading ? "Uploading..." : resume ? "Replace Resume" : "Upload Resume"}
          </button>
        </div>

        {selectedFile && (
          <p className="text-xs text-emerald-700 font-medium">
            Selected: <span className="font-semibold">{selectedFile.name}</span> ({(selectedFile.size / 1024).toFixed(1)} KB)
          </p>
        )}
      </form>
    </div>
  );
}
