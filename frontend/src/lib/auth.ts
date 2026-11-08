/**
 * Authentication and API client utilities for Smart Recruitment Portal.
 */

export interface User {
  id: number;
  email: string;
  full_name: string;
  role: "CANDIDATE" | "RECRUITER" | "ADMIN";
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  user: User;
}

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "srp_access_token";
const USER_KEY = "srp_user_profile";

export function getStoredToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(TOKEN_KEY);
}

export function getStoredUser(): User | null {
  if (typeof window === "undefined") return null;
  const raw = localStorage.getItem(USER_KEY);
  if (!raw) return null;
  try {
    return JSON.parse(raw);
  } catch {
    return null;
  }
}

export function setSession(token: string, user: User): void {
  if (typeof window === "undefined") return;
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function clearSession(): void {
  if (typeof window === "undefined") return;
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

export async function registerUser(payload: {
  email: string;
  password: string;
  full_name: string;
  role: "CANDIDATE" | "RECRUITER";
}): Promise<User> {
  const res = await fetch(`${API_BASE_URL}/api/auth/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    const errorMsg =
      typeof data.detail === "string"
        ? data.detail
        : data.detail?.[0]?.msg || "Registration failed. Please check inputs.";
    throw new Error(errorMsg);
  }

  return data as User;
}

export async function loginUser(payload: {
  email: string;
  password: string;
}): Promise<TokenResponse> {
  const res = await fetch(`${API_BASE_URL}/api/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  const data = await res.json();
  if (!res.ok) {
    const errorMsg =
      typeof data.detail === "string"
        ? data.detail
        : data.detail?.[0]?.msg || "Authentication failed.";
    throw new Error(errorMsg);
  }

  const tokenResp = data as TokenResponse;
  setSession(tokenResp.access_token, tokenResp.user);
  return tokenResp;
}

export async function fetchUserProfile(): Promise<User> {
  const token = getStoredToken();
  if (!token) {
    throw new Error("No active session found.");
  }

  const res = await fetch(`${API_BASE_URL}/api/auth/me`, {
    method: "GET",
    headers: {
      Authorization: `Bearer ${token}`,
      "Content-Type": "application/json",
    },
  });

  const data = await res.json();
  if (!res.ok) {
    clearSession();
    throw new Error(data.detail || "Session expired. Please log in again.");
  }

  const user = data as User;
  if (typeof window !== "undefined") {
    localStorage.setItem(USER_KEY, JSON.stringify(user));
  }
  return user;
}

export async function logoutUser(): Promise<void> {
  try {
    await fetch(`${API_BASE_URL}/api/auth/logout`, { method: "POST" });
  } catch {
    // Ignore network error on logout
  } finally {
    clearSession();
  }
}
