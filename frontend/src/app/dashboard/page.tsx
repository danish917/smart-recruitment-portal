"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { fetchUserProfile } from "@/lib/auth";

export default function DashboardRedirectPage() {
  const router = useRouter();

  useEffect(() => {
    async function redirectRole() {
      try {
        const user = await fetchUserProfile();
        if (user.role === "RECRUITER" || user.role === "ADMIN") {
          router.replace("/recruiter/dashboard");
        } else if (user.role === "CANDIDATE") {
          router.replace("/candidate/dashboard");
        } else {
          router.replace("/login");
        }
      } catch {
        router.replace("/login");
      }
    }
    redirectRole();
  }, [router]);

  return (
    <div className="min-h-screen bg-slate-50 flex items-center justify-center">
      <div className="flex flex-col items-center gap-3">
        <div className="h-8 w-8 border-3 border-emerald-600 border-t-transparent rounded-full animate-spin"></div>
        <span className="text-sm font-medium text-slate-500">Directing to your workspace...</span>
      </div>
    </div>
  );
}
