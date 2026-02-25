import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import { getAuthCookieName, getServerApiBaseUrl } from "@/lib/env";

async function forward(
  request: Request,
  params: Promise<{ path?: string[] }>
) {
  const resolved = await params;
  const apiBase = getServerApiBaseUrl();
  const path = resolved.path?.join("/") ?? "";
  const incomingUrl = new URL(request.url);
  const url = `${apiBase}/${path}${incomingUrl.search}`;

  const incomingHeaders = new Headers(request.headers);
  incomingHeaders.delete("host");

  const cookieStore = await cookies();
  const token = cookieStore.get(getAuthCookieName())?.value;
  if (token && !incomingHeaders.has("Authorization")) {
    incomingHeaders.set("Authorization", `Bearer ${token}`);
  }

  if (!incomingHeaders.has("Accept")) {
    incomingHeaders.set("Accept", "application/json");
  }

  const init: RequestInit = {
    method: request.method,
    headers: incomingHeaders,
    cache: "no-store",
  };

  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = await request.arrayBuffer();
  }

  const response = await fetch(url, init);
  const body = await response.arrayBuffer();

  return new NextResponse(body, {
    status: response.status,
    headers: response.headers,
  });
}

export async function GET(
  request: Request,
  context: { params: Promise<{ path?: string[] }> }
) {
  return forward(request, context.params);
}

export async function POST(
  request: Request,
  context: { params: Promise<{ path?: string[] }> }
) {
  return forward(request, context.params);
}

export async function PUT(
  request: Request,
  context: { params: Promise<{ path?: string[] }> }
) {
  return forward(request, context.params);
}

export async function PATCH(
  request: Request,
  context: { params: Promise<{ path?: string[] }> }
) {
  return forward(request, context.params);
}

export async function DELETE(
  request: Request,
  context: { params: Promise<{ path?: string[] }> }
) {
  return forward(request, context.params);
}
