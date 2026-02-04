"use client";

import { useMemo, useState } from "react";
import { CheckCircle2, Pencil, Trash2, XCircle } from "lucide-react";

import { useUsers } from "../hooks/use-users";
import { type User, type UserFormValues } from "../types";
import UserForm from "./user-form";
import EmptyState from "@/components/empty-state";
import ErrorState from "@/components/error-state";
import { getErrorMessage } from "@/lib/errors";

type FormMode = "create" | "edit";

export default function UsersClient() {
  const [mode, setMode] = useState<FormMode>("create");
  const [editingId, setEditingId] = useState<number | null>(null);
  const [editingUser, setEditingUser] = useState<User | null>(null);

  const { usersQuery, createMutation, updateMutation, deleteMutation } =
    useUsers();

  const users = useMemo(() => usersQuery.data ?? [], [usersQuery.data]);

  const onSubmit = (values: UserFormValues) => {
    if (mode === "edit" && editingId) {
      const payload: UserFormValues = {
        ...values,
        password: values.password?.trim() || undefined,
      };
      updateMutation.mutate(
        { id: editingId, payload },
        {
          onSuccess: () => {
            setMode("create");
            setEditingId(null);
            setEditingUser(null);
          },
        }
      );
      return;
    }

    createMutation.mutate(
      {
        ...values,
        password: values.password?.trim() ?? "",
      },
      {
        onSuccess: () => {
          setMode("create");
          setEditingUser(null);
        },
      }
    );
  };

  const startEdit = (user: User) => {
    setMode("edit");
    setEditingId(user.id);
    setEditingUser(user);
  };

  const cancelEdit = () => {
    setMode("create");
    setEditingId(null);
    setEditingUser(null);
  };

  const handleDelete = (user: User) => {
    if (!confirm(`Eliminar usuario ${user.username ?? user.email}?`)) return;
    deleteMutation.mutate(user.id);
  };

  return (
    <div className="grid gap-8 lg:grid-cols-[360px_1fr]">
      <UserForm
        mode={mode}
        initialUser={editingUser}
        onSubmit={onSubmit}
        onCancelEdit={cancelEdit}
        isSubmitting={createMutation.isPending || updateMutation.isPending}
        errorMessage={
          createMutation.isError || updateMutation.isError
            ? getErrorMessage(
                createMutation.error ?? updateMutation.error,
                "No se pudo guardar el usuario."
              )
            : null
        }
      />

      <section className="rounded-2xl border border-white/10 bg-white/5 p-6 text-slate-100 shadow-sm">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold">Listado de usuarios</h2>
            <p className="text-sm text-slate-400">
              {users.length} usuarios registrados
            </p>
          </div>
          {usersQuery.isFetching ? (
            <span className="text-xs uppercase tracking-wider text-slate-400">
              Actualizando...
            </span>
          ) : null}
        </div>

        {usersQuery.isLoading ? (
          <p className="text-sm text-slate-400">Cargando usuarios...</p>
        ) : usersQuery.isError ? (
          <ErrorState
            message={getErrorMessage(
              usersQuery.error,
              "No se pudo cargar el listado."
            )}
          />
        ) : users.length === 0 ? (
          <EmptyState
            title="Sin usuarios para mostrar"
            description="Crea el primer usuario para comenzar."
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wider text-slate-400">
                <tr>
                  <th className="py-3">Username</th>
                  <th className="py-3">Correo</th>
                  <th className="py-3 text-center">Activo</th>
                  <th className="py-3 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/10">
                {users.map((user) => (
                  <tr key={user.id}>
                    <td className="py-3 font-medium text-slate-100">
                      {user.username ?? "-"}
                    </td>
                    <td className="py-3 text-slate-300">{user.email ?? "-"}</td>
                    <td className="py-3 text-center">
                      {user.is_active ? (
                        <span className="inline-flex items-center justify-center rounded-full bg-emerald-500/10 p-1 text-emerald-400">
                          <CheckCircle2 className="h-5 w-5" aria-hidden="true" />
                          <span className="sr-only">Activo</span>
                        </span>
                      ) : (
                        <span className="inline-flex items-center justify-center rounded-full bg-rose-500/10 p-1 text-rose-400">
                          <XCircle className="h-5 w-5" aria-hidden="true" />
                          <span className="sr-only">Inactivo</span>
                        </span>
                      )}
                    </td>
                    <td className="py-3 text-right">
                      <div className="flex items-center justify-end gap-2">
                        <button
                          type="button"
                          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-white/10 text-slate-300 transition hover:border-white/30 hover:text-white"
                          onClick={() => startEdit(user)}
                          aria-label="Editar usuario"
                          title="Editar"
                        >
                          <Pencil className="h-4 w-4" aria-hidden="true" />
                        </button>
                        <button
                          type="button"
                          className="inline-flex h-9 w-9 items-center justify-center rounded-lg border border-rose-500/30 text-rose-300 transition hover:border-rose-500/60 hover:text-rose-200"
                          onClick={() => handleDelete(user)}
                          disabled={deleteMutation.isPending}
                          aria-label="Eliminar usuario"
                          title="Eliminar"
                        >
                          <Trash2 className="h-4 w-4" aria-hidden="true" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
