/**
 * API type definitions matching backend schemas.
 */

export interface ApiError {
  type: string;
  title: string;
  status: number;
  detail: string;
  instance: string;
}

export interface ApiResponse<T> {
  success: boolean;
  data: T | null;
  error: ApiError | null;
}

export interface HealthData {
  status: string;
  database: boolean;
  redis: boolean;
}
