// API Response Types

export type TaskStatus =
  | 'pending'
  | 'started'
  | 'scraping'
  | 'processing'
  | 'completed'
  | 'failed'
  | 'timeout';

export interface CompanyInfo {
  legal_name: string | null;
  marketing_name: string | null;
  website: string | null;
  linkedin_url: string | null;
  facebook_url: string | null;
  employee_count: number | null;
  employee_range: string | null;
  industry: string | null;
  founded_year: number | null;
  headquarters: string | null;
  full_address: string | null;
  street_address: string | null;
  city: string | null;
  state: string | null;
  country: string | null;
  postal_code: string | null;
  seo_description: string | null;
  description: string | null;
  confidence_score: number | null;
  additional_data?: Record<string, any>;
  sources: string[];
}

export interface SearchRequest {
  query: string;
  include_website?: boolean;
  include_linkedin?: boolean;
  timeout?: number;
}

export interface TaskResponse {
  task_id: string;
  status: TaskStatus;
  message: string;
  created_at: string;
}

export interface TaskStatusResponse {
  task_id: string;
  status: TaskStatus;
  progress: number;
  message: string | null;
  result: CompanyInfo | null;
  error: string | null;
  created_at: string;
  started_at: string | null;
  completed_at: string | null;
  duration_seconds: number | null;
}

export interface ErrorResponse {
  error: string;
  detail: string;
  timestamp: string;
}
