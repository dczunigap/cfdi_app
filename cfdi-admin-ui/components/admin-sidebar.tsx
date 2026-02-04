"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { KeyRound, Users, Phone, ShieldCheck, Building2 } from "lucide-react";

const navItems = [
  { href: "/users", label: "Users", icon: Users },
  { href: "/platform-rfcs", label: "Platform RFCs", icon: Building2 },
  { href: "/admin-sat", label: "Admin SAT", icon: KeyRound }
  // { href: "/admin-sat#rfc-users", label: "RFC por usuario", icon: Users },
  // { href: "/admin-sat#rfc-phones", label: "Telefonos RFC", icon: Phone },
  // { href: "/admin-sat#credentials", label: "Credenciales SAT", icon: KeyRound },
];

export default function AdminSidebar() {
  const pathname = usePathname();

  return (
    <aside className="rounded-2xl border border-white/10 bg-white/5 p-4 text-sm">
      <p className="px-2 text-xs uppercase tracking-[0.24em] text-slate-400">
        Modulos
      </p>
      <nav className="mt-4 grid gap-1">
        {navItems.map((item) => {
          const baseHref = item.href.split("#")[0];
          const isActive =
            pathname === baseHref || pathname.startsWith(`${baseHref}/`);
          const Icon = item.icon;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={`flex items-center gap-3 rounded-xl px-3 py-2 transition ${
                isActive
                  ? "bg-white/10 text-white"
                  : "text-slate-300 hover:bg-white/5 hover:text-white"
              }`}
            >
              <Icon className="h-4 w-4" aria-hidden="true" />
              <span>{item.label}</span>
            </Link>
          );
        })}
      </nav>
    </aside>
  );
}
