export interface Job {
  id: string | number;
  title: string;
  organization: string;
  location: string | null;
  country?: string | null;
  job_type: string | null;
  field: string | null;
  description: string;
  skills: string[];
  closing_date: string | null;
  published_date?: string | null;
  source: string;
  source_url: string;
  match_score?: number;
  match_reason?: string;
  match_factors?: { category: string; status: "match" | "unknown" | "different"; text: string }[];
  is_saved?: boolean;
}

export interface UserPreferences {
  job_types: string[];
  fields: string[];
  location_type: "cambodia" | "abroad";
  country?: string | null;
  onboarding_completed?: boolean;
}

export interface UserProfile {
  telegram_id?: string | number;
  first_name?: string;
  last_name?: string;
  username?: string;
  preferences: UserPreferences;
}

export interface RecommendationsResponse {
  results: Job[];
  count: number;
}

export interface JobsResponse {
  results: Job[];
  count: number;
  next: string | null;
  previous: string | null;
}

export interface SavedJobsResponse {
  results: Job[];
  count: number;
}
