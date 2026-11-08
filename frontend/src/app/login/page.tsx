"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { loginUser, fetchUserProfile } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!email || !password) {
      setError("Please provide both email and password.");
      return;
    }

    setLoading(true);
    try {
      await loginUser({ email, password });
      // Fetch user profile to route directly to role dashboard
      const profile = await fetchUserProfile();
      if (profile.role === "RECRUITER" || profile.role === "ADMIN") {
        router.push("/recruiter/dashboard");
      } else {
        router.push("/candidate/dashboard");
      }
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to sign in.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col justify-center py-12 sm:px-6 lg:px-8">
      {/* Brand Header */}
      <div className="sm:mx-auto sm:w-full sm:max-w-md text-center">
        <Link href="/" className="inline-flex items-center gap-2.5 mb-6 group">
          <div className="h-11 w-11 rounded-xl bg-emerald-600 flex items-center justify-center font-bold text-white shadow-md shadow-emerald-600/20 group-hover:bg-emerald-700 transition">
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <span className="font-bold text-2xl tracking-tight text-slate-800">
            Talent<span className="text-emerald-600">Sync</span>
          </span>
        </Link>
        <h2 className="text-2xl font-bold tracking-tight text-slate-900">
          Welcome back
        </h2>
        <p className="mt-2 text-sm text-slate-500">
          Sign in to access your recruitment portal
        </p>
      </div>

      <div className="mt-8 sm:mx-auto sm:w-full sm:max-w-md px-4 sm:px-0">
        <div className="bg-white border border-slate-200 py-8 px-6 shadow-sm rounded-2xl sm:px-10">
          {error && (
            <div className="mb-6 p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-sm flex items-start gap-3">
              <svg className="w-5 h-5 text-rose-500 shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <div>
                <p className="font-semibold text-rose-800">Sign-in Error</p>
                <p className="text-xs mt-0.5 text-rose-600">{error}</p>
              </div>
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <label
                htmlFor="email"
                className="block text-xs font-semibold text-slate-700 uppercase tracking-wider mb-2"
              >
                Work or Personal Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="you@company.com"
                className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm transition shadow-sm"
              />
            </div>

            <div>
              <div className="flex justify-between items-center mb-2">
                <label
                  htmlFor="password"
                  className="block text-xs font-semibold text-slate-700 uppercase tracking-wider"
                >
                  Password
                </label>
              </div>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="••••••••"
                className="w-full px-4 py-2.5 rounded-xl bg-white border border-slate-300 text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent text-sm transition shadow-sm"
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 flex justify-center items-center py-2.5 px-4 rounded-xl shadow-sm text-sm font-semibold text-white bg-emerald-600 hover:bg-emerald-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-emerald-500 disabled:opacity-50 transition cursor-pointer"
            >
              {loading ? (
                <div className="flex items-center gap-2">
                  <div className="h-4 w-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                  <span>Authenticating...</span>
                </div>
              ) : (
                "Sign In"
              )}
            </button>
          </form>

          <div className="mt-6 pt-6 border-t border-slate-100 text-center">
            <p className="text-sm text-slate-500">
              Don&apos;t have an account?{" "}
              <Link
                href="/register"
                className="font-semibold text-emerald-600 hover:text-emerald-700 transition"
              >
                Create an account
              </Link>
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
