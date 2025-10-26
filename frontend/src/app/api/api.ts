import axios, { AxiosError } from 'axios';
import type {
  SearchRequest,
  TaskResponse,
  TaskStatusResponse,
  ErrorResponse
} from '@/types';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
const apiClient = axios.create({
  baseURL: API_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for logging
apiClient.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError<ErrorResponse>) => {
    if (error.response) {
      console.error('[API Error]', error.response.data);
    } else if (error.request) {
      console.error('[API Error] No response received', error.message);
    } else {
      console.error('[API Error]', error.message);
    }
    return Promise.reject(error);
  }
);

/**
 * Check API health
 */
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await apiClient.get('/health');
    return response.data.status === 'healthy';
  } catch (error) {
    console.error('Health check failed:', error);
    return false;
  }
}

/**
 * Create a new company search task
 */
export async function createSearchTask(
  request: SearchRequest
): Promise<TaskResponse> {
  try {
    const response = await apiClient.post<TaskResponse>('/api/search', request);
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Failed to create search task');
    }
    throw new Error('Failed to create search task');
  }
}

/**
 * Get task status
 */
export async function getTaskStatus(
  taskId: string
): Promise<TaskStatusResponse> {
  try {
    const response = await apiClient.get<TaskStatusResponse>(
      `/api/status/${taskId}`
    );
    return response.data;
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Failed to get task status');
    }
    throw new Error('Failed to get task status');
  }
}

/**
 * Cancel a task
 */
export async function cancelTask(taskId: string): Promise<void> {
  try {
    await apiClient.delete(`/api/task/${taskId}`);
  } catch (error) {
    if (axios.isAxiosError(error) && error.response) {
      throw new Error(error.response.data.detail || 'Failed to cancel task');
    }
    throw new Error('Failed to cancel task');
  }
}

/**
 * Poll task status until completion or failure
 */
export async function pollTaskStatus(
  taskId: string,
  onProgress?: (status: TaskStatusResponse) => void,
  maxAttempts: number = 40,
  interval: number = 3000
): Promise<TaskStatusResponse> {
  let attempts = 0;

  while (attempts < maxAttempts) {
    const status = await getTaskStatus(taskId);

    if (onProgress) {
      onProgress(status);
    }

    if (status.status === 'completed' || status.status === 'failed') {
      return status;
    }

    attempts++;
    await new Promise(resolve => setTimeout(resolve, interval));
  }

  throw new Error('Task polling timeout');
}
