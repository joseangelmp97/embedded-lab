import { readAccessToken } from "@/lib/storage";

interface RequestOptions {
  method?: "GET" | "POST";
  body?: unknown;
  auth?: boolean;
}

interface ApiErrorPayload {
  detail?: string;
  error?: {
    message?: string;
    code?: string;
  };
}

export class ApiClientError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ApiClientError";
    this.status = status;
  }
}

export async function apiRequest<T>(path: string, options: RequestOptions = {}): Promise<T> {
  const headers: HeadersInit = {
    "Content-Type": "application/json"
  };

  if (options.auth) {
    const token = readAccessToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }

  const response = await fetch(path, {
    method: options.method ?? "GET",
    headers,
    body: options.body ? JSON.stringify(options.body) : undefined
  });

  if (!response.ok) {
    let message = "Unexpected API error";

    try {
      const payload = (await response.json()) as ApiErrorPayload;
      message = payload.error?.message ?? payload.detail ?? message;
    } catch {
      // Keep default message for non-JSON errors.
    }

    throw new ApiClientError(message, response.status);
  }

  return (await response.json()) as T;
}
