import { cookies } from "next/headers";
import { redirect } from "next/navigation";
import AdminSidebar from "@/components/admin-sidebar";
import {
  getAppSubtitle,
  getAppTitle,
  getAuthCookieName,
  getServerApiBaseUrl,
} from "@/lib/env";

type AdminShellProps = {
  children: React.ReactNode;
};

async function logoutAction() {
  "use server";

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

  cookieStore.set(cookieName, "", {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  redirect("/login");
}

export default async function AdminShell({ children }: AdminShellProps) {
  const cookieStore = await cookies();
  const authCookieName = getAuthCookieName();
  const auth = cookieStore.get(authCookieName)?.value;
  if (!auth) {
    redirect("/login");
  }

  const appTitle = getAppTitle();
  const appSubtitle = getAppSubtitle();

  return (
    <div className="min-h-screen bg-slate-950 text-white">
      <header className="border-b border-white/10 bg-slate-950">
        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">
          <div>
            <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
              {appTitle}
            </p>
            <h1 className="text-lg font-semibold text-white">{appSubtitle}</h1>
          </div>
          <form action={logoutAction}>
            <button
              type="submit"
              className="rounded-lg border border-white/10 px-4 py-2 text-sm font-medium text-slate-200 transition hover:border-white/20 hover:bg-white/5"
            >
              Cerrar sesión
            </button>
          </form>
        </div>
      </header>
      <main className="mx-auto grid max-w-7xl gap-8 px-6 py-10 lg:grid-cols-[240px_1fr]">
        <AdminSidebar />
        <section className="min-w-0">{children}</section>
      </main>
    </div>
  );
}
