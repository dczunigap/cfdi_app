import { getApiBaseUrl, getApiToken } from "@/lib/env";

export type ApiError = {
  message: string;
  status?: number;
  details?: unknown;
};

function withDefaultHeaders(
  options: RequestInit,
  { setJsonContentType }: { setJsonContentType: boolean }
): Headers {
  const headers = new Headers(options.headers ?? {});
  if (setJsonContentType && !headers.has("Content-Type")) {
    headers.set("Content-Type", "application/json");
  }
  if (!headers.has("Accept")) {
    headers.set("Accept", "application/json");
  }
  const token = getApiToken();
  if (token && !headers.has("Authorization")) {
    headers.set("Authorization", `Bearer ${token}`);
  }
  return headers;
}

function parseApiError(response: Response, bodyText: string): ApiError {
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
  return { message, status: response.status, details };
}

async function requestApi<T>(
  path: string,
  options: RequestInit,
  { setJsonContentType }: { setJsonContentType: boolean }
): Promise<T> {
  const baseUrl = getApiBaseUrl();
  const headers = withDefaultHeaders(options, { setJsonContentType });

  const response = await fetch(`${baseUrl}${path}`, {
    ...options,
    headers,
    cache: "no-store",
  });

  const bodyText = await response.text();

  if (!response.ok) {
    throw parseApiError(response, bodyText);
  }

  if (response.status === 204 || !bodyText) {
    return undefined as T;
  }

  return JSON.parse(bodyText) as T;
}

export async function apiFetch<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  return requestApi<T>(path, options, { setJsonContentType: true });
}

export async function apiFetchForm<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  return requestApi<T>(path, options, { setJsonContentType: false });
}
