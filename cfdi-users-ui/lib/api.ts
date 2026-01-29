import { getApiBaseUrl } from "@/lib/env";

export type ApiError = {
  message: string;
  status?: number;
  details?: unknown;
};

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
      ...(options.headers ?? {}),
    },
    cache: "no-store",
  });

  const bodyText = await response.text();

  if (!response.ok) {
    let message = response.statusText;
    let details: unknown = undefined;
    if (bodyText) {
      try {
        const data = JSON.parse(bodyText) as {
          message?: string;
          detail?: string | unknown;
        };
        if (data?.message) message = data.message;
        if (data?.detail) {
          details = data.detail;
          if (typeof data.detail === "string") {
            message = data.detail;
          }
        }
      } catch {
        // ignore parse errors
      }
    }
    const error: ApiError = { message, status: response.status, details };
    throw error;
  }

  if (response.status === 204 || !bodyText) {
    return undefined as T;
  }

  return JSON.parse(bodyText) as T;
}
