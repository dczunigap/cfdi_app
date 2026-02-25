import { apiFetch, apiFetchForm } from "@/lib/api";
import type {
  AdminUser,
  RfcPhone,
  SatCredential,
  UserRfc,
  UserRfcCatalogs,
} from "./types";

export async function listSatCredentials(): Promise<SatCredential[]> {
  return apiFetch<SatCredential[]>("/sat/credentials");
}

export async function upsertSatCredentials(form: FormData): Promise<void> {
  await apiFetchForm<void>("/sat/credentials", {
    method: "POST",
    body: form,
  });
}

export async function deleteSatCredentials(rfc: string): Promise<void> {
  await apiFetch<void>(`/sat/credentials/${encodeURIComponent(rfc)}`, {
    method: "DELETE",
  });
}

export async function listRfcPhones(): Promise<RfcPhone[]> {
  return apiFetch<RfcPhone[]>("/rfc-phones");
}

export async function upsertRfcPhone(payload: {
  phone: string;
  rfc: string;
}): Promise<RfcPhone> {
  return apiFetch<RfcPhone>("/rfc-phones", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function deleteRfcPhone(id: number): Promise<void> {
  await apiFetch<void>(`/rfc-phones/${id}`, { method: "DELETE" });
}

export async function listUserRfcs(userId: number): Promise<UserRfc[]> {
  return apiFetch<UserRfc[]>(`/user-rfcs?user_id=${userId}`);
}

export async function addUserRfc(payload: {
  user_id: number;
  rfc: string;
  regimen_fiscal_clave: string;
}): Promise<UserRfc> {
  return apiFetch<UserRfc>("/user-rfcs", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function listUserRfcCatalogs(): Promise<UserRfcCatalogs> {
  return apiFetch<UserRfcCatalogs>("/user-rfcs/catalogos");
}

export async function deleteUserRfc(userId: number, rfc: string): Promise<void> {
  await apiFetch<void>(`/user-rfcs/${userId}/${encodeURIComponent(rfc)}`, {
    method: "DELETE",
  });
}

export async function listAdminUsers(): Promise<AdminUser[]> {
  return apiFetch<AdminUser[]>("/users");
}
