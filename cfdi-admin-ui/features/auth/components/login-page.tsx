"use client";

import { Suspense, useState } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { getPublicAppTitle } from "@/lib/env";

function LoginPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const error = searchParams.get("error");
  const message =
    error === "invalid"
      ? "Usuario o password incorrectos."
      : error === "missing-config"
        ? "Falta configurar API_BASE_URL en el servidor."
        : null;

  const [loading, setLoading] = useState(false);
  const [localError, setLocalError] = useState<string | null>(null);

  const appTitle = getPublicAppTitle();

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setLocalError(null);
    setLoading(true);
    const formData = new FormData(event.currentTarget);
    const payload = {
      email: String(formData.get("username") ?? ""),
      password: String(formData.get("password") ?? ""),
    };

    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    setLoading(false);
    if (!response.ok) {
      setLocalError("Credenciales invalidas.");
      return;
    }
    router.push("/users");
  };

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <div className="mx-auto flex min-h-screen max-w-5xl items-center px-6 py-12">
        <div className="grid w-full gap-10 lg:grid-cols-[1.1fr_0.9fr]">
          <div className="space-y-6">
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
              {appTitle}
            </p>
            <h1 className="text-4xl font-semibold leading-tight md:text-5xl">
              Acceso administrativo
            </h1>
            <p className="max-w-xl text-base text-slate-300 md:text-lg">
              Inicia sesión con un usuario valido del CFDI API.
            </p>
            <div className="grid max-w-md gap-3 rounded-2xl border border-white/10 bg-white/5 p-6 text-sm text-slate-200">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Entorno</span>
                <span className="font-medium">Next.js + Tailwind</span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">Modo</span>
                <span className="font-medium">Admin only</span>
              </div>
            </div>
          </div>

          <div className="rounded-3xl border border-white/10 bg-white/5 p-8 text-slate-100 shadow-2xl shadow-black/30">
            <div className="mb-6 space-y-2">
              <h2 className="text-2xl font-semibold">Iniciar sesión</h2>
              <p className="text-sm text-slate-400">
                Usa el correo y password registrados en el CFDI API.
              </p>
            </div>

            {message ? (
              <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {message}
              </div>
            ) : null}
            {localError ? (
              <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {localError}
              </div>
            ) : null}

            <form onSubmit={handleSubmit} className="space-y-5">
              <label className="block text-sm font-medium text-slate-200">
                Correo
                <input
                  name="username"
                  type="text"
                  autoComplete="email"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-white/30"
                  required
                />
              </label>

              <label className="block text-sm font-medium text-slate-200">
                Password
                <input
                  name="password"
                  type="password"
                  autoComplete="current-password"
                  className="mt-2 w-full rounded-xl border border-white/10 bg-slate-950 px-4 py-3 text-slate-100 outline-none transition focus:border-white/30"
                  required
                />
              </label>

              <button
                type="submit"
                disabled={loading}
                className="w-full rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-70"
              >
                {loading ? "Validando..." : "Entrar"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}

export default function LoginPage() {
  return (
    <Suspense fallback={null}>
      <LoginPageContent />
    </Suspense>
  );
}
