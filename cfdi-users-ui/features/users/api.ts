import { apiFetch } from "@/lib/api";
import { type User, type UserFormValues } from "./types";

export async function listUsers(): Promise<User[]> {
  return apiFetch<User[]>("/users");
}

export async function createUser(payload: UserFormValues): Promise<User> {
  return apiFetch<User>("/users", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export async function updateUser(
  id: number,
  payload: UserFormValues
): Promise<User> {
  return apiFetch<User>(`/users/${id}`, {
    method: "PUT",
    body: JSON.stringify(payload),
  });
}

export async function deleteUser(id: number): Promise<void> {
  await apiFetch<void>(`/users/${id}`, { method: "DELETE" });
}
