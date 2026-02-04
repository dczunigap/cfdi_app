import { apiFetch } from "@/lib/api";
import type { PlatformRfc } from "./types";

export async function listPlatformRfcs(): Promise<PlatformRfc[]> {
  return apiFetch<PlatformRfc[]>("/platform-rfcs");
}

export async function addPlatformRfc(payload: {
  rfc: string;
  nombre?: string | null;
}): Promise<PlatformRfc> {
  return apiFetch<PlatformRfc>("/platform-rfcs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deletePlatformRfc(id: number): Promise<void> {
  await apiFetch<void>(`/platform-rfcs/${id}`, { method: "DELETE" });
}
