import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getAuthCookieName, getServerApiBaseUrl } from "@/lib/env";

export async function POST() {
  const cookieStore = await cookies();
  const cookieName = getAuthCookieName();
  const token = cookieStore.get(cookieName)?.value;

  if (token) {
    const apiBase = getServerApiBaseUrl();
    await fetch(`${apiBase}/auth/logout`, {
      method: "POST",
      headers: { Authorization: `Bearer ${token}` },
    }).catch(() => null);
  }

  const res = NextResponse.json({ ok: true });
  res.cookies.set(cookieName, "", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  return res;
}
