import type {
  Job,
  JobsResponse,
  RecommendationsResponse,
  SavedJobsResponse,
  UserPreferences,
  UserProfile,
} from "./types";
import { getAuthHeaders } from "./telegram";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000/api";

/** Thrown for backend errors; carries the HTTP status so callers (e.g. the
 * "onboarding required" 409 from /jobs/recommendations/) can branch on it. */
export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    headers: {
      "Content-Type": "application/json",
      // Identifies the caller to Django as the current Telegram user (or,
      // in local dev outside Telegram, a debug fallback id). See telegram.ts.
      ...getAuthHeaders(),
      ...options?.headers,
    },
    ...options,
  });

  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // response wasn't JSON — fall back to statusText
    }
    throw new ApiError(res.status, detail);
  }

  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

export const api = {
  getRecommendations(): Promise<RecommendationsResponse> {
    return request("/jobs/recommendations/");
  },

  getJobs(params?: { search?: string; job_type?: string; field?: string; location?: string }): Promise<JobsResponse> {
    const query = new URLSearchParams(
      Object.fromEntries(
        Object.entries(params ?? {}).filter(([, v]) => v !== undefined && v !== "")
      )
    ).toString();
    return request(`/jobs/${query ? `?${query}` : ""}`);
  },

  getJob(id: string | number): Promise<Job> {
    return request(`/jobs/${id}/`);
  },

  getSavedJobs(): Promise<SavedJobsResponse> {
    return request("/jobs/saved/");
  },

  saveJob(id: string | number): Promise<void> {
    return request(`/jobs/${id}/save/`, { method: "POST" });
  },

  unsaveJob(id: string | number): Promise<void> {
    return request(`/jobs/${id}/save/`, { method: "DELETE" });
  },

  getProfile(): Promise<UserProfile> {
    return request("/profile/");
  },

  updatePreferences(preferences: UserPreferences): Promise<UserProfile> {
    return request("/profile/preferences/", {
      method: "PUT",
      body: JSON.stringify(preferences),
    });
  },
};
