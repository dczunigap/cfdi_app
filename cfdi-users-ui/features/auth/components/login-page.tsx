import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import { getAppTitle, getAuthCookieName, getAuthCookieTtlSeconds } from "@/lib/env";

type LoginPageProps = {
  searchParams?: Promise<{
    error?: string;
  }>;
};

async function loginAction(formData: FormData) {
  "use server";

  const username = String(formData.get("username") ?? "");
  const password = String(formData.get("password") ?? "");

  const expectedUser = process.env.ADMIN_USER ?? "";
  const expectedPass = process.env.ADMIN_PASS ?? "";

  if (!expectedUser || !expectedPass) {
    redirect("/login?error=missing-config");
  }

  if (username === expectedUser && password === expectedPass) {
    const cookieStore = await cookies();
    cookieStore.set(getAuthCookieName(), "1", {
      httpOnly: true,
      sameSite: "lax",
      path: "/",
      maxAge: getAuthCookieTtlSeconds(),
      secure: process.env.NODE_ENV === "production",
    });
    redirect("/users");
  }

  redirect("/login?error=invalid");
}

export default async function LoginPage({ searchParams }: LoginPageProps) {
  const resolvedParams = (await searchParams) ?? {};
  const error = resolvedParams.error;
  const message =
    error === "missing-config"
      ? "Falta configurar ADMIN_USER y ADMIN_PASS en .env.local."
      : error === "invalid"
        ? "Usuario o password incorrectos."
        : null;

  const appTitle = getAppTitle();

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
              Ingresa con el superusuario para administrar altas, ediciones y bajas de
              usuarios.
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
                Usa las credenciales definidas en el archivo .env.local.
              </p>
            </div>

            {message ? (
              <div className="mb-4 rounded-xl border border-rose-200 bg-rose-50 px-4 py-3 text-sm text-rose-700">
                {message}
              </div>
            ) : null}

            <form action={loginAction} className="space-y-5">
              <label className="block text-sm font-medium text-slate-200">
                Usuario
                <input
                  name="username"
                  type="text"
                  autoComplete="username"
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
                className="w-full rounded-xl bg-white px-4 py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100"
              >
                Entrar
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
