"use client";

import { Suspense, useEffect, useState } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import { User, fetchUserProfile, logoutUser } from "@/lib/auth";

interface NavItem {
  label: string;
  href: string;
  icon: (active: boolean) => React.ReactNode;
}

function RecruiterLayoutInner({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  useEffect(() => {
    async function checkAuth() {
      try {
        const profile = await fetchUserProfile();
        if (profile.role !== "RECRUITER" && profile.role !== "ADMIN") {
          // Prevent recruiter layout from rendering for candidates
          router.replace("/candidate/dashboard");
          return;
        }
        setUser(profile);
      } catch {
        router.replace("/login");
      } finally {
        setLoading(false);
      }
    }
    checkAuth();
  }, [router]);

  const handleLogout = async () => {
    await logoutUser();
    router.replace("/login");
  };

  const navItems: NavItem[] = [
    {
      label: "Dashboard",
      href: "/recruiter/dashboard",
      icon: (active) => (
        <svg className={`w-5 h-5 ${active ? "text-emerald-600" : "text-slate-400 group-hover:text-slate-600"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
        </svg>
      ),
    },
    {
      label: "Manage Jobs",
      href: "/recruiter/jobs",
      icon: (active) => (
        <svg className={`w-5 h-5 ${active ? "text-emerald-600" : "text-slate-400 group-hover:text-slate-600"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
        </svg>
      ),
    },
    {
      label: "Post a Job",
      href: "/recruiter/jobs/create",
      icon: (active) => (
        <svg className={`w-5 h-5 ${active ? "text-emerald-600" : "text-slate-400 group-hover:text-slate-600"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 9v3m0 0v3m0-3h3m-3-3H9m12 0a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
    {
      label: "AI Screening",
      href: "/recruiter/dashboard#screening",
      icon: (active) => (
        <svg className={`w-5 h-5 ${active ? "text-emerald-600" : "text-slate-400 group-hover:text-slate-600"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
    },
    {
      label: "Analytics",
      href: "/recruiter/dashboard#analytics",
      icon: (active) => (
        <svg className={`w-5 h-5 ${active ? "text-emerald-600" : "text-slate-400 group-hover:text-slate-600"}`} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
  ];

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="h-8 w-8 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-sm font-medium text-slate-500">Loading Recruiter Workspace...</span>
        </div>
      </div>
    );
  }

  if (!user) return null;

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* Mobile Header */}
      <div className="md:hidden flex items-center justify-between bg-white border-b border-slate-200 px-4 py-3 sticky top-0 z-40">
        <div className="flex items-center gap-2.5">
          <div className="h-9 w-9 rounded-xl bg-emerald-600 flex items-center justify-center font-bold text-white shadow-sm">
            TS
          </div>
          <span className="font-bold text-lg text-slate-900">Talent<span className="text-emerald-600">Sync</span></span>
        </div>
        <button
          onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
          className="p-2 rounded-lg text-slate-600 hover:bg-slate-100"
        >
          <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d={mobileMenuOpen ? "M6 18L18 6M6 6l12 12" : "M4 6h16M4 12h16M4 18h16"} />
          </svg>
        </button>
      </div>

      {/* Sidebar Navigation */}
      <aside
        className={`${
          mobileMenuOpen ? "block" : "hidden"
        } md:block md:w-64 bg-white border-r border-slate-200 shrink-0 flex flex-col z-30 fixed md:sticky top-0 h-screen overflow-y-auto`}
      >
        {/* Brand */}
        <div className="p-6 border-b border-slate-100 hidden md:flex items-center gap-3">
          <div className="h-10 w-10 rounded-xl bg-emerald-600 flex items-center justify-center font-bold text-white shadow-md shadow-emerald-600/20">
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m4 6h.01M5 20h14a2 2 0 002-2V8a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
            </svg>
          </div>
          <div>
            <span className="font-bold text-lg tracking-tight text-slate-900 block leading-tight">
              Talent<span className="text-emerald-600">Sync</span>
            </span>
            <span className="text-[11px] font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded-full border border-emerald-200">
              Recruiter Hub
            </span>
          </div>
        </div>

        {/* Primary Action Button */}
        <div className="p-4">
          <Link
            href="/recruiter/jobs/create"
            onClick={() => setMobileMenuOpen(false)}
            className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-sm shadow-sm transition cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 4v16m8-8H4" />
            </svg>
            <span>Post a Job</span>
          </Link>
        </div>

        {/* Navigation Items */}
        <div className="px-4 pb-4 flex-1 space-y-1">
          {navItems.map((item) => {
            const active = pathname === item.href.split("#")[0];
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={() => setMobileMenuOpen(false)}
                className={`group flex items-center gap-3 px-3.5 py-2.5 rounded-xl text-sm font-semibold transition ${
                  active
                    ? "bg-emerald-50 text-emerald-800 shadow-xs border border-emerald-200/60"
                    : "text-slate-600 hover:text-slate-900 hover:bg-slate-50"
                }`}
              >
                {item.icon(active)}
                <span>{item.label}</span>
              </Link>
            );
          })}
        </div>

        {/* User Card & Logout */}
        <div className="p-4 border-t border-slate-100 bg-slate-50/50">
          <div className="flex items-center gap-3 mb-3">
            <div className="h-9 w-9 rounded-full bg-emerald-100 text-emerald-700 font-bold flex items-center justify-center text-xs shrink-0">
              {user.full_name?.charAt(0).toUpperCase() || "R"}
            </div>
            <div className="overflow-hidden flex-1">
              <p className="text-xs font-semibold text-slate-800 truncate">{user.full_name}</p>
              <p className="text-[11px] text-slate-500 truncate">{user.email}</p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-semibold text-slate-700 hover:text-rose-700 hover:bg-rose-50 border border-slate-200 hover:border-rose-200 transition cursor-pointer"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
            <span>Sign Out</span>
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-y-auto">
        <main className="flex-1 p-6 sm:p-8 max-w-7xl w-full mx-auto">
          {children}
        </main>
      </div>
    </div>
  );
}

export default function RecruiterLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <Suspense
      fallback={
        <div className="min-h-screen bg-slate-50 flex items-center justify-center">
          <div className="h-8 w-8 border-2 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        </div>
      }
    >
      <RecruiterLayoutInner>{children}</RecruiterLayoutInner>
    </Suspense>
  );
}
