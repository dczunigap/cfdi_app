import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getAuthCookieName, getServerApiBaseUrl } from "@/lib/env";

export async function GET() {
  const cookieStore = await cookies();
  const token = cookieStore.get(getAuthCookieName())?.value;
  if (!token) {
    return NextResponse.json({ message: "No autorizado" }, { status: 401 });
  }

  const apiBase = getServerApiBaseUrl();
  const response = await fetch(`${apiBase}/auth/me`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  const text = await response.text();
  if (!response.ok) {
    return NextResponse.json(
      { message: text || response.statusText },
      { status: response.status }
    );
  }
  return NextResponse.json(JSON.parse(text));
}
