import { NextResponse } from "next/server";
import { getAuthCookieName } from "@/lib/env";
import { getServerApiBaseUrl } from "@/lib/env";

export async function POST(request: Request) {
  const body = await request.json().catch(() => null);
  if (!body || !body.email || !body.password) {
    return NextResponse.json({ message: "Credenciales requeridas." }, { status: 400 });
  }

  const apiBase = getServerApiBaseUrl();
  const response = await fetch(`${apiBase}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify(body),
  });

  const text = await response.text();
  if (!response.ok) {
    return NextResponse.json(
      { message: text || response.statusText },
      { status: response.status }
    );
  }

  const data = JSON.parse(text) as { access_token: string; expires_in: number };
  const cookieName = getAuthCookieName();
  const res = NextResponse.json({ ok: true });
  res.cookies.set(cookieName, data.access_token, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: data.expires_in,
    secure: process.env.NODE_ENV === "production",
  });
  return res;
}
