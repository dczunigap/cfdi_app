export function getApiBaseUrl() {
  const baseUrl = process.env.NEXT_PUBLIC_API_BASE_URL;
  const resolved = (baseUrl || "/api/proxy").replace(/\/+$/, "");
  return resolved;
}

export function getApiToken() {
  return process.env.NEXT_PUBLIC_API_TOKEN || "";
}

export function getServerApiBaseUrl() {
  const baseUrl =
    process.env.API_BASE_URL || process.env.NEXT_PUBLIC_API_BASE_URL;
  if (!baseUrl) {
    throw new Error("API_BASE_URL is not configured.");
  }
  return baseUrl.replace(/\/+$/, "");
}

export function getAuthCookieName() {
  return process.env.AUTH_COOKIE_NAME || "cfdi_users_auth";
}

export function getAuthCookieTtlSeconds() {
  const raw = process.env.AUTH_COOKIE_TTL_SECONDS;
  const value = raw ? Number(raw) : 60 * 60 * 8;
  if (!Number.isFinite(value) || value <= 0) {
    return 60 * 60 * 8;
  }
  return Math.floor(value);
}

export function getAuthMode() {
  return process.env.AUTH_MODE || "local";
}

export function getAppTitle() {
  return process.env.APP_TITLE || "CFDI Admin";
}

export function getAppSubtitle() {
  return process.env.APP_SUBTITLE || "Administración de usuarios";
}
