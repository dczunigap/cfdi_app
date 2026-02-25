"use client";

import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";

import { userSchema, type User, type UserFormValues } from "../types";

type UserFormProps = {
  mode: "create" | "edit";
  initialUser?: User | null;
  onSubmit: (values: UserFormValues) => void;
  onCancelEdit: () => void;
  isSubmitting: boolean;
  errorMessage?: string | null;
};

const emptyValues: UserFormValues = {
  username: "",
  email: "",
  password: "",
  is_active: true,
};

export default function UserForm({
  mode,
  initialUser,
  onSubmit,
  onCancelEdit,
  isSubmitting,
  errorMessage,
}: UserFormProps) {
  const form = useForm<UserFormValues>({
    resolver: zodResolver(userSchema),
    defaultValues: emptyValues,
  });

  useEffect(() => {
    if (mode === "edit" && initialUser) {
      form.reset({
        username: initialUser.username ?? "",
        email: initialUser.email ?? "",
        password: "",
        is_active: initialUser.is_active ?? true,
      });
      return;
    }
    form.reset(emptyValues);
  }, [form, mode, initialUser]);

  return (
    <section className="rounded-2xl border border-white/10 bg-white/5 p-6 text-slate-100 shadow-sm">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">
          {mode === "create" ? "Nuevo usuario" : "Editar usuario"}
        </h2>
        {mode === "edit" ? (
          <button
            type="button"
            className="text-xs font-semibold uppercase tracking-wider text-slate-400"
            onClick={onCancelEdit}
          >
            Cancelar
          </button>
        ) : null}
      </div>

      <form
        className="mt-6 space-y-4"
        autoComplete="off"
        onSubmit={form.handleSubmit((values) => {
          if (mode === "create" && !values.password?.trim()) {
            form.setError("password", { message: "Password requerido" });
            return;
          }
          onSubmit(values);
        })}
      >
        <label className="block text-sm font-medium text-slate-200">
          Username
          <input
            type="text"
            className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-white/30"
            autoComplete="off"
            {...form.register("username")}
          />
          {form.formState.errors.username ? (
            <p className="mt-1 text-xs text-rose-400">
              {form.formState.errors.username.message}
            </p>
          ) : null}
        </label>

        <label className="block text-sm font-medium text-slate-200">
          Correo
          <input
            type="email"
            className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-white/30"
            autoComplete="off"
            {...form.register("email")}
          />
          {form.formState.errors.email ? (
            <p className="mt-1 text-xs text-rose-400">
              {form.formState.errors.email.message}
            </p>
          ) : null}
        </label>

        <label className="block text-sm font-medium text-slate-200">
          Password
          <input
            type="password"
            className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-white/30"
            autoComplete="new-password"
            {...form.register("password")}
          />
          {mode === "edit" ? (
            <p className="mt-1 text-xs text-slate-400">
              Dejar en blanco para mantener el password actual.
            </p>
          ) : null}
          {form.formState.errors.password ? (
            <p className="mt-1 text-xs text-rose-400">
              {form.formState.errors.password.message}
            </p>
          ) : null}
        </label>

        <label className="flex items-center gap-2 text-sm text-slate-300">
          <input
            type="checkbox"
            className="h-4 w-4 rounded border-white/20 bg-slate-950 text-emerald-500"
            {...form.register("is_active")}
          />
          Usuario activo
        </label>

        <button
          type="submit"
          className="w-full rounded-xl bg-white px-4 py-2 text-sm font-semibold text-slate-900 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-70"
          disabled={isSubmitting}
        >
          {mode === "create" ? "Crear usuario" : "Guardar cambios"}
        </button>

        {errorMessage ? (
          <p className="text-sm text-rose-400">{errorMessage}</p>
        ) : null}
      </form>
    </section>
  );
}
