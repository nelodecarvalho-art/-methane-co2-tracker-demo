export interface ReadingOut {
  time: string;
  sensor_id: string;
  gas_type: string;
  concentration_ppm: number;
  temperature_c: number | null;
  battery_pct: number | null;
  is_anomaly: boolean;
}

export interface AlertOut {
  id: number;
  sensor_id: string;
  gas_type: string;
  started_at: string;
  ended_at: string | null;
  max_ppm: number;
  status: string;
  notified_at: string | null;
}

export interface Page<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  role: string;
}

export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

export async function login(
  email: string,
  password: string,
  apiBaseUrl: string = API_BASE_URL,
): Promise<LoginResponse> {
  const url = new URL("/auth/login", apiBaseUrl);
  const response = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password }),
  });
  if (!response.ok) {
    throw new ApiError(response.status, `/auth/login -> HTTP ${response.status}`);
  }
  return (await response.json()) as LoginResponse;
}

export async function demoLogin(apiBaseUrl: string = API_BASE_URL): Promise<LoginResponse> {
  const url = new URL("/auth/demo-login", apiBaseUrl);
  const response = await fetch(url, { method: "POST" });
  if (!response.ok) {
    throw new ApiError(response.status, `/auth/demo-login -> HTTP ${response.status}`);
  }
  return (await response.json()) as LoginResponse;
}

async function apiGet<T>(
  apiBaseUrl: string,
  token: string,
  path: string,
  params?: Record<string, string | undefined>,
): Promise<T> {
  const url = new URL(path, apiBaseUrl);
  if (params) {
    for (const [key, value] of Object.entries(params)) {
      if (value) url.searchParams.set(key, value);
    }
  }

  const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) {
    throw new ApiError(response.status, `${path} -> HTTP ${response.status}`);
  }
  return (await response.json()) as T;
}

export function fetchReadings(
  token: string,
  params?: Record<string, string | undefined>,
  apiBaseUrl: string = API_BASE_URL,
): Promise<Page<ReadingOut>> {
  return apiGet<Page<ReadingOut>>(apiBaseUrl, token, "/readings", params);
}

export function fetchAlerts(
  token: string,
  params?: Record<string, string | undefined>,
  apiBaseUrl: string = API_BASE_URL,
): Promise<Page<AlertOut>> {
  return apiGet<Page<AlertOut>>(apiBaseUrl, token, "/alerts", params);
}

export async function fetchComplianceReportPdf(
  token: string,
  params: { start: string; end: string },
  apiBaseUrl: string = API_BASE_URL,
): Promise<Blob> {
  const url = new URL("/reports/compliance", apiBaseUrl);
  url.searchParams.set("start", params.start);
  url.searchParams.set("end", params.end);

  const response = await fetch(url, { headers: { Authorization: `Bearer ${token}` } });
  if (!response.ok) {
    throw new ApiError(response.status, `/reports/compliance -> HTTP ${response.status}`);
  }
  return response.blob();
}

export { API_BASE_URL };
