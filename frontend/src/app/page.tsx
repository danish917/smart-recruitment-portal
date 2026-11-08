"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { fetchUserProfile } from "@/lib/auth";

interface HealthResponse {
  status: string;
  service: string;
  version: string;
  database?: {
    status: string;
    engine: string;
    database?: string;
  };
}

export default function Home() {
  const router = useRouter();
  const [healthData, setHealthData] = useState<HealthResponse | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  useEffect(() => {
    async function checkAuthAndRedirect() {
      try {
        const user = await fetchUserProfile();
        if (user) {
          if (user.role === "RECRUITER" || user.role === "ADMIN") {
            router.replace("/recruiter/dashboard");
            return;
          } else {
            router.replace("/candidate/dashboard");
            return;
          }
        }
      } catch {
        // Unauthenticated - stay on public landing page
      } finally {
        setCheckingAuth(false);
      }
    }

    checkAuthAndRedirect();

    // Check backend health
    const apiBase = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";
    fetch(`${apiBase}/health`)
      .then((res) => (res.ok ? res.json() : null))
      .then((data) => setHealthData(data))
      .catch(() => {});
  }, [router]);

  if (checkingAuth) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="h-8 w-8 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col text-slate-800">
      {/* Top Navbar */}
      <header className="border-b border-slate-200 bg-white/90 backdrop-blur sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <div className="h-10 w-10 rounded-xl bg-emerald-600 flex items-center justify-center font-bold text-white shadow-md shadow-emerald-600/20">
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
            <span className="font-bold text-xl tracking-tight text-slate-900">
              Talent<span className="text-emerald-600">Sync</span>
            </span>
          </div>

          <div className="flex items-center gap-4">
            <Link
              href="/login"
              className="text-sm font-semibold text-slate-600 hover:text-slate-900 px-3 py-1.5 transition"
            >
              Sign In
            </Link>
            <Link
              href="/register"
              className="text-sm font-semibold px-4 py-2 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white shadow-sm transition"
            >
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <main className="flex-1">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-20 pb-16 text-center">
          <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200 mb-6">
            <span className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse"></span>
            AI-Driven Screening & Qdrant Semantic Matching
          </div>

          <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-slate-900 max-w-4xl mx-auto leading-tight">
            Smarter Talent Acquisition. <br className="hidden sm:inline" />
            <span className="text-emerald-600">Accelerated Career Growth.</span>
          </h1>

          <p className="mt-6 text-lg sm:text-xl text-slate-600 max-w-2xl mx-auto leading-relaxed">
            Connect high-impact candidates with verified requisitions using dense vector embeddings, explainable screening scores, and automated skill-gap roadmaps.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link
              href="/register"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-base shadow-sm transition cursor-pointer"
            >
              Create Free Account
            </Link>
            <Link
              href="/login"
              className="w-full sm:w-auto px-6 py-3.5 rounded-xl bg-white hover:bg-slate-50 border border-slate-300 text-slate-700 font-semibold text-base transition shadow-sm cursor-pointer"
            >
              Sign In to Portal
            </Link>
          </div>
        </div>

        {/* Feature Cards Grid */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Card 1 */}
            <div className="p-8 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md transition">
              <div className="h-12 w-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-6">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                Automated NLP Resume Parsing
              </h3>
              <p className="text-sm text-slate-500 leading-relaxed">
                Extract technical skills, soft skills, education tiers, and professional work history from PDF resumes with zero hallucinations.
              </p>
            </div>

            {/* Card 2 */}
            <div className="p-8 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md transition">
              <div className="h-12 w-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-6">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                Qdrant Semantic Matching
              </h3>
              <p className="text-sm text-slate-500 leading-relaxed">
                Matches candidate profiles with job requisitions using 384-dimensional dense embeddings and cosine similarity in Qdrant.
              </p>
            </div>

            {/* Card 3 */}
            <div className="p-8 rounded-2xl bg-white border border-slate-200 shadow-sm hover:shadow-md transition">
              <div className="h-12 w-12 rounded-xl bg-emerald-50 text-emerald-600 flex items-center justify-center mb-6">
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <h3 className="text-lg font-bold text-slate-900 mb-2">
                Skill-Gap & Learning Roadmaps
              </h3>
              <p className="text-sm text-slate-500 leading-relaxed">
                Identifies missing technical requirements with mathematical coverage calculation and generates curated, actionable study paths.
              </p>
            </div>
          </div>
        </div>

        {/* System Telemetry Banner */}
        {healthData && (
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pb-16">
            <div className="p-4 rounded-xl bg-white border border-slate-200 flex flex-wrap items-center justify-between gap-4 text-xs text-slate-600 shadow-sm">
              <div className="flex items-center gap-2">
                <span className="h-2 w-2 rounded-full bg-emerald-500"></span>
                <span>Service: <strong className="text-slate-800">{healthData.service}</strong> (v{healthData.version})</span>
              </div>
              <div className="flex items-center gap-4">
                <span>Database: <strong className="text-slate-800">{healthData.database?.engine}</strong> ({healthData.database?.status})</span>
                <span>Storage: <strong className="text-slate-800">Secure Object Storage</strong></span>
              </div>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-200 bg-white py-8 text-center text-xs text-slate-500">
        <p>&copy; {new Date().getFullYear()} TalentSync Recruitment Platform. Powered by Neon PostgreSQL & FastAPI.</p>
      </footer>
    </div>
  );
}
