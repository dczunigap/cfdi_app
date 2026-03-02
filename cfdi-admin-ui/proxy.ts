import { NextResponse, type NextRequest } from "next/server";
import { getAuthCookieName, getAuthCookieTtlSeconds } from "@/lib/env";

export function proxy(request: NextRequest) {
  const cookieName = getAuthCookieName();
  const auth = request.cookies.get(cookieName)?.value;
  if (!auth) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set("error", "unauthorized");
    return NextResponse.redirect(url);
  }

  const response = NextResponse.next();
  response.cookies.set(cookieName, auth, {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: getAuthCookieTtlSeconds(),
    secure: process.env.NODE_ENV === "production",
  });
  return response;
}

export const config = {
  matcher: [
    "/users/:path*",
    "/admin-sat/:path*",
    "/platform-rfcs/:path*",
    "/declaracion-config/:path*",
    "/rfc-users/:path*",
  ],
};
